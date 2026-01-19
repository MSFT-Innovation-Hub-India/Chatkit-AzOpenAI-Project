"""
FastAPI Application for ChatKit Retail Returns Sample.

Exposes the ChatKit endpoint for retail order returns and serves the frontend.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from chatkit.server import StreamingResult

from config import settings

# Import the retail use case ChatKit server and Cosmos DB store
from use_cases.retail import RetailChatKitServer
from use_cases.retail.cosmos_store import CosmosDBStore

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
data_store: Optional[CosmosDBStore] = None
server: Optional[RetailChatKitServer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    global data_store, server
    
    logger.info("Starting ChatKit Retail Returns Application...")
    
    # Initialize Cosmos DB store for thread persistence
    # Uses the same Cosmos DB account as retail data
    data_store = CosmosDBStore(
        endpoint="https://common-nosql-db.documents.azure.com:443/",
        database_name="db001",
        threads_container="ChatKit_Threads",
        items_container="ChatKit_Items",
    )
    logger.info("Cosmos DB store initialized for thread persistence")
    
    # Initialize ChatKit server with Cosmos DB store
    server = RetailChatKitServer(data_store)
    logger.info("Retail ChatKit server initialized")
    logger.info("All data (threads, items, retail) stored in Azure Cosmos DB")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    if data_store:
        await data_store.close()


# Create FastAPI app
app = FastAPI(
    title="ChatKit Retail Returns",
    description="A self-hosted ChatKit application for retail order returns with Azure OpenAI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """
    Main ChatKit endpoint.
    Receives ChatKit protocol requests and returns streaming responses.
    """
    if server is None:
        return Response(content='{"error": "Server not initialized"}', status_code=500)
    
    try:
        body = await request.body()
        
        # Process the request through ChatKit server
        result = await server.process(body, {})
        
        if isinstance(result, StreamingResult):
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        return Response(content=result.json, media_type="application/json")
    
    except Exception as e:
        logger.error(f"Error processing ChatKit request: {e}", exc_info=True)
        return Response(
            content=f'{{"error": "{str(e)}"}}',
            status_code=500,
            media_type="application/json"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "use_case": "retail_returns",
        "azure_openai_configured": bool(settings.azure_openai_endpoint),
        "cosmos_db": "common-nosql-db.documents.azure.com",
    }


@app.get("/api/branding")
async def get_branding():
    """Return branding configuration for the frontend."""
    return {
        "name": "Returns Assistant",
        "tagline": "Quick and easy order returns",
        "logoUrl": "/static/logo.svg",
        "primaryColor": "#2563eb",
        "faviconUrl": "/static/favicon.ico",
        "prompts": [
            {"label": "📦 Start a return", "prompt": "Hi, I need to return an item"},
            {"label": "👤 I'm Jane Smith", "prompt": "My email is jane.smith@email.com"},
            {"label": "📋 Check my orders", "prompt": "What orders do I have that I can return?"},
            {"label": "❓ Return policy", "prompt": "What is your return policy?"},
        ],
        "howToUse": [
            "💬 Tell me you'd like to return an item",
            "👤 Identify yourself by name or email",
            "📦 Select the item you want to return",
            "📝 Choose your reason and resolution",
            "✅ Confirm and get your return label",
        ],
        "features": [
            "🔍 Look up orders from Azure Cosmos DB",
            "📦 Interactive item selection widgets",
            "💳 Multiple resolution options (refund, exchange, credit)",
            "🏷️ Automatic return label generation",
            "⭐ Loyalty tier benefits (Gold/Platinum get free returns)",
            "☁️ Azure OpenAI powered",
        ],
    }


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serve the ChatKit frontend.
    """
    from pathlib import Path
    
    # Check for React build first
    react_build = Path("static/dist/index.html")
    if react_build.exists():
        return FileResponse(str(react_build))
    
    # Fallback to vanilla JS
    return FileResponse("static/index.html")


# Serve static files
try:
    from pathlib import Path
    react_dist = Path("static/dist")
    if react_dist.exists():
        app.mount("/assets", StaticFiles(directory="static/dist/assets"), name="assets")
        logger.info("Serving React build from static/dist")
except (RuntimeError, FileNotFoundError):
    pass

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found")


if __name__ == "__main__":
    import uvicorn
    # Run on port 8001 to avoid conflict with main Todo app on 8000
    uvicorn.run(
        "main_retail:app",
        host=settings.app_host,
        port=8001,
        reload=False,
        log_level=settings.log_level.lower()
    )
