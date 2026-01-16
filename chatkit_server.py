"""
Todo ChatKit Server Implementation.

This is a specialized ChatKit server for the todo list use case.
It extends BaseChatKitServer and delegates to the modular todo use case components.
"""

import logging
from typing import Any, AsyncIterator

from chatkit.server import ThreadStreamEvent
from chatkit.store import ThreadMetadata
from chatkit.agents import stream_widget

from agents import Agent

from base_server import BaseChatKitServer
from store import SQLiteStore
from use_cases.todo import create_todo_agent, build_todo_widget

logger = logging.getLogger(__name__)


class TodoChatKitServer(BaseChatKitServer):
    """
    ChatKit server for todo list management.
    
    This server:
    - Uses the todo agent with add/complete/delete/list tools
    - Renders interactive todo widgets
    - Handles widget actions (form submissions, button clicks, checkboxes)
    
    To create a similar server for a different use case:
    1. Create your use case module under use_cases/
    2. Define your agent, widgets, and action handlers
    3. Extend BaseChatKitServer and implement get_agent(), action(), post_respond_hook()
    """
    
    def __init__(self, data_store: SQLiteStore):
        """
        Initialize the todo server.
        
        Args:
            data_store: SQLite store for thread and todo persistence
        """
        super().__init__(data_store)
        self._agent = None
    
    def get_agent(self) -> Agent:
        """Return the todo assistant agent."""
        if self._agent is None:
            self._agent = create_todo_agent()
        return self._agent
    
    async def post_respond_hook(
        self,
        thread: ThreadMetadata,
        agent_context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Stream todo widget if agent tools triggered a display.
        
        The todo agent tools set _show_todo_widget=True on the context
        when they want to display the updated todo list.
        """
        if getattr(agent_context, '_show_todo_widget', False):
            todos = getattr(agent_context, '_todos', [])
            widget = build_todo_widget(todos, thread.id)
            logger.info(f"Streaming todo widget with {len(todos)} items")
            async for event in stream_widget(thread, widget):
                yield event
    
    async def action(
        self,
        thread: ThreadMetadata,
        action: Any,
        sender: Any,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle todo widget actions.
        
        Supported actions:
        - add_todo_form: Add a new todo from form submission
        - complete_todo: Toggle todo completion status
        - delete_todo: Remove a todo item
        - toggle_todo: Toggle checkbox state
        """
        action_type = action.type
        payload = action.payload or {}
        logger.info(f"Action received: {action_type} with payload: {payload}")
        
        if action_type == "add_todo_form":
            todo_text = payload.get("todo_text", "").strip() if isinstance(payload, dict) else ""
            logger.info(f"Adding todo: '{todo_text}' to thread {thread.id}")
            if todo_text:
                await self.data_store.add_todo(thread.id, todo_text)
            
        elif action_type == "complete_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                await self.data_store.complete_todo(thread.id, todo_id)
        
        elif action_type == "delete_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                await self.data_store.delete_todo(thread.id, todo_id)
        
        elif action_type == "toggle_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                # Toggle = complete if not already completed
                todos = await self.data_store.list_todos(thread.id)
                todo = next((t for t in todos if t["id"] == todo_id), None)
                if todo and not todo["completed"]:
                    await self.data_store.complete_todo(thread.id, todo_id)
        
        # Stream updated widget after any action
        todos = await self.data_store.list_todos(thread.id)
        widget = build_todo_widget(todos, thread.id)
        logger.info(f"Streaming updated widget with {len(todos)} items")
        async for event in stream_widget(thread, widget):
            yield event
