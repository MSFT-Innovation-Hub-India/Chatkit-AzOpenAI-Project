"""
FastAPI Application for ChatKit Todo Sample.
Exposes the ChatKit endpoint and serves the frontend.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chatkit.server import StreamingResult

from config import settings
from store import SQLiteStore

# Import the use-case specific ChatKit server
# Each use case provides its own server - swap this import for a different use case
from use_cases.todo import TodoChatKitServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
data_store: Optional[SQLiteStore] = None
server: Optional[TodoChatKitServer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    global data_store, server
    
    logger.info("Starting ChatKit Todo Application...")
    
    # Initialize data store
    data_store = SQLiteStore(settings.data_store_path)
    logger.info(f"SQLite store initialized at: {settings.data_store_path}")
    
    # Initialize ChatKit server
    server = TodoChatKitServer(data_store)
    logger.info("ChatKit server initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    if data_store:
        await data_store.close()


# Create FastAPI app
app = FastAPI(
    title="ChatKit Todo Sample",
    description="A self-hosted ChatKit todo list application with Azure OpenAI",
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
        # Pass empty context - can be extended for auth/user info
        result = await server.process(body, {})
        
        if isinstance(result, StreamingResult):
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
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
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "azure_openai_configured": bool(settings.azure_openai_endpoint)
    }


@app.get("/api/branding")
async def get_branding():
    """Return branding configuration for the frontend."""
    return {
        "name": settings.brand_name,
        "tagline": settings.brand_tagline,
        "logoUrl": settings.brand_logo_url,
        "primaryColor": settings.brand_primary_color,
        "faviconUrl": settings.brand_favicon_url,
    }


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the ChatKit frontend."""
    return FileResponse("static/index.html")


# Serve static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found, skipping mount")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
