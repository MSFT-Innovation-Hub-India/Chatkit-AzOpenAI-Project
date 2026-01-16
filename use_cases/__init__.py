"""
Use Cases Package.

This package contains modular use case implementations for the ChatKit server.
Each use case is a self-contained module with its own:
- Agent and tools
- Widget builders
- Action handlers
- Store extensions (if needed)

Available use cases:
- todo: Interactive todo list management with widgets
"""

# Re-export commonly used items from the todo use case
from use_cases.todo import (
    create_todo_agent,
    build_todo_widget,
    handle_todo_action,
)

__all__ = [
    "create_todo_agent",
    "build_todo_widget",
    "handle_todo_action",
]
