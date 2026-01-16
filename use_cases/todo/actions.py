"""
Todo Action Handler.

This module handles all interactive actions from the todo widget.
"""

from typing import Any
from .database import add_todo, complete_todo, delete_todo


def handle_todo_action(action: Any) -> dict:
    """
    Handle an action from the todo widget.
    
    Args:
        action: The action object with type and payload attributes
        
    Returns:
        A response dict with success status and optional message
    """
    action_type = action.type
    payload = action.payload or {}
    
    if action_type == "add_todo_form":
        return _handle_add(payload)
    elif action_type == "complete_todo":
        return _handle_complete(payload)
    elif action_type == "toggle_todo":
        return _handle_toggle(payload)
    elif action_type == "delete_todo":
        return _handle_delete(payload)
    else:
        return {"success": False, "message": f"Unknown action: {action_type}"}


def _handle_add(payload: dict) -> dict:
    """Handle add todo form submission."""
    todo_text = payload.get("todo_text", "").strip()
    
    if not todo_text:
        return {"success": False, "message": "Todo text is required"}
    
    todo = add_todo(todo_text)
    return {"success": True, "todo": todo}


def _handle_complete(payload: dict) -> dict:
    """Handle complete todo button click."""
    todo_id = payload.get("todo_id")
    
    if not todo_id:
        return {"success": False, "message": "Todo ID is required"}
    
    todo = complete_todo(todo_id)
    if todo:
        return {"success": True, "todo": todo}
    return {"success": False, "message": "Todo not found"}


def _handle_toggle(payload: dict) -> dict:
    """Handle checkbox toggle."""
    todo_id = payload.get("todo_id")
    
    if not todo_id:
        return {"success": False, "message": "Todo ID is required"}
    
    # Toggle is essentially the same as complete (toggles state)
    todo = complete_todo(todo_id)
    if todo:
        return {"success": True, "todo": todo}
    return {"success": False, "message": "Todo not found"}


def _handle_delete(payload: dict) -> dict:
    """Handle delete todo button click."""
    todo_id = payload.get("todo_id")
    
    if not todo_id:
        return {"success": False, "message": "Todo ID is required"}
    
    success = delete_todo(todo_id)
    if success:
        return {"success": True, "deleted_id": todo_id}
    return {"success": False, "message": "Todo not found"}
