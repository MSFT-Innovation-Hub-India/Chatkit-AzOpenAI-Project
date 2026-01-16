"""
ChatKit Server Implementation with Azure OpenAI.
Implements a self-hosted ChatKit server with todo list functionality.
Features rich interactive widgets for todo management.
"""

import logging
from typing import Any, AsyncIterator
import uuid

from chatkit.server import ChatKitServer, ThreadStreamEvent
from chatkit.store import Store, ThreadMetadata
from chatkit.types import UserMessageItem, ClientToolCallItem
from chatkit.agents import stream_agent_response, stream_widget, AgentContext, ThreadItemConverter
from chatkit.widgets import (
    Card, Text, Box, Button, Row, Checkbox, Form, Input, 
    Badge, Icon, Divider, Title, Spacer, Col
)
from chatkit.actions import ActionConfig

from agents import Agent, function_tool, Runner, OpenAIChatCompletionsModel, RunConfig
from agents.run_context import RunContextWrapper

from store import SQLiteStore
from azure_client import client_manager
from config import settings

logger = logging.getLogger(__name__)


# Type alias for the context used by agent tools
TodoContext = AgentContext[Any]


class TodoChatKitServer(ChatKitServer):
    """
    Self-hosted ChatKit server with Azure OpenAI and todo list functionality.
    
    Features:
    - Uses Azure OpenAI for chat responses
    - Supports adding, completing, and listing todos
    - Streams widget updates for todo list visualization
    """
    
    def __init__(self, data_store: SQLiteStore):
        super().__init__(data_store)
        self.data_store = data_store
    
    # Define todo list tools
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
    
    # Create the assistant agent (model will be set at runtime with Azure OpenAI)
    assistant_agent = Agent["TodoContext"](
        name="Todo Assistant",
        instructions="""You are a helpful todo list assistant. You help users manage their tasks and stay organized.

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

Keep text responses very brief since the widget shows all the details. Use emojis occasionally.""",
        tools=[add_todo, complete_todo, delete_todo, list_todos],
    )
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input: UserMessageItem | ClientToolCallItem,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle user messages and generate responses using Azure OpenAI.
        Streams events back to the ChatKit client.
        """
        # Get Azure OpenAI client
        client = await client_manager.get_client()
        
        # Create the Azure OpenAI model wrapper for the agents SDK
        azure_model = OpenAIChatCompletionsModel(
            model=settings.azure_openai_deployment,
            openai_client=client,
        )
        
        # Create agent context with thread and store (using ChatKit's AgentContext)
        agent_context = AgentContext(
            thread=thread,
            store=self.data_store,
            request_context=context,
        )
        
        # Convert input to agent-compatible format
        converter = ThreadItemConverter()
        agent_input = await converter.to_agent_input(input)
        
        # Create a runner with the Azure OpenAI model
        result = Runner.run_streamed(
            self.assistant_agent,
            agent_input,
            context=agent_context,
            run_config=RunConfig(model=azure_model),
        )
        
        # Stream the agent response back to the client
        async for event in stream_agent_response(agent_context, result):
            if hasattr(event, 'update'):
                logger.info(f"Streaming event: {event.type} - update type: {event.update.type if hasattr(event.update, 'type') else 'N/A'}")
            else:
                logger.info(f"Streaming event: {event.type}")
            yield event
        
        # After agent response, check if we should show a todo widget
        if getattr(agent_context, '_show_todo_widget', False):
            todos = getattr(agent_context, '_todos', [])
            widget = self._build_todo_widget(todos, thread.id)
            logger.info(f"Built widget: {widget}")
            async for widget_event in stream_widget(
                thread,
                widget,
            ):
                # Log detailed widget event info - dump full event for debugging
                import json
                try:
                    event_dict = widget_event.model_dump() if hasattr(widget_event, 'model_dump') else str(widget_event)
                    logger.info(f"Widget event FULL: {json.dumps(event_dict, default=str)[:2000]}")
                except Exception as e:
                    logger.info(f"Widget event (error serializing): {widget_event} - {e}")
                yield widget_event
    
    async def action(
        self,
        thread: ThreadMetadata,
        action: "Action",
        sender: Any,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle widget actions (button clicks, form submissions, checkbox toggles, etc.)
        """
        from chatkit.actions import Action
        
        action_type = action.type
        payload = action.payload or {}
        logger.info(f"Action received: {action_type} with payload: {payload}")
        
        if action_type == "add_todo_form":
            # Handle form submission to add a new todo
            todo_text = payload.get("todo_text", "").strip() if isinstance(payload, dict) else ""
            logger.info(f"Adding todo: '{todo_text}' to thread {thread.id}")
            if todo_text:
                await self.data_store.add_todo(thread.id, todo_text)
            # Stream updated todo list widget
            todos = await self.data_store.list_todos(thread.id)
            logger.info(f"Todos after add: {len(todos)} items")
            widget = self._build_todo_widget(todos, thread.id)
            async for event in stream_widget(thread, widget):
                logger.info(f"Streaming action widget event: {event.type}")
                yield event
        
        elif action_type == "complete_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                await self.data_store.complete_todo(thread.id, todo_id)
            # Stream updated todo list widget
            todos = await self.data_store.list_todos(thread.id)
            widget = self._build_todo_widget(todos, thread.id)
            async for event in stream_widget(thread, widget):
                yield event
        
        elif action_type == "delete_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                await self.data_store.delete_todo(thread.id, todo_id)
            # Stream updated todo list widget
            todos = await self.data_store.list_todos(thread.id)
            widget = self._build_todo_widget(todos, thread.id)
            async for event in stream_widget(thread, widget):
                yield event
        
        elif action_type == "toggle_todo":
            todo_id = payload.get("todo_id") if isinstance(payload, dict) else None
            if todo_id:
                # Toggle the todo status
                todos = await self.data_store.list_todos(thread.id)
                todo = next((t for t in todos if t["id"] == todo_id), None)
                if todo and not todo["completed"]:
                    await self.data_store.complete_todo(thread.id, todo_id)
            
            # Stream updated widget
            todos = await self.data_store.list_todos(thread.id)
            widget = self._build_todo_widget(todos, thread.id)
            async for event in stream_widget(thread, widget):
                yield event
    
    def _build_todo_widget(self, todos: list, thread_id: str) -> Card:
        """Build an interactive todo list widget card with form input and action buttons."""
        children = []
        
        # Header with title and stats
        pending_count = sum(1 for t in todos if not t["completed"])
        completed_count = sum(1 for t in todos if t["completed"])
        
        children.append(
            Row(
                id="header_row",
                children=[
                    Title(id="title", value="📋 My Todo List", size="lg"),
                    Spacer(id="spacer1"),
                    Badge(
                        id="pending_badge",
                        label=f"{pending_count} pending",
                        color="warning" if pending_count > 0 else "success",
                    ),
                    Badge(
                        id="completed_badge", 
                        label=f"{completed_count} done",
                        color="success",
                    ),
                ]
            )
        )
        
        children.append(Divider(id="divider1"))
        
        # Add todo form
        children.append(
            Form(
                id="add_todo_form",
                children=[
                    Row(
                        id="form_row",
                        children=[
                            Input(
                                id="todo_text",
                                placeholder="What needs to be done?",
                                name="todo_text",
                            ),
                            Button(
                                id="add_button",
                                label="➕ Add",
                                color="primary",
                                onClickAction=ActionConfig(
                                    type="add_todo_form",
                                    handler="server",
                                ),
                            ),
                        ]
                    )
                ]
            )
        )
        
        children.append(Spacer(id="spacer2"))
        
        # Todo list items
        if not todos:
            children.append(
                Box(
                    id="empty_state",
                    children=[
                        Text(id="empty_icon", value="🎉", textAlign="center"),
                        Text(id="empty_text", value="No todos yet! Add one above or ask me to add tasks.", textAlign="center"),
                    ]
                )
            )
        else:
            for todo in todos:
                is_completed = todo["completed"]
                children.append(
                    Row(
                        id=f"todo_{todo['id']}",
                        children=[
                            Checkbox(
                                id=f"check_{todo['id']}",
                                name=f"check_{todo['id']}",
                                defaultChecked=is_completed,
                                onChangeAction=ActionConfig(
                                    type="toggle_todo",
                                    handler="server",
                                    payload={"todo_id": todo["id"]}
                                ),
                            ),
                            Text(
                                id=f"text_{todo['id']}", 
                                value=todo["title"],
                                lineThrough=is_completed,
                                color="secondary" if is_completed else None,
                            ),
                            Spacer(id=f"spacer_{todo['id']}"),
                            Button(
                                id=f"complete_{todo['id']}",
                                label="✓" if not is_completed else "↩",
                                size="sm",
                                color="success" if not is_completed else "secondary",
                                onClickAction=ActionConfig(
                                    type="complete_todo",
                                    handler="server",
                                    payload={"todo_id": todo["id"]}
                                ),
                            ),
                            Button(
                                id=f"delete_{todo['id']}",
                                label="🗑",
                                size="sm",
                                color="danger",
                                onClickAction=ActionConfig(
                                    type="delete_todo",
                                    handler="server",
                                    payload={"todo_id": todo["id"]}
                                ),
                            ),
                        ]
                    )
                )
        
        return Card(id=f"todo_widget_{thread_id}", children=children)
