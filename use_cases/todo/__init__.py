"""
Todo Use Case Module.

This module provides a complete todo list management use case for ChatKit.
It includes:
- Agent with todo management tools
- Interactive widget builder  
- Action handlers for widget interactions
- SQLite database for persistence

Usage:
    from use_cases.todo import create_todo_agent, build_todo_widget, handle_todo_action
    
    # Create the agent
    agent = create_todo_agent()
    
    # Build a widget for the current todos
    from use_cases.todo.database import get_all_todos
    todos = get_all_todos()
    widget = build_todo_widget(todos, thread_id)
    
    # Handle widget actions
    result = handle_todo_action(action)
"""

from use_cases.todo.agent import create_todo_agent, TodoContext
from use_cases.todo.widgets import build_todo_widget
from use_cases.todo.actions import handle_todo_action
from use_cases.todo.database import get_all_todos, add_todo, complete_todo, delete_todo

__all__ = [
    "create_todo_agent",
    "build_todo_widget", 
    "handle_todo_action",
    "TodoContext",
    "get_all_todos",
    "add_todo",
    "complete_todo",
    "delete_todo",
]
