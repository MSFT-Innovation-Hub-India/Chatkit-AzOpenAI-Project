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


@function_tool(description_override="Find and delete a todo item by searching for keywords in its title. Use this when the user wants to delete a todo by describing it rather than by ID.")
async def find_and_delete_todo(ctx: RunContextWrapper["TodoContext"], search_text: str) -> str:
    """Find a todo by title/description and delete it."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    todos = await store.list_todos(thread_id)
    
    # Search for matching todos (case-insensitive)
    search_lower = search_text.lower()
    matches = [t for t in todos if search_lower in t["title"].lower()]
    
    if not matches:
        # Trigger widget display to help user find the right todo
        ctx.context._show_todo_widget = True
        ctx.context._todos = todos
        return f"No todo found matching '{search_text}'. Here's your todo list - you can use the delete button next to any item."
    
    if len(matches) == 1:
        # Exactly one match - delete it
        todo = matches[0]
        await store.delete_todo(thread_id, todo["id"])
        
        # Trigger widget display after deleting
        updated_todos = await store.list_todos(thread_id)
        ctx.context._show_todo_widget = True
        ctx.context._todos = updated_todos
        
        return f"Deleted '{todo['title']}'! Here's your updated list:"
    
    # Multiple matches - show them to user
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    match_titles = ", ".join([f"'{m['title']}'" for m in matches])
    return f"Found multiple todos matching '{search_text}': {match_titles}. Please be more specific or use the delete button in the widget."


@function_tool(description_override="List all todo items and show an interactive widget to manage them.")
async def list_todos(ctx: RunContextWrapper["TodoContext"]) -> str:
    """Get all todos for the current thread and trigger widget display."""
    thread_id = ctx.context.thread.id
    store = ctx.context.store
    todos = await store.list_todos(thread_id)
    
    # Mark that we should show widget after response
    ctx.context._show_todo_widget = True
    ctx.context._todos = todos
    logger.info(f"list_todos: Set _show_todo_widget=True on context (id={id(ctx.context)}), todos={len(todos)}")
    
    if not todos:
        return "Your todo list is empty. I'll show you a form to add new items!"
    
    pending = sum(1 for t in todos if not t["completed"])
    completed = sum(1 for t in todos if t["completed"])
    return f"You have {len(todos)} todos ({completed} completed, {pending} pending). Here's your interactive todo list!"


# ----- Agent Definition -----

TODO_AGENT_INSTRUCTIONS = """You are a helpful todo list assistant. You help users manage their tasks and stay organized.

CRITICAL RULES - YOU MUST FOLLOW THESE:

1. **ALWAYS USE TOOLS** - Never respond to todo-related requests without calling a tool first.

2. **For ANY request to see/show/list/view todos**: ALWAYS call list_todos tool FIRST, even if you think you know what's there. The widget only displays when you call the tool.

3. **For adding todos**: ALWAYS call add_todo immediately. Don't ask for clarification unless the user said nothing about what to add.

4. **For completing todos**: Use complete_todo with the todo ID.

5. **For deleting todos by description**: When the user wants to delete a todo by describing it (e.g., "delete the ice cream todo", "remove the one about groceries"), use find_and_delete_todo with the search text. This will automatically find and delete the matching todo.

6. **For deleting todos by ID**: If you have the exact todo ID, use delete_todo.

TRIGGER WORDS that REQUIRE calling list_todos:
- "show" (show todos, show me, show my list)
- "list" (list todos, list my tasks)  
- "view" (view todos, view my list)
- "see" (let me see, can I see)
- "what" (what's on my list, what todos)
- "display" (display todos)
- "todos" (my todos, the todos)

After you call a tool, an interactive widget will automatically appear. Keep your text response VERY brief (1 line) since the widget shows all details."""


def create_todo_agent() -> Agent["TodoContext"]:
    """
    Create and return the todo assistant agent.
    
    Returns:
        An Agent configured for todo list management
    """
    return Agent["TodoContext"](
        name="Todo Assistant",
        instructions=TODO_AGENT_INSTRUCTIONS,
        tools=[add_todo, complete_todo, delete_todo, find_and_delete_todo, list_todos],
    )
