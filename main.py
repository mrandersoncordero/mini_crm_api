from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import engine
from app.utils.base_model import Base
from app.routers import auth, users, clients, leads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    async with engine.begin() as conn:
        # Create tables if they don't exist
        # await conn.run_sync(Base.metadata.create_all)
        pass
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Mini CRM API",
    description="API for managing leads and clients",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(leads.router)


@app.get("/")
async def root():
    return {"message": "Welcome to Mini CRM API", "docs": "/docs", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
