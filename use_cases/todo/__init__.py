"""
Todo Use Case Module.

This module provides a complete todo list management use case for ChatKit.
It includes:
- ChatKit server implementation (server.py)
- Agent with todo management tools (agent.py)
- Interactive widget builder (widgets.py)
- Action handlers for widget interactions (actions.py)
- SQLite database for persistence (database.py - legacy)

Usage:
    from use_cases.todo import TodoChatKitServer
    from store import SQLiteStore
    
    # Create the server
    data_store = SQLiteStore("./data/chatkit.db")
    chatkit_server = TodoChatKitServer(data_store)
    
    # Or use individual components:
    from use_cases.todo import create_todo_agent, build_todo_widget
"""

from use_cases.todo.server import TodoChatKitServer
from use_cases.todo.agent import create_todo_agent, TodoContext
from use_cases.todo.widgets import build_todo_widget
from use_cases.todo.actions import handle_todo_action
from use_cases.todo.database import get_all_todos, add_todo, complete_todo, delete_todo

__all__ = [
    # Primary export - the complete ChatKit server
    "TodoChatKitServer",
    
    # Individual components for customization
    "create_todo_agent",
    "build_todo_widget", 
    "handle_todo_action",
    "TodoContext",
    
    # Legacy database functions (use store.py instead)
    "get_all_todos",
    "add_todo",
    "complete_todo",
    "delete_todo",
]
