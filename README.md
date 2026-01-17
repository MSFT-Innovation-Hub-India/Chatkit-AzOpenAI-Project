# ChatKit Todo Sample with Azure OpenAI

A self-hosted ChatKit todo list application powered by Azure OpenAI, featuring interactive widgets and a modular architecture designed for reuse and extension.

![Architecture Diagram](docs/architecture.png)

## 🎯 Features

- **ChatKit Integration**: Uses OpenAI's ChatKit for a modern chat UI with interactive widgets
- **Azure OpenAI**: Powered by Azure OpenAI with GPT-4o model
- **Interactive Widgets**: Rich UI with buttons, checkboxes, forms, and badges
- **Global Todo Persistence**: Todos persist across sessions and conversations
- **Customizable Branding**: Easy logo, colors, and styling customization
- **Modular Architecture**: Easily extend with new use cases
- **Self-Hosted**: Full control over your data and infrastructure
- **Azure Container Apps**: Cloud-native deployment with auto-scaling

## 🤔 What is ChatKit?

ChatKit is OpenAI's protocol for building **self-hosted chat applications** with rich, interactive UIs. Unlike traditional agent applications that only return text, ChatKit enables:

| Standard Agent | ChatKit Application |
|----------------|---------------------|
| Text-only responses | Text + Interactive widgets |
| One-way communication | Bidirectional (actions ↔ updates) |
| Build your own UI | Pre-built UI components |
| Request/response | Real-time streaming |

### How Widget Rendering Works

**Widgets are NOT HTML sent from the server.** The flow is:

1. **Server** builds widget objects in Python (`Card`, `Button`, `Row`, etc.)
2. **Server** streams widget as JSON over SSE (e.g., `{"type": "Button", "label": "Add"}`)
3. **Client** JavaScript parses JSON and creates DOM elements
4. **Browser** renders the final HTML

```
Server (Python)           Wire (JSON)              Client (JavaScript)
─────────────────    ─────────────────────    ─────────────────────────
Button(label="Add")  → {"type":"Button",...}  → <button>Add</button>
```

### Where is the UI Served From?

In this project, **FastAPI serves both**:
- `/chatkit` - The ChatKit API endpoint (streaming JSON)
- `/` and `/static` - The frontend HTML/JS/CSS files

```python
# main.py serves the frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"))
```

**No separate web server is needed** for this vanilla HTML/JS implementation. If using React/Vue, you can either:
- Build and copy to `static/` (simple)
- Host frontend on CDN separately (production)

For detailed architecture, deployment patterns, and React examples, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📁 Project Structure

```
chatkit-sample/
├── main.py                  # FastAPI application entry point
├── config.py                # Configuration management (incl. branding)
├── base_server.py           # Reusable base server with Azure OpenAI
├── azure_client.py          # Azure OpenAI client manager
├── store.py                 # SQLite data store (global todos)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build configuration
├── azure.yaml              # Azure Developer CLI configuration
├── ARCHITECTURE.md         # Detailed architecture documentation
├── .env.example            # Environment variables template
├── use_cases/              # Modular use case implementations
│   └── todo/               # Todo list use case (complete module)
│       ├── __init__.py     # Exports TodoChatKitServer
│       ├── server.py       # ChatKit server for this use case
│       ├── agent.py        # Agent with tools
│       ├── widgets.py      # Widget builders
│       ├── actions.py      # Action handlers
│       └── database.py     # Data persistence (legacy)
├── static/
│   ├── index.html          # ChatKit frontend
│   ├── branding.css        # Customizable brand colors/styles
│   └── logo.svg            # Default logo (replace with your own)
└── infra/
    ├── main.bicep          # Azure infrastructure as code
    └── main.parameters.json # Deployment parameters
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Azure subscription with:
  - Azure OpenAI with GPT-4o deployment
  - (Optional) Azure Container Apps for deployment
- Azure CLI and Azure Developer CLI (azd)

### Local Development

1. **Clone and navigate to the project**
   ```bash
   cd chatkit-sample
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Azure OpenAI settings:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

5. **Login to Azure (for authentication)**
   ```bash
   az login
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

7. **Open your browser**
   Navigate to `http://localhost:8000`

## 🎨 Branding & Customization

Customize the app's appearance to match your organization's brand:

### Environment Variables

```env
# In your .env file
BRAND_NAME=My Company Todos
BRAND_TAGLINE=Stay Organized
BRAND_LOGO_URL=/static/logo.svg
BRAND_PRIMARY_COLOR=#0078d4
BRAND_FAVICON_URL=/static/favicon.ico
```

### CSS Customization

Edit `static/branding.css` for deeper styling:

```css
:root {
    --brand-primary: #0078d4;        /* Primary brand color */
    --header-gradient-start: #0078d4; /* Header gradient */
    --header-gradient-end: #005a9e;
    --color-success: #28a745;         /* Success/complete color */
    --color-danger: #dc3545;          /* Delete/error color */
}
```

### Custom Logo

Replace `static/logo.svg` with your own logo file (SVG, PNG, or any web format).

## 💬 Using the Todo Assistant

The ChatKit Todo app understands natural language commands:

- **Add tasks**: "Add buy groceries to my list" or "I need to call mom tomorrow"
- **List tasks**: "Show me my todos" or "What's on my list?"
- **Complete tasks**: "I finished the grocery shopping" or "Mark todo_abc123 as complete"
- **Delete tasks**: "Remove the call mom task" or "Delete todo_abc123"

### Example Conversation

```
You: Add three tasks: buy groceries, finish report, and call mom
Assistant: I've added 3 tasks to your todo list:
1. ⬜ buy groceries (ID: todo_a1b2c3)
2. ⬜ finish report (ID: todo_d4e5f6)
3. ⬜ call mom (ID: todo_g7h8i9)

You: I finished the groceries
Assistant: ✅ Marked "buy groceries" as complete!

You: Show my todos
Assistant: Here are your todos:
1. ✅ buy groceries (ID: todo_a1b2c3)
2. ⬜ finish report (ID: todo_d4e5f6)
3. ⬜ call mom (ID: todo_g7h8i9)

Total: 3 items (1 completed, 2 pending)
```

## ☁️ Deploy to Azure Container Apps

### Using Azure Developer CLI (Recommended)

1. **Install Azure Developer CLI**
   ```bash
   # Windows
   winget install Microsoft.Azd
   
   # macOS
   brew install azure/azd/azd
   
   # Linux
   curl -fsSL https://aka.ms/install-azd.sh | bash
   ```

2. **Login and initialize**
   ```bash
   azd auth login
   azd init
   ```

3. **Configure environment variables**
   ```bash
   azd env set AZURE_OPENAI_ENDPOINT "https://your-resource.openai.azure.com/"
   azd env set AZURE_OPENAI_DEPLOYMENT "gpt-4o"
   ```

4. **Deploy**
   ```bash
   azd up
   ```

   This will:
   - Provision Azure Container Registry, Container Apps Environment, and Container App
   - Build and push the Docker image
   - Deploy the application
   - Output the application URL

### Manual Deployment

1. **Build the Docker image**
   ```bash
   docker build -t chatkit-todo:latest .
   ```

2. **Test locally with Docker**
   ```bash
   docker run -p 8000:8000 \
     -e AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
     -e AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
     chatkit-todo:latest
   ```

3. **Deploy to Azure Container Registry**
   ```bash
   az acr login --name <your-acr-name>
   docker tag chatkit-todo:latest <your-acr-name>.azurecr.io/chatkit-todo:latest
   docker push <your-acr-name>.azurecr.io/chatkit-todo:latest
   ```

4. **Deploy infrastructure with Bicep**
   ```bash
   az deployment group create \
     --resource-group <your-rg> \
     --template-file infra/main.bicep \
     --parameters baseName=chatkit azureOpenAIEndpoint="https://..." azureOpenAIDeployment=gpt-4o
   ```

## 🔐 Authentication

The application uses **Azure DefaultAzureCredential** which supports:

- **Local Development**: Azure CLI credentials (`az login`)
- **Azure-Hosted**: Managed Identity (automatically configured)
- **CI/CD**: Service Principal with environment variables

### Required Azure OpenAI RBAC Role

Grant the identity `Cognitive Services OpenAI User` role on your Azure OpenAI resource:

```bash
az role assignment create \
  --assignee <identity-principal-id> \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<aoai-resource>
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Container Apps                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  ChatKit Todo App                   │    │
│  │  ┌───────────────┐  ┌──────────────────────────┐   │    │
│  │  │   FastAPI     │  │    ChatKit Server        │   │    │
│  │  │   (main.py)   │──│  (chatkit_server.py)     │   │    │
│  │  └───────────────┘  └──────────────────────────┘   │    │
│  │          │                      │                   │    │
│  │          │              ┌───────┴───────┐          │    │
│  │          │              │   Todo Tools   │          │    │
│  │          │              │ (add/complete/ │          │    │
│  │          │              │  delete/list)  │          │    │
│  │          ▼              └───────┬───────┘          │    │
│  │  ┌───────────────┐              │                   │    │
│  │  │ SQLite Store  │◄─────────────┘                   │    │
│  │  │  (store.py)   │                                  │    │
│  │  └───────────────┘                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │ Managed Identity
                            ▼
                 ┌─────────────────────┐
                 │   Azure OpenAI      │
                 │   (GPT-4o model)    │
                 └─────────────────────┘
```

### Components

| Component | Description |
|-----------|-------------|
| **FastAPI** | Web framework serving the ChatKit endpoint and static files |
| **ChatKit Server** | Implements OpenAI's ChatKit protocol for self-hosted chat |
| **Azure OpenAI Client** | Manages Azure OpenAI connections with auto-refresh tokens |
| **SQLite Store** | Persists threads, messages, and todo items |
| **Todo Tools** | Function tools for add, complete, delete, and list operations |

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Required |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o` |
| `AZURE_OPENAI_API_VERSION` | API version | `2025-01-01-preview` |
| `APP_HOST` | Application bind host | `0.0.0.0` |
| `APP_PORT` | Application port | `8000` |
| `DATA_STORE_PATH` | SQLite database path | `./data/chatkit.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `BRAND_NAME` | App title in header | `ChatKit Todo` |
| `BRAND_TAGLINE` | Subtitle in header | `AI-Powered Task Management` |
| `BRAND_LOGO_URL` | Logo image URL | `/static/logo.png` |
| `BRAND_PRIMARY_COLOR` | Primary brand color (hex) | `#0078d4` |
| `BRAND_FAVICON_URL` | Favicon URL | `/static/favicon.ico` |

## 🎨 Branding & Customization

Customize the UI to match your organization's brand identity.

### Environment Variables

The easiest way to customize branding is through environment variables in your `.env` file:

```env
# Branding Configuration
BRAND_NAME=My Company Assistant
BRAND_TAGLINE=Your AI-Powered Helper
BRAND_LOGO_URL=/static/my-logo.png
BRAND_PRIMARY_COLOR=#ff6600
BRAND_FAVICON_URL=/static/my-favicon.ico
```

### Adding Your Logo

1. **Add your logo file** to the `static/` directory:
   ```
   static/
   ├── logo.png          # Your company logo (recommended: 32x32 or 40x40px)
   ├── favicon.ico       # Browser favicon
   └── index.html
   ```

2. **Update environment variables**:
   ```env
   BRAND_LOGO_URL=/static/logo.png
   BRAND_FAVICON_URL=/static/favicon.ico
   ```

3. **External logos** are also supported:
   ```env
   BRAND_LOGO_URL=https://mycompany.com/logo.png
   ```

### CSS Theme Customization

For advanced customization, edit `static/branding.css`:

```css
:root {
    /* Primary brand color - affects buttons, links, accents */
    --brand-primary: #0078d4;
    
    /* Header gradient */
    --header-gradient-start: #1a1a2e;
    --header-gradient-end: #16213e;
    
    /* Background colors */
    --background-primary: #0f0f23;
    --background-secondary: #1a1a2e;
    
    /* Text colors */
    --text-primary: #ffffff;
    --text-secondary: #a0a0b0;
    
    /* Logo dimensions */
    --logo-width: 32px;
    --logo-height: 32px;
}
```

### Example Brand Themes

The `branding.css` file includes commented examples for popular brands:

- **Microsoft** - Blue primary (#0078d4)
- **GitHub** - Purple primary (#8b5cf6)
- **Slack** - Green primary (#4a154b)
- **Salesforce** - Blue primary (#00a1e0)

### API Endpoint

Branding configuration is served at `/api/branding`:

```json
{
    "name": "ChatKit Todo",
    "tagline": "AI-Powered Task Management",
    "logoUrl": "/static/logo.png",
    "primaryColor": "#0078d4",
    "faviconUrl": "/static/favicon.ico"
}
```

This allows frontend applications (including React/Vue) to dynamically load branding at runtime.

## 📚 Resources

- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/guides/custom-chatkit)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

## 🔄 Azure OpenAI vs Standard OpenAI

This project uses **Azure OpenAI** instead of the standard OpenAI endpoints. Here are the key differences:

### Configuration Changes

| Aspect | Standard OpenAI | Azure OpenAI |
|--------|-----------------|--------------|
| **Endpoint** | `https://api.openai.com/v1` | `https://your-resource.openai.azure.com/` |
| **Authentication** | API Key (`OPENAI_API_KEY`) | Azure AD / Managed Identity |
| **Model Reference** | Model name (`gpt-4o`) | Deployment name (custom) |
| **Client** | `AsyncOpenAI` | `AsyncAzureOpenAI` |

### Code Changes Made

1. **Azure Client Manager** (`azure_client.py`):
   ```python
   # Uses Azure-specific client with DefaultAzureCredential
   from openai import AsyncAzureOpenAI
   from azure.identity.aio import DefaultAzureCredential
   
   self.client = AsyncAzureOpenAI(
       azure_endpoint=settings.azure_openai_endpoint,
       azure_ad_token_provider=self._get_token,
       api_version=settings.azure_openai_api_version,
   )
   ```

2. **Model Wrapper** (`base_server.py`):
   ```python
   # Wraps Azure client for OpenAI Agents SDK
   azure_model = OpenAIChatCompletionsModel(
       model=settings.azure_openai_deployment,  # Deployment name, not model name
       openai_client=client,
   )
   ```

3. **Authentication**:
   - Local: Uses `az login` credentials via Azure CLI
   - Azure-hosted: Uses Managed Identity automatically
   - No API keys required in code

### Environment Variables

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o          # Your deployment name
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Note: No OPENAI_API_KEY needed - uses Azure AD authentication
```

### RBAC Requirements

Grant your identity the `Cognitive Services OpenAI User` role:
```bash
az role assignment create \
  --assignee <your-identity> \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<resource>
```

## 🧩 Extending with New Use Cases

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation on:
- The modular use case pattern
- How to create new agents with custom tools
- Building interactive widgets
- Handling widget actions

### Quick Guide

1. Create a new folder: `use_cases/my_use_case/`
2. Define your agent with tools in `agent.py`
3. Build widgets in `widgets.py`
4. Handle actions in `actions.py`
5. Extend `BaseChatKitServer` for your server

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License.
