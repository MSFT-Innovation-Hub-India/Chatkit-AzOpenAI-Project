# Azure OpenAI Adaptations

This document explains what customizations were made to use ChatKit with **Azure OpenAI** instead of the default **OpenAI**, and identifies which components would be unnecessary if using OpenAI directly.

---

## Executive Summary

ChatKit is designed to work with OpenAI directly. This project adds a custom layer to support Azure OpenAI. The key differences are:

| Aspect | With OpenAI (Default) | With Azure OpenAI (This Project) |
|--------|----------------------|----------------------------------|
| **Authentication** | API key | Azure AD / Managed Identity |
| **Client** | `AsyncOpenAI` | `AsyncAzureOpenAI` |
| **Endpoint** | `api.openai.com` | `your-resource.openai.azure.com` |
| **Model reference** | `gpt-4o` (model name) | Deployment name |
| **Custom code needed** | ❌ None | ✅ Client manager, base server |

---

## Files Created/Modified for Azure OpenAI

### 1. `azure_client.py` — **AZURE-SPECIFIC (Would be unnecessary with OpenAI)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  azure_client.py                                      AZURE-ONLY FILE      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PURPOSE: Create and manage AsyncAzureOpenAI client with Azure AD auth     │
│                                                                             │
│  KEY AZURE-SPECIFIC CODE:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  from openai import AsyncAzureOpenAI                                │   │
│  │  from azure.identity import DefaultAzureCredential                  │   │
│  │                                                                     │   │
│  │  # Azure AD authentication (not API key)                            │   │
│  │  credential = DefaultAzureCredential()                              │   │
│  │  token_provider = get_bearer_token_provider(                        │   │
│  │      credential,                                                    │   │
│  │      "https://cognitiveservices.azure.com/.default"                │   │
│  │  )                                                                  │   │
│  │                                                                     │   │
│  │  # Azure-specific client                                            │   │
│  │  client = AsyncAzureOpenAI(                                         │   │
│  │      azure_endpoint=endpoint,           # ← Azure resource URL      │   │
│  │      azure_ad_token_provider=token,     # ← Azure AD (not API key)  │   │
│  │      api_version="2025-01-01-preview",  # ← Azure API versioning    │   │
│  │  )                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WITH OPENAI DIRECTLY: This entire file would be replaced by:              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  from openai import AsyncOpenAI                                     │   │
│  │  client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why it exists:**
- Azure OpenAI uses Azure AD tokens (Managed Identity, CLI credentials) instead of API keys
- Azure requires `azure_endpoint` (resource URL) + `api_version` parameters
- Token refresh is automatic but requires `get_bearer_token_provider`

**With OpenAI directly:** Delete this file. Use `AsyncOpenAI(api_key=...)` directly.

---

### 2. `base_server.py` — **CONTAINS AZURE-SPECIFIC MODEL WRAPPING**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  base_server.py                                       MIXED (Azure + Core) │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AZURE-SPECIFIC SECTION (respond method, lines 140-175):                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  # Get Azure OpenAI client                                          │   │
│  │  client = await client_manager.get_client()  # ← Azure client mgr   │   │
│  │                                                                     │   │
│  │  # Create the Azure OpenAI model wrapper                            │   │
│  │  azure_model = OpenAIChatCompletionsModel(                          │   │
│  │      model=settings.azure_openai_deployment,  # ← Deployment name   │   │
│  │      openai_client=client,                    # ← Azure client      │   │
│  │  )                                                                  │   │
│  │                                                                     │   │
│  │  # Run agent with Azure model                                       │   │
│  │  result = Runner.run_streamed(                                      │   │
│  │      agent,                                                         │   │
│  │      agent_input,                                                   │   │
│  │      context=agent_context,                                         │   │
│  │      run_config=RunConfig(model=azure_model), # ← Override model    │   │
│  │  )                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WITH OPENAI DIRECTLY: Replace with:                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  # No client manager needed, no model override                      │   │
│  │  result = Runner.run_streamed(                                      │   │
│  │      agent,                                                         │   │
│  │      agent_input,                                                   │   │
│  │      context=agent_context,                                         │   │
│  │      # Uses OPENAI_API_KEY env var automatically                    │   │
│  │  )                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  The base server pattern itself IS still useful for:                       │
│  • Agent abstraction (get_agent method)                                    │
│  • Action handling                                                         │
│  • Post-respond hooks                                                      │
│  But the Azure-specific client/model code would be removed.                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why it exists:**
- The `agents` SDK (OpenAI's Agents SDK) defaults to using `OPENAI_API_KEY`
- For Azure, we must explicitly create an `OpenAIChatCompletionsModel` with our Azure client
- `RunConfig(model=azure_model)` overrides the default model

**With OpenAI directly:** Remove `azure_client` import, remove `OpenAIChatCompletionsModel` wrapping, let the Runner use its default OpenAI client.

---

### 3. `config.py` — **CONTAINS AZURE-SPECIFIC SETTINGS**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  config.py                                            MIXED (Azure + App)  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AZURE-SPECIFIC SETTINGS:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  # Azure OpenAI Configuration                                       │   │
│  │  azure_openai_endpoint: str       # ← Azure resource URL            │   │
│  │  azure_openai_deployment: str     # ← Deployment name (not model)   │   │
│  │  azure_openai_api_version: str    # ← Azure versioning              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WITH OPENAI DIRECTLY: Replace with:                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  openai_api_key: str              # ← Just the API key              │   │
│  │  openai_model: str = "gpt-4o"     # ← Model name                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Comparison

### With Azure OpenAI (Current)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AZURE OPENAI ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐                                                      │
│  │   User Request    │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │   base_server.py  │  ← Custom abstraction layer                          │
│  │   respond()       │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐      ┌───────────────────┐                          │
│  │ azure_client.py   │ ──►  │ DefaultAzure      │  ← Azure AD auth         │
│  │ client_manager    │      │ Credential        │                          │
│  └─────────┬─────────┘      └───────────────────┘                          │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │ AsyncAzureOpenAI  │  ← Azure-specific client                             │
│  │ + token provider  │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │ OpenAIChat        │  ← Wrapper to use Azure client with Agents SDK       │
│  │ CompletionsModel  │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │   agents.Runner   │  ← OpenAI Agents SDK                                 │
│  │   run_streamed()  │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │   Azure OpenAI    │  ← your-resource.openai.azure.com                    │
│  │   (GPT-4o deploy) │                                                      │
│  └───────────────────┘                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### With OpenAI Directly (Simplified)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPENAI DIRECT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐                                                      │
│  │   User Request    │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │   use case server │  ← Could extend ChatKitServer directly               │
│  │   respond()       │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │   agents.Runner   │  ← OpenAI Agents SDK                                 │
│  │   run_streamed()  │     Uses OPENAI_API_KEY automatically                │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                │
│  ┌───────────────────┐                                                      │
│  │     OpenAI API    │  ← api.openai.com                                    │
│  │     (gpt-4o)      │                                                      │
│  └───────────────────┘                                                      │
│                                                                             │
│  NO azure_client.py, NO OpenAIChatCompletionsModel wrapper                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Necessity Matrix

| Component | With Azure OpenAI | With OpenAI Directly | Notes |
|-----------|-------------------|---------------------|-------|
| `azure_client.py` | ✅ **Required** | ❌ **Delete** | Azure AD auth, token provider |
| `base_server.py` | ✅ Required (Azure model wrapping) | ⚠️ **Simplify** | Remove Azure client/model code, keep abstraction |
| `config.py` Azure settings | ✅ Required | ❌ **Replace** | Use `OPENAI_API_KEY` instead |
| `OpenAIChatCompletionsModel` | ✅ Required | ❌ **Remove** | Only needed to inject Azure client |
| `RunConfig(model=...)` | ✅ Required | ❌ **Remove** | Agents SDK uses default OpenAI |
| `DefaultAzureCredential` | ✅ Required | ❌ **Remove** | Azure-specific auth |
| **ChatKitServer** | ✅ Required | ✅ Required | Core ChatKit functionality |
| **Agent/Tools** | ✅ Required | ✅ Required | Your business logic |
| **Widgets** | ✅ Required | ✅ Required | UI components |
| **Store** | ✅ Required | ✅ Required | Data persistence |

---

## Code Changes Summary

### To Convert from Azure OpenAI → OpenAI Direct

1. **Delete** `azure_client.py`

2. **Modify** `config.py`:
   ```python
   # Remove these:
   azure_openai_endpoint: str
   azure_openai_deployment: str
   azure_openai_api_version: str
   
   # Add:
   openai_model: str = "gpt-4o"
   # API key is read from OPENAI_API_KEY env var automatically
   ```

3. **Simplify** `base_server.py` respond method:
   ```python
   # BEFORE (Azure):
   client = await client_manager.get_client()
   azure_model = OpenAIChatCompletionsModel(
       model=settings.azure_openai_deployment,
       openai_client=client,
   )
   result = Runner.run_streamed(
       agent, agent_input, context=agent_context,
       run_config=RunConfig(model=azure_model),
   )
   
   # AFTER (OpenAI Direct):
   result = Runner.run_streamed(
       agent, agent_input, context=agent_context,
       # No run_config needed - uses OPENAI_API_KEY automatically
   )
   ```

4. **Remove** imports:
   ```python
   # Remove from base_server.py:
   from agents import OpenAIChatCompletionsModel, RunConfig
   from azure_client import client_manager
   ```

5. **Update** `.env`:
   ```env
   # Remove:
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_DEPLOYMENT=...
   AZURE_OPENAI_API_VERSION=...
   
   # Add:
   OPENAI_API_KEY=sk-...
   ```

---

## Why Use Azure OpenAI Instead of OpenAI?

| Reason | Azure OpenAI Advantage |
|--------|----------------------|
| **Enterprise compliance** | Data stays in your Azure region |
| **Managed Identity** | No API keys to manage/rotate |
| **Private endpoints** | Keep traffic on Azure backbone |
| **Azure integration** | RBAC, logging, monitoring built-in |
| **Cost management** | Azure billing, reservations, budgets |
| **SLA guarantees** | Enterprise SLA from Microsoft |

---

## Dependencies

### Azure-Specific Python Packages

```
# These are only needed for Azure OpenAI:
azure-identity>=1.19.0     # DefaultAzureCredential
```

### Shared Packages

```
# These are needed regardless of OpenAI vs Azure:
openai>=1.93.0             # OpenAI SDK (includes AsyncAzureOpenAI)
openai-agents>=0.1.0       # Agents SDK (Runner, Agent, etc.)
openai-chatkit>=0.1.0      # ChatKit server/widgets
fastapi
uvicorn
```

---

## Summary

This project adds **three main components** to support Azure OpenAI:

1. **`azure_client.py`** - Manages Azure AD authentication and `AsyncAzureOpenAI` client
2. **Azure-specific code in `base_server.py`** - Wraps the client in `OpenAIChatCompletionsModel` and passes to `RunConfig`
3. **Azure settings in `config.py`** - Endpoint, deployment name, API version

**With OpenAI directly**, you would:
- Delete `azure_client.py`
- Simplify `base_server.py` (remove ~15 lines of Azure wrapping)
- Use `OPENAI_API_KEY` environment variable (Agents SDK reads it automatically)
- Remove `azure-identity` from dependencies

The **ChatKitServer**, **Widgets**, **Store**, and **Agent/Tools** are all framework components that remain the same regardless of which OpenAI service you use.

---

*Document created: January 18, 2026*
