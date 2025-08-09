from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# Initialize database (run once at startup)


def init_db():
    with sqlite3.connect("todos.db", check_same_thread=False) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
        """)


def get_db():
    conn = sqlite3.connect("todos.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()  # Close after request


init_db()  # Call on startup

# Mount frontend assets
templates = Jinja2Templates(directory="frontend/templates")


class TodoCreate(BaseModel):
    text: str


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/todos")
async def list_todos(
    request: Request,
    db: sqlite3.Connection = Depends(get_db)  # New connection per request
):
    # Fetch updated list directly
    todos = db.execute("SELECT * FROM todos").fetchall()
    return templates.TemplateResponse("todo/list.html", {
        "request": request,
        "todos": todos
    })


@app.post("/todos")
async def create_todo(
    request: Request,
    db: sqlite3.Connection = Depends(get_db)  # New connection per request
):
    form_data = await request.form()
    db.execute("INSERT INTO todos (text) VALUES (?)", (form_data['text'],))
    db.commit()

    # Fetch updated list directly
    todos = db.execute("SELECT * FROM todos").fetchall()
    return templates.TemplateResponse("todo/list.html", {
        "request": request,
        "todos": todos
    })


@app.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db)  # New connection per request
):
    db.execute("DELETE FROM todos WHERE id=?", (todo_id,))
    db.commit()

    # Fetch updated list directly
    todos = db.execute("SELECT * FROM todos").fetchall()
    return templates.TemplateResponse("todo/list.html", {
        "request": request,
        "todos": todos
    })


@app.put("/todos/{todo_id}/toggle")
async def check_todo(
    todo_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db)  # New connection per request
):
    db.execute(
        "UPDATE todos SET completed = NOT completed WHERE id=?",
        (todo_id,)
    )
    db.commit()

    # Fetch updated list directly
    todos = db.execute("SELECT * FROM todos").fetchall()
    return templates.TemplateResponse("todo/list.html", {
        "request": request,
        "todos": todos
    })
