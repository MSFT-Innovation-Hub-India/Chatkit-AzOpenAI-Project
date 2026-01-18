"""
Todo Widget Builder.

This module builds interactive ChatKit widgets for the todo list UI.
"""

from chatkit.widgets import (
    Card, Text, Box, Button, Row, Checkbox, Form, Input, 
    Badge, Divider, Title, Spacer
)
from chatkit.actions import ActionConfig


def build_todo_widget(todos: list, thread_id: str) -> Card:
    """
    Build an interactive todo list widget card.
    
    The widget includes:
    - Header with title and stats badges
    - Form for adding new todos
    - List of existing todos with checkboxes and action buttons
    
    Args:
        todos: List of todo items with id, title, completed fields
        thread_id: The thread ID for widget identification
        
    Returns:
        A Card widget containing the todo list UI
    """
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
                    color="warning",
                ),
                Badge(
                    id="completed_badge", 
                    label=f"{completed_count} done",
                    color="info",
                ),
            ]
        )
    )
    
    children.append(Divider(id="divider1"))
    
    # Add todo form - use onSubmitAction on Form to capture input values
    children.append(
        Form(
            id="add_todo_form",
            onSubmitAction=ActionConfig(
                type="add_todo_form",
                handler="server",
            ),
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
                            submit=True,
                        ),
                    ]
                )
            ]
        )
    )
    
    children.append(Spacer(id="spacer2"))
    
    # Todo list items or empty state
    if not todos:
        children.append(
            Box(
                id="empty_state",
                children=[
                    Text(id="empty_icon", value="🎉", textAlign="center"),
                    Text(
                        id="empty_text", 
                        value="No todos yet! Add one above or ask me to add tasks.", 
                        textAlign="center"
                    ),
                ]
            )
        )
    else:
        for todo in todos:
            children.append(_build_todo_item(todo))
        
        # Add "All caught up!" message when no pending tasks
        if pending_count == 0:
            children.append(Spacer(id="spacer3"))
            children.append(
                Box(
                    id="all_done_state",
                    children=[
                        Row(
                            id="all_done_row",
                            children=[
                                Text(id="all_done_icon", value="✅"),
                                Text(
                                    id="all_done_text", 
                                    value="All caught up! No pending tasks left.",
                                ),
                            ]
                        )
                    ]
                )
            )
    
    return Card(id=f"todo_widget_{thread_id}", children=children)


def _build_todo_item(todo: dict) -> Row:
    """
    Build a single todo item row.
    
    Args:
        todo: Todo item with id, title, completed fields
        
    Returns:
        A Row widget representing the todo item
    """
    is_completed = todo["completed"]
    todo_id = todo["id"]
    
    row_children = [
        Checkbox(
            id=f"check_{todo_id}",
            name=f"check_{todo_id}",
            defaultChecked=is_completed,
            onChangeAction=ActionConfig(
                type="toggle_todo",
                handler="server",
                payload={"todo_id": todo_id}
            ),
        ),
        Text(
            id=f"text_{todo_id}", 
            value=todo["title"],
            lineThrough=is_completed,
            color="secondary" if is_completed else None,
        ),
    ]
    
    # Add "Done" badge for completed items
    if is_completed:
        row_children.append(
            Badge(
                id=f"done_badge_{todo_id}",
                label="Done",
                color="secondary",
            )
        )
    
    row_children.append(Spacer(id=f"spacer_{todo_id}"))
    
    # Complete button - soft variant with success (green) color
    row_children.append(
        Button(
            id=f"complete_{todo_id}",
            label="✓",
            size="sm",
            color="success",
            variant="soft",
            onClickAction=ActionConfig(
                type="complete_todo",
                handler="server",
                payload={"todo_id": todo_id}
            ),
        )
    )
    
    # Delete button - soft variant with secondary color
    row_children.append(
        Button(
            id=f"delete_{todo_id}",
            label="🗑",
            size="sm",
            color="secondary",
            variant="soft",
            onClickAction=ActionConfig(
                type="delete_todo",
                handler="server",
                payload={"todo_id": todo_id}
            ),
        )
    )
    
    return Row(id=f"todo_{todo_id}", children=row_children)
