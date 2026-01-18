"""
SQLite-based data store for ChatKit.
Implements the Store interface required by ChatKit server.
"""

import json
import asyncio
import uuid
import aiosqlite
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from chatkit.store import Store, ThreadMetadata, ThreadItem, Page, Attachment
from chatkit.types import ActiveStatus, LockedStatus, ClosedStatus
from pydantic import TypeAdapter

# Create a TypeAdapter for parsing thread items from JSON
_thread_item_adapter = TypeAdapter(ThreadItem)


class SQLiteStore(Store):
    """
    SQLite-based persistent store for ChatKit threads and messages.
    Suitable for local development and small-scale deployments.
    For production on Azure, consider using Azure Cosmos DB.
    """
    
    def __init__(self, db_path: str = "./data/chatkit.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def _ensure_db(self) -> aiosqlite.Connection:
        """Ensure database connection exists and tables are created."""
        if self._db is None:
            # Create directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
            
            # Create tables
            await self._db.executescript("""
                CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT DEFAULT 'ready',
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    data TEXT,
                    created_at TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    data TEXT,
                    created_at TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS todos (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    title TEXT,
                    completed INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_items_thread_id ON items(thread_id);
                CREATE INDEX IF NOT EXISTS idx_attachments_thread_id ON attachments(thread_id);
                CREATE INDEX IF NOT EXISTS idx_todos_thread_id ON todos(thread_id);
            """)
            await self._db.commit()
        
        return self._db
    
    # ----- Store interface implementation -----
    
    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        """Load a thread's metadata by id."""
        db = await self._ensure_db()
        
        async with db.execute(
            "SELECT * FROM threads WHERE id = ?", (thread_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                # Parse created_at from database
                created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
                return ThreadMetadata(
                    id=row["id"],
                    title=row["title"],
                    status=ActiveStatus(),
                    created_at=created_at,
                )
        
        # If thread doesn't exist, create it
        return await self._create_thread(thread_id, context)
    
    async def _create_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        """Create a new thread."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        thread = ThreadMetadata(
            id=thread_id, 
            title="New Chat", 
            status=ActiveStatus(),
            created_at=now
        )
        
        async with self._lock:
            await db.execute(
                "INSERT OR REPLACE INTO threads (id, title, status, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (thread_id, thread.title, "active", "{}", now_iso, now_iso)
            )
            await db.commit()
        
        return thread
    
    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        """Persist thread metadata."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        
        # Get status type string from the status object
        status_str = thread.status.type if thread.status else "active"
        
        async with self._lock:
            await db.execute(
                "INSERT OR REPLACE INTO threads (id, title, status, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM threads WHERE id = ?), ?), ?)",
                (thread.id, thread.title, status_str, "{}", thread.id, now, now)
            )
            await db.commit()
    
    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: Any,
    ) -> Page[ThreadItem]:
        """Load a page of thread items with pagination."""
        db = await self._ensure_db()
        
        order_dir = "DESC" if order == "desc" else "ASC"
        
        if after:
            query = f"SELECT * FROM items WHERE thread_id = ? AND id > ? ORDER BY created_at {order_dir} LIMIT ?"
            params = (thread_id, after, limit + 1)
        else:
            query = f"SELECT * FROM items WHERE thread_id = ? ORDER BY created_at {order_dir} LIMIT ?"
            params = (thread_id, limit + 1)
        
        items = []
        has_more = False
        last_id = None
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            for i, row in enumerate(rows):
                if i >= limit:
                    has_more = True
                    break
                item_data = json.loads(row["data"])
                # Parse dict back into proper ThreadItem type
                item = _thread_item_adapter.validate_python(item_data)
                items.append(item)
                last_id = row["id"]
        
        return Page(data=items, has_more=has_more, after=last_id if has_more else None)
    
    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: Any
    ) -> None:
        """Persist a newly created thread item."""
        await self.save_item(thread_id, item, context)
    
    async def save_item(
        self, thread_id: str, item: ThreadItem, context: Any
    ) -> None:
        """Upsert a thread item by id."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        
        # Serialize item to JSON - use model_dump with mode='json' for proper serialization
        if hasattr(item, 'model_dump'):
            item_data = item.model_dump(mode='json')
        else:
            item_data = dict(item)
        item_id = item_data.get('id', f"item_{uuid.uuid4().hex[:12]}")
        
        async with self._lock:
            await db.execute(
                "INSERT OR REPLACE INTO items (id, thread_id, data, created_at) VALUES (?, ?, ?, COALESCE((SELECT created_at FROM items WHERE id = ?), ?))",
                (item_id, thread_id, json.dumps(item_data), item_id, now)
            )
            await db.commit()
    
    async def load_item(
        self, thread_id: str, item_id: str, context: Any
    ) -> ThreadItem:
        """Load a thread item by id."""
        db = await self._ensure_db()
        
        async with db.execute(
            "SELECT * FROM items WHERE id = ? AND thread_id = ?", (item_id, thread_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                item_data = json.loads(row["data"])
                return _thread_item_adapter.validate_python(item_data)
        
        raise KeyError(f"Item {item_id} not found in thread {thread_id}")
    
    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Delete a thread and its items."""
        db = await self._ensure_db()
        
        async with self._lock:
            await db.execute("DELETE FROM items WHERE thread_id = ?", (thread_id,))
            await db.execute("DELETE FROM attachments WHERE thread_id = ?", (thread_id,))
            await db.execute("DELETE FROM todos WHERE thread_id = ?", (thread_id,))
            await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
            await db.commit()
    
    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: Any
    ) -> None:
        """Delete a thread item by id."""
        db = await self._ensure_db()
        
        async with self._lock:
            await db.execute(
                "DELETE FROM items WHERE id = ? AND thread_id = ?", (item_id, thread_id)
            )
            await db.commit()
    
    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: Any,
    ) -> Page[ThreadMetadata]:
        """Load a page of threads with pagination."""
        db = await self._ensure_db()
        
        order_dir = "DESC" if order == "desc" else "ASC"
        
        if after:
            query = f"SELECT * FROM threads WHERE id > ? ORDER BY updated_at {order_dir} LIMIT ?"
            params = (after, limit + 1)
        else:
            query = f"SELECT * FROM threads ORDER BY updated_at {order_dir} LIMIT ?"
            params = (limit + 1,)
        
        threads = []
        has_more = False
        last_id = None
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            for i, row in enumerate(rows):
                if i >= limit:
                    has_more = True
                    break
                
                # Parse created_at from ISO string (use bracket notation for sqlite3.Row)
                created_at_str = row["created_at"] if "created_at" in row.keys() else row["updated_at"]
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                else:
                    created_at = datetime.now(timezone.utc)
                
                # Build proper ThreadStatus object
                status_str = row["status"] if "status" in row.keys() else "active"
                if status_str == "locked":
                    status = LockedStatus()
                elif status_str == "closed":
                    status = ClosedStatus()
                else:
                    status = ActiveStatus()
                
                threads.append(ThreadMetadata(
                    id=row["id"],
                    title=row["title"],
                    created_at=created_at,
                    status=status,
                ))
                last_id = row["id"]
        
        return Page(data=threads, has_more=has_more, after=last_id if has_more else None)
    
    # ----- Attachment methods -----
    
    async def save_attachment(self, attachment: Attachment, context: Any) -> None:
        """Persist attachment metadata."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        
        attachment_data = attachment.model_dump() if hasattr(attachment, 'model_dump') else dict(attachment)
        
        async with self._lock:
            await db.execute(
                "INSERT OR REPLACE INTO attachments (id, thread_id, data, created_at) VALUES (?, ?, ?, ?)",
                (attachment.id, getattr(attachment, 'thread_id', ''), json.dumps(attachment_data), now)
            )
            await db.commit()
    
    async def load_attachment(
        self, attachment_id: str, context: Any
    ) -> Attachment:
        """Load attachment metadata by id."""
        db = await self._ensure_db()
        
        async with db.execute(
            "SELECT * FROM attachments WHERE id = ?", (attachment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["data"])
        
        raise KeyError(f"Attachment {attachment_id} not found")
    
    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        """Delete attachment metadata by id."""
        db = await self._ensure_db()
        
        async with self._lock:
            await db.execute(
                "DELETE FROM attachments WHERE id = ?", (attachment_id,)
            )
            await db.commit()
    
    # Todo-specific methods
    # Note: Todos are GLOBAL (not tied to thread_id) because they represent user data,
    # not conversation state. The thread_id parameter is kept for API compatibility
    # but is ignored for queries (only stored for reference).
    
    async def add_todo(self, thread_id: str, title: str) -> Dict[str, Any]:
        """Add a todo item (global, not thread-specific)."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        todo_id = f"todo_{uuid.uuid4().hex[:12]}"
        
        async with self._lock:
            await db.execute(
                "INSERT INTO todos (id, thread_id, title, completed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (todo_id, thread_id, title, 0, now, now)
            )
            await db.commit()
        
        return {
            "id": todo_id,
            "title": title,
            "completed": False,
            "created_at": now
        }
    
    async def complete_todo(self, thread_id: str, todo_id: str) -> Optional[Dict[str, Any]]:
        """Mark a todo as completed (global lookup by todo_id only)."""
        db = await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        
        async with self._lock:
            await db.execute(
                "UPDATE todos SET completed = 1, updated_at = ? WHERE id = ?",
                (now, todo_id)
            )
            await db.commit()
        
        async with db.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "title": row["title"],
                    "completed": bool(row["completed"]),
                    "updated_at": row["updated_at"]
                }
        return None
    
    async def delete_todo(self, thread_id: str, todo_id: str) -> bool:
        """Delete a todo item (global lookup by todo_id only)."""
        db = await self._ensure_db()
        
        async with self._lock:
            cursor = await db.execute(
                "DELETE FROM todos WHERE id = ?", (todo_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def list_todos(self, thread_id: str) -> List[Dict[str, Any]]:
        """List ALL todos (global, ignores thread_id)."""
        db = await self._ensure_db()
        
        todos = []
        async with db.execute(
            "SELECT * FROM todos ORDER BY created_at ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                todos.append({
                    "id": row["id"],
                    "title": row["title"],
                    "completed": bool(row["completed"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
        
        return todos
    
    async def close(self):
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
