"""
Todo Agent Definition.

This module defines the AI agent for todo list management.
The agent uses OpenAI Agents SDK with function tools.
"""

import logging
from typing import Any

from agents import Agent, function_tool
from agents.run_context import RunContextWrapper
from chatkit.agents import AgentContext

logger = logging.getLogger(__name__)

# Type alias for the context used by todo tools
TodoContext = AgentContext[Any]


# ----- Tool Definitions -----

@function_tool(description_override="Add a new item to the user's todo list and show the updated widget.")
async def add_todo(ctx: RunContextWrapper["TodoContext"], item: str) -> str:
    """Add a todo item to the list."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    result = await store.add_todo(thread_id, item)
    
    # Trigger widget display after adding
    todos = await store.list_todos(thread_id)
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    
    return f"Added '{item}' to your todo list! Here's your updated list:"


@function_tool(description_override="Mark a todo item as completed using its ID and show the updated widget.")
async def complete_todo(ctx: RunContextWrapper["TodoContext"], todo_id: str) -> str:
    """Mark a todo item as completed."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    result = await store.complete_todo(thread_id, todo_id)
    
    # Trigger widget display after completing
    todos = await store.list_todos(thread_id)
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    
    if result:
        return f"Completed '{result['title']}'! Here's your updated list:"
    return f"Todo with ID '{todo_id}' not found."


@function_tool(description_override="Delete a todo item from the list using its ID and show the updated widget.")
async def delete_todo(ctx: RunContextWrapper["TodoContext"], todo_id: str) -> str:
    """Delete a todo item from the list."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    success = await store.delete_todo(thread_id, todo_id)
    
    # Trigger widget display after deleting
    todos = await store.list_todos(thread_id)
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    
    if success:
        return f"Deleted the todo! Here's your updated list:"
    return f"Todo with ID '{todo_id}' not found."


@function_tool(description_override="List all todo items and show an interactive widget to manage them.")
async def list_todos(ctx: RunContextWrapper["TodoContext"]) -> str:
    """Get all todos for the current thread and trigger widget display."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    todos = await store.list_todos(thread_id)
    
    # Mark that we should show widget after response
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    
    if not todos:
        return "Your todo list is empty. I'll show you a form to add new items!"
    
    pending = sum(1 for t in todos if not t["completed"])
    completed = sum(1 for t in todos if t["completed"])
    return f"You have {len(todos)} todos ({completed} completed, {pending} pending). Here's your interactive todo list!"


# ----- Agent Definition -----

TODO_AGENT_INSTRUCTIONS = """You are a helpful todo list assistant. You help users manage their tasks and stay organized.

Your capabilities:
- Add new todo items when users ask
- Mark todos as completed when users finish tasks  
- Delete todos that are no longer needed
- List all todos to show the current state with an interactive widget

IMPORTANT: When users ask to add todos, ALWAYS use the add_todo tool immediately with the item they specify. Do NOT ask for clarification unless they literally said nothing about what to add.

When users want to complete a todo, use the complete_todo tool with the todo ID.
When users want to delete a todo, use the delete_todo tool with the todo ID.
When users want to see their todos (e.g., "show todos", "list todos", "my tasks"), use the list_todos tool.

After EVERY tool call, an interactive widget will be displayed showing the current todos with buttons and checkboxes.

Keep text responses very brief since the widget shows all the details. Use emojis occasionally."""


def create_todo_agent() -> Agent["TodoContext"]:
    """
    Create and return the todo assistant agent.
    
    Returns:
        An Agent configured for todo list management
    """
    return Agent["TodoContext"](
        name="Todo Assistant",
        instructions=TODO_AGENT_INSTRUCTIONS,
        tools=[add_todo, complete_todo, delete_todo, list_todos],
    )
