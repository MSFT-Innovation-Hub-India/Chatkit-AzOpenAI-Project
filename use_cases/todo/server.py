"""
Todo ChatKit Server Implementation.

This is the ChatKit server for the todo list use case.
It extends BaseChatKitServer and integrates all todo-specific components.

Location: use_cases/todo/server.py
- Lives alongside other todo modules (agent.py, widgets.py, actions.py)
- Each use case should have its own server.py
"""

import logging
from typing import Any, AsyncIterator
from datetime import datetime, timezone

from chatkit.server import ThreadStreamEvent
from chatkit.store import ThreadMetadata, Page
from chatkit.agents import stream_widget
from chatkit.types import (
    ThreadItemUpdatedEvent, ThreadItemReplacedEvent, 
    WidgetItem, WidgetRootUpdated,
    AssistantMessageItem, AssistantMessageContent
)

from agents import Agent

from base_server import BaseChatKitServer
from store import SQLiteStore

from .agent import create_todo_agent
from .widgets import build_todo_widget

logger = logging.getLogger(__name__)


class TodoChatKitServer(BaseChatKitServer):
    """
    ChatKit server for todo list management.
    
    This server:
    - Uses the todo agent with add/complete/delete/list tools
    - Renders interactive todo widgets
    - Handles widget actions (form submissions, button clicks, checkboxes)
    
    To create a similar server for a different use case:
    1. Create your use case module under use_cases/your_use_case/
    2. Copy this structure: agent.py, widgets.py, actions.py, server.py
    3. Extend BaseChatKitServer and implement get_agent(), action(), post_respond_hook()
    4. Update main.py to import and use your server
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
    
    async def _collapse_old_widgets(
        self,
        thread: ThreadMetadata,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Find existing todo widgets and replace them with text summaries.
        This keeps the conversation clean with only one live widget.
        """
        try:
            # Load all items in the thread using the correct method signature
            items_page: Page = await self.data_store.load_thread_items(
                thread_id=thread.id,
                after=None,
                limit=100,
                order="asc",
                context=context
            )
            
            for item in items_page.data:
                # Check if it's a widget item (todo widget)
                if isinstance(item, WidgetItem):
                    widget_id = getattr(item.widget, 'id', '') if item.widget else ''
                    if widget_id.startswith('todo_widget_'):
                        # Create a text summary to replace the old widget
                        summary = AssistantMessageItem(
                            id=item.id,
                            thread_id=thread.id,
                            created_at=item.created_at,
                            content=[AssistantMessageContent(
                                text="📋 _Previous todo list snapshot_"
                            )],
                        )
                        logger.info(f"Collapsing old widget {item.id} into summary")
                        yield ThreadItemReplacedEvent(item=summary)
        except Exception as e:
            logger.warning(f"Error collapsing old widgets: {e}")
    
    async def post_respond_hook(
        self,
        thread: ThreadMetadata,
        agent_context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Stream todo widget if agent tools triggered a display.
        
        The todo agent tools set _show_todo_widget=True on the context
        when they want to display the updated todo list.
        
        Before showing a new widget, collapses old widgets into summaries.
        """
        show_widget = getattr(agent_context, '_show_todo_widget', False)
        todos_from_context = getattr(agent_context, '_todos', None)
        
        logger.info(f"post_respond_hook: thread={thread.id}, show_widget={show_widget}")
        
        if show_widget and todos_from_context is not None:
            # Collapse old widgets before showing new one
            async for event in self._collapse_old_widgets(thread, {}):
                yield event
            
            # Use the todos already fetched by the tool
            widget = build_todo_widget(todos_from_context, thread.id)
            logger.info(f"Streaming todo widget with {len(todos_from_context)} items (from tool)")
            async for event in stream_widget(thread, widget):
                yield event
        else:
            # Fallback: Always fetch and show todos after any response
            todos = await self.data_store.list_todos(thread.id)
            logger.info(f"Fallback: Fetching todos directly, found {len(todos)} items")
            if todos or show_widget:
                # Collapse old widgets before showing new one
                async for event in self._collapse_old_widgets(thread, {}):
                    yield event
                
                widget = build_todo_widget(todos, thread.id)
                logger.info(f"Streaming todo widget with {len(todos)} items (fallback)")
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
        - complete_todo: Mark a todo as complete
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
        
        # Update the existing widget in place (instead of adding a new one)
        todos = await self.data_store.list_todos(thread.id)
        widget = build_todo_widget(todos, thread.id)
        logger.info(f"Updating widget with {len(todos)} items")
        
        # Use ThreadItemUpdatedEvent with WidgetRootUpdated to update existing widget
        if sender and hasattr(sender, 'id'):
            yield ThreadItemUpdatedEvent(
                item_id=sender.id,
                update=WidgetRootUpdated(widget=widget),
            )
        else:
            # Fallback: stream a new widget if sender is not available
            logger.warning("No sender widget, streaming new widget instead")
            async for event in stream_widget(thread, widget):
                yield event
