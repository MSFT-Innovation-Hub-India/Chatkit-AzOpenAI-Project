# ChatKit Sample Architecture

This document explains the modular architecture of this ChatKit sample project, the role of the ChatKit server, and provides a guide for implementing new use cases.

## Table of Contents

1. [What is ChatKit?](#what-is-chatkit)
2. [How Widget Rendering Works](#how-widget-rendering-works)
3. [Architecture Overview](#architecture-overview)
4. [ChatKit Server: Middleware or Backend?](#chatkit-server-middleware-or-backend)
5. [Production Deployment Patterns](#production-deployment-patterns)
6. [Project Structure](#project-structure)
7. [Core Components](#core-components)
8. [How the Todo Use Case Works](#how-the-todo-use-case-works)
9. [Creating a New Use Case](#creating-a-new-use-case)
10. [Widget Reference](#widget-reference)

---

## What is ChatKit?

ChatKit is OpenAI's protocol for building **self-hosted chat applications** with rich, interactive UIs. It provides:

| Feature | Description |
|---------|-------------|
| **Streaming Protocol** | Real-time message streaming over WebSocket/SSE |
| **Interactive Widgets** | Rich UI components (buttons, forms, checkboxes, cards) |
| **Action Handling** | Server-side handling of user interactions |
| **Thread Management** | Built-in conversation thread persistence |

### ChatKit vs Standard Agent Applications

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STANDARD AGENTIC APPLICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User  ──►  REST API  ──►  Agent/LLM  ──►  Text Response                   │
│                                                                             │
│   • Text-only responses                                                     │
│   • No built-in UI framework                                                │
│   • Custom frontend needed                                                  │
│   • Request/response pattern                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHATKIT APPLICATION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User  ──►  ChatKit UI  ◄──►  ChatKit Server  ──►  Agent/LLM               │
│                  │                    │                                     │
│                  │                    ▼                                     │
│                  │              ┌──────────┐                                │
│                  ◄──────────────┤ Widgets  │ (Buttons, Forms, Cards)        │
│                  │              └──────────┘                                │
│                  │                    │                                     │
│                  ◄────────────────────┘ Actions (Click, Submit, Toggle)     │
│                                                                             │
│   • Rich interactive widgets                                                │
│   • Real-time streaming                                                     │
│   • Built-in UI components                                                  │
│   • Bidirectional communication                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Differences:**

| Aspect | Standard Agent App | ChatKit App |
|--------|-------------------|-------------|
| **Output** | Text only | Text + Interactive Widgets |
| **Interaction** | One-way (request → response) | Bidirectional (actions ↔ updates) |
| **UI** | Build your own | Pre-built components |
| **Streaming** | Optional | Built-in |
| **State** | Manual | Thread-based |

---

## How Widget Rendering Works

This is a crucial concept to understand: **widgets are NOT HTML sent from the server**. Instead:

### The Widget Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. SERVER: Build Widget (Python)                                           │
│                                                                             │
│     widget = Card(                                                          │
│         id="todo_widget",                                                   │
│         children=[                                                          │
│             Title(id="t1", value="My Todos", size="lg"),                    │
│             Button(id="b1", label="Add", color="primary", ...)              │
│         ]                                                                   │
│     )                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ SSE Stream (JSON)
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. WIRE FORMAT: JSON Widget Definition                                     │
│                                                                             │
│     {                                                                       │
│       "type": "Card",                                                       │
│       "id": "todo_widget",                                                  │
│       "children": [                                                         │
│         { "type": "Title", "id": "t1", "value": "My Todos", "size": "lg" }, │
│         { "type": "Button", "id": "b1", "label": "Add", "color": "primary" }│
│       ]                                                                     │
│     }                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ JavaScript parses JSON
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. CLIENT: Render to HTML (JavaScript)                                     │
│                                                                             │
│     function renderWidgetComponent(component) {                             │
│       switch (component.type.toLowerCase()) {                               │
│         case 'title':                                                       │
│           const h3 = document.createElement('h3');                          │
│           h3.textContent = component.value;                                 │
│           return h3;                                                        │
│         case 'button':                                                      │
│           const btn = document.createElement('button');                     │
│           btn.textContent = component.label;                                │
│           btn.onclick = () => handleWidgetAction(component.onClickAction);  │
│           return btn;                                                       │
│       }                                                                     │
│     }                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ DOM elements created
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. BROWSER: Final HTML                                                     │
│                                                                             │
│     <div class="widget-card">                                               │
│       <h3 class="widget-title lg">My Todos</h3>                             │
│       <button class="widget-button primary">Add</button>                    │
│     </div>                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Points

1. **Server sends JSON, not HTML** - Widgets are serialized as JSON objects with `type`, `id`, and properties
2. **Client interprets JSON** - The frontend JavaScript has a renderer (`renderWidgetComponent`) that creates DOM elements
3. **Widgets are part of the thread** - Widget data is streamed as thread events alongside text messages
4. **Styling is client-side** - CSS classes are applied by the frontend based on widget properties

### Where is the Frontend Served From?

In this project, **FastAPI serves both the API and static files**:

```python
# main.py

# Serve the ChatKit frontend (index.html)
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return FileResponse("static/index.html")

# Serve static assets (JS, CSS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ChatKit API endpoint
@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(body, {})
    return StreamingResponse(result, media_type="text/event-stream")
```

### Do You Need a Separate Web Server?

| Scenario | Separate Server Needed? | Recommendation |
|----------|------------------------|----------------|
| **This sample (vanilla HTML/JS)** | ❌ No | FastAPI serves `static/index.html` directly |
| **React/Vue/Angular SPA** | ⚠️ Optional | Can be served by FastAPI, or use CDN for better caching |
| **Production with CDN** | ✅ Yes (recommended) | Static assets on CDN, API on containers |
| **Next.js / SSR frameworks** | ✅ Yes | Needs Node.js server for SSR |

### React/Vue Implementation Pattern

If using React or another framework:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OPTION 1: Single Server (Simple)                        │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    FastAPI Container                                │   │
│   │  ┌──────────────────────┐  ┌─────────────────────────────────────┐  │   │
│   │  │  /chatkit endpoint   │  │  /static (React build output)       │  │   │
│   │  │  (ChatKit API)       │  │  - index.html                       │  │   │
│   │  │                      │  │  - bundle.js (widget renderer)      │  │   │
│   │  │                      │  │  - styles.css                       │  │   │
│   │  └──────────────────────┘  └─────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   Build: npm run build → copy dist/ to static/                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                 OPTION 2: Separate Hosting (Production)                     │
│                                                                             │
│   ┌─────────────────────────────┐     ┌─────────────────────────────────┐   │
│   │  CDN / Static Hosting       │     │  Container (Azure, AWS, etc.)   │   │
│   │  (Vercel, Cloudflare, S3)   │     │                                 │   │
│   │                             │     │  ┌───────────────────────────┐  │   │
│   │  - index.html               │────►│  │  /chatkit endpoint        │  │   │
│   │  - bundle.js (React app)    │ API │  │  (ChatKit Server + Agent) │  │   │
│   │  - Widget renderer code     │     │  └───────────────────────────┘  │   │
│   └─────────────────────────────┘     └─────────────────────────────────┘   │
│                                                                             │
│   Pros: Global CDN caching, independent deployments                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Widget Renderer is Client-Side

The critical piece is the **widget renderer** - JavaScript code that converts JSON to DOM:

```javascript
// This is what makes widgets work - must be in your frontend code
function renderWidgetComponent(component) {
    const type = component.type.toLowerCase();
    
    switch (type) {
        case 'card':
            const card = document.createElement('div');
            card.className = 'widget-card';
            for (const child of component.children) {
                card.appendChild(renderWidgetComponent(child));
            }
            return card;
            
        case 'button':
            const btn = document.createElement('button');
            btn.textContent = component.label;
            btn.className = `widget-button ${component.color}`;
            btn.onclick = () => handleWidgetAction(component.onClickAction);
            return btn;
            
        // ... other component types
    }
}
```

If you use React, you'd write this as React components:

```jsx
// React equivalent
function WidgetRenderer({ component }) {
  switch (component.type.toLowerCase()) {
    case 'card':
      return (
        <div className="widget-card">
          {component.children.map(child => 
            <WidgetRenderer key={child.id} component={child} />
          )}
        </div>
      );
    case 'button':
      return (
        <button 
          className={`widget-button ${component.color}`}
          onClick={() => handleWidgetAction(component.onClickAction)}
        >
          {component.label}
        </button>
      );
  }
}
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT TIER                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        ChatKit Frontend                               │  │
│  │                    (JavaScript/React/HTML)                            │  │
│  │  • Renders messages and widgets                                       │  │
│  │  • Sends user messages                                                │  │
│  │  • Handles widget actions (clicks, form submits)                      │  │
│  │  • Receives streaming updates                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                      WebSocket / Server-Sent Events                         │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION TIER (ChatKit Server)                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     FastAPI + ChatKit Server                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐    │  │
│  │  │  BaseChatKit    │  │   Use Case      │  │     Agent +         │    │  │
│  │  │  Server         │──│   (Todo, etc)   │──│     Tools           │    │  │
│  │  │                 │  │                 │  │                     │    │  │
│  │  │  • respond()    │  │  • agent.py     │  │  • add_todo         │    │  │
│  │  │  • action()     │  │  • widgets.py   │  │  • list_todos       │    │  │
│  │  │  • streaming    │  │  • actions.py   │  │  • complete_todo    │    │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘    │  │
│  │           │                                          │                │  │
│  │           ▼                                          │                │  │
│  │  ┌─────────────────┐                                 │                │  │
│  │  │  SQLite Store   │◄────────────────────────────────┘                │  │
│  │  │  (Threads, Msgs)│                                                  │  │
│  │  └─────────────────┘                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                          Azure AD / Managed Identity                        │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI SERVICES TIER                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Azure OpenAI                                   │  │
│  │                        (GPT-4o Model)                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ChatKit Server: Middleware or Backend?

### The Short Answer

**The ChatKit Server is your backend application tier**, not traditional middleware. It:

- **Hosts your agent logic** (tools, instructions, business logic)
- **Manages state** (threads, messages, user data)
- **Orchestrates AI calls** (Azure OpenAI integration)
- **Renders widgets** (builds and streams UI components)
- **Handles actions** (processes button clicks, form submissions)

### Why Co-location is Required

The ChatKit server and agent code **must be co-located** (same process/container) because:

1. **Streaming Dependency**: Agent responses stream token-by-token; the ChatKit server must intercept and forward these in real-time
2. **Context Sharing**: Tools set flags on the agent context (e.g., `_show_todo_widget`) that trigger widget streaming
3. **Action → Agent Loop**: Widget actions may need to invoke agent tools or update agent state

```
┌──────────────────────────────────────────────────────────────────┐
│                    SINGLE DEPLOYMENT UNIT                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │   ChatKit Server  ◄───────►  Agent + Tools                 │  │
│  │        │                          │                        │  │
│  │        │        Shared Context    │                        │  │
│  │        └──────────────────────────┘                        │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ✓ Co-located in same process                                   │
│  ✓ Share memory/context                                         │
│  ✓ Real-time streaming                                          │
└──────────────────────────────────────────────────────────────────┘
```

### What Could Be Separated?

| Component | Can Separate? | Notes |
|-----------|---------------|-------|
| **Frontend (ChatKit UI)** | ✅ Yes | Static files can be hosted on CDN |
| **Data Store** | ✅ Yes | Use external database (PostgreSQL, Cosmos DB) |
| **Agent/Tools** | ❌ No* | Must be in same process for streaming |
| **Azure OpenAI** | ✅ Yes | Already external service |

*You could theoretically separate the agent via gRPC streaming, but this adds significant complexity.

---

## Production Deployment Patterns

### Pattern 1: Simple (Recommended for Most Cases)

All components in a single container, horizontally scaled:

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │Container│     │Container│     │Container│
    │   #1    │     │   #2    │     │   #3    │
    │         │     │         │     │         │
    │ ChatKit │     │ ChatKit │     │ ChatKit │
    │ +Agent  │     │ +Agent  │     │ +Agent  │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Shared State   │
                │  (Redis/SQL/    │
                │   Cosmos DB)    │
                └─────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Azure OpenAI   │
                └─────────────────┘
```

**Pros:**
- Simple deployment
- Easy horizontal scaling
- Shared state via external store

**Cons:**
- All components scale together
- Larger container images

### Pattern 2: Separated Frontend

Static frontend on CDN, API on containers:

```
    ┌─────────────────────────────────────────────┐
    │              CDN / Static Hosting           │
    │         (Azure Static Web Apps, S3)         │
    │                                             │
    │   ┌──────────────────────────────────────┐  │
    │   │          ChatKit Frontend            │  │
    │   │          (index.html, JS)            │  │
    │   └──────────────────────────────────────┘  │
    └─────────────────────────────────────────────┘
                          │
                          │ WebSocket/SSE
                          ▼
    ┌─────────────────────────────────────────────┐
    │          Azure Container Apps               │
    │                                             │
    │   ┌──────────────────────────────────────┐  │
    │   │    ChatKit Server + Agent + Tools    │  │
    │   └──────────────────────────────────────┘  │
    └─────────────────────────────────────────────┘
```

**Pros:**
- Frontend cached globally
- Reduced backend load for static assets
- Independent frontend deployments

### Pattern 3: Multi-Tenant / Enterprise

Multiple use cases, shared infrastructure:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    API Gateway / Router                     │
    └─────────────────────────────────────────────────────────────┘
                │                    │                    │
                ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Todo Service   │  │  Support Bot    │  │  Sales Agent    │
    │                 │  │                 │  │                 │
    │  ChatKit+Agent  │  │  ChatKit+Agent  │  │  ChatKit+Agent  │
    │  (Todo tools)   │  │  (FAQ tools)    │  │  (CRM tools)    │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌─────────────────┐         ┌─────────────────┐
           │  Shared State   │         │  Azure OpenAI   │
           │  (Cosmos DB)    │         │  (Shared Pool)  │
           └─────────────────┘         └─────────────────┘
```

**Pros:**
- Independent scaling per use case
- Isolated failures
- Different SLAs per service

---

## Project Structure

```
chatkit-sample/
├── main.py                 # FastAPI application entry point + branding API
├── chatkit_server.py       # Todo-specific ChatKit server (extends BaseChatKitServer)
├── base_server.py          # Reusable base server with Azure OpenAI integration
├── azure_client.py         # Azure OpenAI client management
├── config.py               # Environment configuration (Azure + branding settings)
├── store.py                # SQLite data store (threads + GLOBAL todos)
├── use_cases/              # Use case modules
│   ├── __init__.py         # Package exports
│   └── todo/               # Todo list use case
│       ├── __init__.py     # Public exports
│       ├── agent.py        # Agent definition with tools
│       ├── widgets.py      # Widget builders
│       ├── actions.py      # Action handlers
│       └── database.py     # Todo-specific database operations (legacy)
├── static/
│   ├── index.html          # ChatKit frontend with session management
│   ├── branding.css        # Customizable brand colors/styles
│   └── logo.svg            # Default logo (replaceable)
└── infra/
    ├── main.bicep          # Azure infrastructure as code
    └── main.parameters.json
```

## Data Architecture: Threads vs. Global Data

Understanding the difference between **thread-scoped** and **global** data is crucial:

### Thread-Scoped Data (Conversation Context)
- **Chat messages**: Each conversation thread has its own message history
- **Thread metadata**: Title, timestamps, status per conversation
- **Purpose**: Enables multiple independent conversations

### Global Data (User/Application State)
- **Todos**: Stored globally, visible across ALL conversations
- **Purpose**: User's task list persists regardless of which chat thread they're in

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Thread A (conversation 1)        Thread B (conversation 2)                 │
│  ┌─────────────────────┐          ┌─────────────────────┐                   │
│  │ Message 1           │          │ Message 1           │                   │
│  │ Message 2           │          │ Message 2           │                   │
│  │ Message 3           │          │ ...                 │                   │
│  └─────────────────────┘          └─────────────────────┘                   │
│            │                                │                               │
│            └────────────┬───────────────────┘                               │
│                         ▼                                                   │
│              ┌─────────────────────┐                                        │
│              │   GLOBAL TODOS      │  ◄── Same todos visible in both       │
│              │   ☑ Buy groceries   │      threads                           │
│              │   ☐ Call mom        │                                        │
│              │   ☐ Finish report   │                                        │
│              └─────────────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session Management

The frontend uses `localStorage` to persist the thread ID across page refreshes:

```javascript
// Thread ID persists in browser localStorage
let threadId = localStorage.getItem('chatkit_thread_id');
if (!threadId) {
    threadId = 'thread_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('chatkit_thread_id', threadId);
}
```

- **Page refresh**: Same thread, conversation history preserved
- **"New Chat" button**: Creates new thread, clears conversation but keeps todos

## Core Components

### 1. BaseChatKitServer (`base_server.py`)

The base server provides reusable infrastructure for all ChatKit use cases:

```python
class BaseChatKitServer(ChatKitServer):
    """Base server with Azure OpenAI integration."""
    
    @abstractmethod
    def get_agent(self) -> Agent:
        """Return the agent for this use case."""
        pass
    
    @abstractmethod
    async def action(self, thread, action, sender, context):
        """Handle widget actions."""
        pass
    
    async def post_respond_hook(self, thread, agent_context):
        """Optional: Stream widgets after agent response."""
        pass
    
    async def respond(self, thread, input, context):
        """Handles message flow - DO NOT OVERRIDE."""
        pass
```

**What it handles:**
- Azure OpenAI client initialization
- Agent context creation
- Response streaming
- Widget streaming helper methods

### 2. Use Case Modules (`use_cases/`)

Each use case is a self-contained module with:

| File | Purpose |
|------|---------|
| `agent.py` | Agent definition with tools (function_tool decorators) |
| `widgets.py` | Functions that build ChatKit widgets |
| `actions.py` | Handlers for widget button clicks, form submissions, etc. |
| `database.py` | Data persistence (optional, if use case needs storage) |
| `__init__.py` | Public exports for the use case |

### 3. Specific ChatKit Server (e.g., `chatkit_server.py`)

Your use-case-specific server extends `BaseChatKitServer`:

```python
class TodoChatKitServer(BaseChatKitServer):
    def get_agent(self) -> Agent:
        return create_todo_agent()
    
    async def post_respond_hook(self, thread, agent_context):
        if getattr(agent_context, '_show_todo_widget', False):
            widget = build_todo_widget(...)
            async for event in stream_widget(thread, widget):
                yield event
    
    async def action(self, thread, action, sender, context):
        # Handle widget actions
        ...
```

## How the Todo Use Case Works

### Flow Diagram

```
User Message
     │
     ▼
┌──────────────────────────────────────┐
│  TodoChatKitServer.respond()         │
│  (inherited from BaseChatKitServer)  │
└──────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│  Azure OpenAI   │ ◄── create_todo_agent() provides Agent with tools
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  Agent Tools    │ ──► add_todo, list_todos, complete_todo, delete_todo
│  (agent.py)     │     Set agent_context._show_todo_widget = True
└─────────────────┘
     │
     ▼
┌───────────────────────┐
│  post_respond_hook()  │ ──► build_todo_widget() → stream_widget()
└───────────────────────┘
     │
     ▼
Widget Streamed to Client
```

### Widget Action Flow

```
User Clicks Button/Checkbox
     │
     ▼
Frontend sends: threads.custom_action
     │
     ▼
┌──────────────────────────────┐
│  TodoChatKitServer.action()  │
└──────────────────────────────┘
     │
     ▼
┌───────────────────────────────┐
│  Update Database              │
│  (data_store.add_todo, etc.)  │
└───────────────────────────────┘
     │
     ▼
┌───────────────────────┐
│  build_todo_widget()  │
│  stream_widget()      │
└───────────────────────┘
     │
     ▼
Updated Widget Streamed to Client
```

### How Widget Actions Work (Detailed)

This section explains the complete journey of a button click from the UI to your server handler.

#### Step 1: Define Action in Widget (Python)

When building a widget, you attach an `ActionConfig` to interactive elements:

```python
# use_cases/todo/widgets.py
Button(
    id="add_button",
    label="➕ Add",
    onClickAction=ActionConfig(
        type="add_todo_form",      # Your custom action identifier
        handler="server",          # Route to server (always "server")
        payload={"priority": "high"}  # Optional static data
    )
)
```

#### Step 2: Serialized to JSON (Wire Format)

The widget is serialized and streamed to the client:

```json
{
  "type": "Button",
  "id": "add_button", 
  "label": "➕ Add",
  "onClickAction": {
    "type": "add_todo_form",
    "handler": "server",
    "payload": {"priority": "high"}
  }
}
```

#### Step 3: Client Renders and Attaches Handler (JavaScript)

The frontend creates the button and stores the action config:

```javascript
// static/index.html
case 'button':
    const btn = document.createElement('button');
    btn.textContent = component.label;
    btn.onclick = () => handleWidgetAction(
        component.onClickAction,  // Stored action config
        component.id
    );
    return btn;
```

#### Step 4: User Clicks → Client Sends Action

When clicked, the client collects form data and sends to server:

```javascript
// static/index.html
async function handleWidgetAction(action, componentId) {
    // Collect form data if button is inside a form
    const formData = collectFormData(componentId);  // {todo_text: "Buy milk"}
    
    // Merge form data with action payload
    const payload = { ...action.payload, ...formData };
    // Result: {priority: "high", todo_text: "Buy milk"}
    
    // Send via ChatKit protocol
    await fetch('/chatkit', {
        method: 'POST',
        body: JSON.stringify({
            type: "threads.custom_action",  // ChatKit protocol message
            params: {
                thread_id: currentThreadId,
                item_id: widgetId,
                action: {
                    type: "add_todo_form",    // Your action type
                    payload: payload          // Merged data
                }
            }
        })
    });
}
```

#### Step 5: ChatKit Routes to Your Handler

The ChatKit library parses the request and calls your `action()` method:

```python
# ChatKit library internal (you don't write this)
if request.type == "threads.custom_action":
    await your_server.action(thread, action, sender, context)
```

#### Step 6: Your Action Handler (Your Code)

You implement the business logic:

```python
# chatkit_server.py - YOU write this
async def action(self, thread, action, sender, context):
    action_type = action.type    # "add_todo_form"
    payload = action.payload     # {"priority": "high", "todo_text": "Buy milk"}
    
    if action_type == "add_todo_form":
        todo_text = payload.get("todo_text", "").strip()
        if todo_text:
            await self.data_store.add_todo(thread.id, todo_text)
    
    elif action_type == "delete_todo":
        todo_id = payload.get("todo_id")
        await self.data_store.delete_todo(thread.id, todo_id)
    
    # Stream updated widget back to client
    todos = await self.data_store.list_todos(thread.id)
    widget = build_todo_widget(todos, thread.id)
    async for event in stream_widget(thread, widget):
        yield event
```

#### Key Insight: Agent is NOT Involved

**Actions bypass the LLM entirely.** This is crucial to understand:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TEXT MESSAGE FLOW (uses Agent/LLM)                                         │
│                                                                             │
│  User types: "Add buy milk"                                                 │
│       │                                                                     │
│       ▼                                                                     │
│  respond() → Agent → LLM → Tool call (add_todo) → Widget                    │
│                  ▲                                                          │
│                  │ $$$  LLM tokens consumed                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WIDGET ACTION FLOW (NO Agent/LLM)                                          │
│                                                                             │
│  User clicks: [Add] button                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  action() → Your code → Database → Widget                                   │
│                                                                             │
│  ✓ No LLM call                                                              │
│  ✓ No token cost                                                            │
│  ✓ Instant response                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Summary: Action Components

| Component | Location | Role |
|-----------|----------|------|
| `ActionConfig` | `widgets.py` | Defines action type and static payload |
| `onClickAction` | JSON wire format | Carried to client with widget |
| `handleWidgetAction` | `index.html` (JS) | Collects form data, sends request |
| `threads.custom_action` | ChatKit protocol | Request type that routes to `action()` |
| `action()` method | `chatkit_server.py` | **Your handler** - all business logic |
| Agent/LLM | N/A | **NOT used** for widget actions |

## Creating a New Use Case

### Step 1: Create the Use Case Module

```bash
mkdir use_cases/my_use_case
```

### Step 2: Define Your Agent (`use_cases/my_use_case/agent.py`)

```python
from agents import Agent, function_tool
from agents.run_context import RunContextWrapper
from chatkit.agents import AgentContext

MyContext = AgentContext[Any]

@function_tool(description_override="Do something useful")
async def my_tool(ctx: RunContextWrapper["MyContext"], param: str) -> str:
    """Tool implementation."""
    # Access thread: ctx.context.thread.id
    # Access store: ctx.context.store
    
    # Trigger widget display
    ctx.context._show_my_widget = True
    ctx.context._my_data = some_data
    
    return "Done!"

MY_AGENT_INSTRUCTIONS = """You are a helpful assistant..."""

def create_my_agent() -> Agent["MyContext"]:
    return Agent["MyContext"](
        name="My Assistant",
        instructions=MY_AGENT_INSTRUCTIONS,
        tools=[my_tool],
    )
```

### Step 3: Build Your Widgets (`use_cases/my_use_case/widgets.py`)

```python
from chatkit.widgets import Card, Row, Text, Button, Title
from chatkit.actions import ActionConfig

def build_my_widget(data: list, thread_id: str) -> Card:
    children = [
        Title(id="title", value="My Widget", size="lg"),
    ]
    
    for item in data:
        children.append(
            Row(
                id=f"item_{item['id']}",
                children=[
                    Text(id=f"text_{item['id']}", value=item['name']),
                    Button(
                        id=f"btn_{item['id']}",
                        label="Action",
                        onClickAction=ActionConfig(
                            type="my_action",
                            handler="server",
                            payload={"item_id": item['id']}
                        ),
                    ),
                ]
            )
        )
    
    return Card(id=f"my_widget_{thread_id}", children=children)
```

### Step 4: Handle Actions (`use_cases/my_use_case/actions.py`)

```python
def handle_my_action(action_type: str, payload: dict):
    if action_type == "my_action":
        item_id = payload.get("item_id")
        # Do something with the item
        return {"success": True}
    return {"success": False}
```

### Step 5: Create Your Server (`my_chatkit_server.py`)

```python
from base_server import BaseChatKitServer
from use_cases.my_use_case import create_my_agent, build_my_widget

class MyChatKitServer(BaseChatKitServer):
    def get_agent(self):
        return create_my_agent()
    
    async def post_respond_hook(self, thread, agent_context):
        if getattr(agent_context, '_show_my_widget', False):
            data = getattr(agent_context, '_my_data', [])
            widget = build_my_widget(data, thread.id)
            async for event in stream_widget(thread, widget):
                yield event
    
    async def action(self, thread, action, sender, context):
        action_type = action.type
        payload = action.payload or {}
        
        # Handle the action
        if action_type == "my_action":
            # Update data
            ...
        
        # Stream updated widget
        widget = build_my_widget(updated_data, thread.id)
        async for event in stream_widget(thread, widget):
            yield event
```

### Step 6: Register in `main.py`

```python
from my_chatkit_server import MyChatKitServer

chatkit_server = MyChatKitServer(data_store)
```

## Widget Reference

### Available Widget Components

| Component | Key Properties |
|-----------|---------------|
| `Card` | `id`, `children` |
| `Row` | `id`, `children` |
| `Title` | `id`, `value`, `size` ('sm', 'md', 'lg') |
| `Text` | `id`, `value`, `color`, `textAlign`, `lineThrough` |
| `Button` | `id`, `label`, `color`, `size`, `onClickAction` |
| `Checkbox` | `id`, `name`, `defaultChecked`, `onChangeAction` |
| `Input` | `id`, `name`, `placeholder` |
| `Form` | `id`, `children` |
| `Badge` | `id`, `label`, `color` |
| `Divider` | `id` |
| `Spacer` | `id` |
| `Box` | `id`, `children` |

### ActionConfig

```python
ActionConfig(
    type="action_type",        # String identifier for the action
    handler="server",          # Always "server" for backend handling
    payload={"key": "value"}   # Optional data to pass with action
)
```

---

## Branding & Customization

The application supports full branding customization via environment variables and CSS:

### Environment Variables

```env
BRAND_NAME=My Company Todos      # Header title
BRAND_TAGLINE=Stay Organized     # Header subtitle
BRAND_LOGO_URL=/static/logo.svg  # Logo image URL
BRAND_PRIMARY_COLOR=#0078d4      # Primary brand color
BRAND_FAVICON_URL=/static/favicon.ico
```

### Branding API

The `/api/branding` endpoint returns branding configuration as JSON:

```json
{
  "name": "My Company Todos",
  "tagline": "Stay Organized",
  "logoUrl": "/static/logo.svg",
  "primaryColor": "#0078d4",
  "faviconUrl": "/static/favicon.ico"
}
```

### CSS Customization

Edit `static/branding.css` to customize colors, typography, and spacing:

```css
:root {
    /* Primary brand colors */
    --brand-primary: #0078d4;
    --brand-primary-hover: #106ebe;
    
    /* Header gradient */
    --header-gradient-start: #0078d4;
    --header-gradient-end: #005a9e;
    
    /* Status colors */
    --color-success: #28a745;
    --color-danger: #dc3545;
    
    /* Logo sizing */
    --logo-width: 32px;
    --logo-height: 32px;
}
```

### Branding Flow

```
Page Load → fetch(/api/branding) → Apply to DOM
                  │
                  ▼
            config.py reads
            env variables
```

---

## Best Practices

1. **Separation of Concerns**: Keep agent, widgets, and actions in separate files
2. **Trigger Flags**: Use `agent_context._show_*` flags to trigger widget display
3. **Streaming**: Always use `async for event in stream_widget(...)` for widget updates
4. **IDs**: Every widget component needs a unique `id` property
5. **Action Types**: Use descriptive action type strings (e.g., `"add_item"`, `"delete_item"`)
6. **Error Handling**: Handle missing payloads gracefully in action handlers

---

## Summary: Why Use ChatKit?

### When to Use ChatKit

| Use ChatKit When... | Use Standard Agent When... |
|---------------------|---------------------------|
| You need interactive UI elements | Text responses are sufficient |
| Users need to take actions (click, submit) | Read-only chat experience |
| Real-time streaming is important | Request/response is fine |
| You want consistent UI components | Custom frontend is preferred |
| Building user-facing applications | Building API-first services |

### Key Takeaways

1. **ChatKit is not middleware** — it's your application backend that happens to speak the ChatKit protocol
2. **Agent and ChatKit must be co-located** — streaming requires tight integration
3. **Widgets are server-rendered** — the backend builds the UI, not the frontend
4. **Actions are server-handled** — user interactions go to your backend, not just the LLM
5. **The pattern is reusable** — extend `BaseChatKitServer` for new use cases

### The Value Proposition

```
Traditional Agent App:
  User → [Your Frontend] → [Your API] → [Agent] → Text → [Your Frontend renders it]
                    ↑
            You build ALL of this

ChatKit App:
  User → [ChatKit UI] → [ChatKit Server] → [Agent] → Text + Widgets
                    ↑                              ↑
         Pre-built UI              Your business logic here
```

ChatKit lets you focus on your **agent logic and business rules** while providing a **production-ready chat interface** out of the box.
