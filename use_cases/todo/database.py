"""
Todo Database Operations.

Simple in-memory database with SQLite persistence for todo items.
"""

import sqlite3
import uuid
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent.parent / "todos.db"


def _get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with the todos table."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_all_todos() -> list:
    """
    Get all todo items.
    
    Returns:
        List of todo dictionaries with id, title, completed fields
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, completed FROM todos ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"id": row["id"], "title": row["title"], "completed": bool(row["completed"])}
        for row in rows
    ]


def add_todo(title: str) -> dict:
    """
    Add a new todo item.
    
    Args:
        title: The todo item title
        
    Returns:
        The created todo dictionary
    """
    todo_id = str(uuid.uuid4())[:8]
    
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (id, title, completed) VALUES (?, ?, ?)",
        (todo_id, title, False)
    )
    conn.commit()
    conn.close()
    
    return {"id": todo_id, "title": title, "completed": False}


def complete_todo(todo_id: str) -> dict | None:
    """
    Toggle the completed status of a todo item.
    
    Args:
        todo_id: The ID of the todo to toggle
        
    Returns:
        The updated todo dictionary, or None if not found
    """
    conn = _get_connection()
    cursor = conn.cursor()
    
    # First get current state
    cursor.execute("SELECT id, title, completed FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    new_completed = not bool(row["completed"])
    cursor.execute(
        "UPDATE todos SET completed = ? WHERE id = ?",
        (new_completed, todo_id)
    )
    conn.commit()
    conn.close()
    
    return {"id": todo_id, "title": row["title"], "completed": new_completed}


def delete_todo(todo_id: str) -> bool:
    """
    Delete a todo item.
    
    Args:
        todo_id: The ID of the todo to delete
        
    Returns:
        True if deleted, False if not found
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted


# Initialize database on module load
init_database()
