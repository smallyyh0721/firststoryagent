"""
Story Agent - FastAPI Application
AI-powered Story Writer with Notion Integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import stories_router
from contextlib import asynccontextmanager

# Global clients
llm_client = None
notion_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    from backend.core.llm import LLMClient
    from backend.core.notion import NotionClient
    
    global llm_client, notion_client
    
    print("Starting Story Agent...")
    
    # Initialize clients
    llm_client = LLMClient()
    notion_client = NotionClient()
    
    print("[OK] Clients initialized")
    
    yield
    
    # Shutdown
    print("Shutting down Story Agent...")
    if llm_client:
        llm_client.close()
    print("[OK] Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="Story Agent API",
    description="AI-powered Story Writer with Notion Integration",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stories_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Story Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "story-agent"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )