# ChatKit Todo Sample with Azure OpenAI

A self-hosted ChatKit todo list application powered by Azure OpenAI, designed for deployment on Azure Container Apps.

![Architecture Diagram](docs/architecture.png)

## 🎯 Features

- **ChatKit Integration**: Uses OpenAI's ChatKit for a modern chat UI
- **Azure OpenAI**: Powered by Azure OpenAI with GPT-4o model
- **Todo Management**: Natural language task management
- **Self-Hosted**: Full control over your data and infrastructure
- **Azure Container Apps**: Cloud-native deployment with auto-scaling

## 📁 Project Structure

```
chatkit-sample/
├── main.py                  # FastAPI application entry point
├── config.py                # Configuration management
├── chatkit_server.py        # ChatKit server implementation
├── azure_client.py          # Azure OpenAI client manager
├── store.py                 # SQLite data store
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build configuration
├── azure.yaml              # Azure Developer CLI configuration
├── .env.example            # Environment variables template
├── static/
│   └── index.html          # ChatKit frontend
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

## 📚 Resources

- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/guides/custom-chatkit)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License.
