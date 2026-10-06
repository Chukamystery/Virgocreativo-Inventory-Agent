from fastapi import FastAPI

from app import models
from app.config import settings
from app.database import Base, engine
from app.routers import (
    agent,
    alerts,
    audit,
    auth_routes,
    handoffs,
    inventory,
    lookups,
    procurement,
    products,
    reorder,
    stock_movements,
    suppliers,
)

from app.logging_config import (
    configure_logging,
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description=(
        "Backend API for the "
        "Inventory Agent learning project."
    ),
)


app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(stock_movements.router)
app.include_router(audit.router)
app.include_router(reorder.router)
app.include_router(agent.router)
app.include_router(procurement.router)
app.include_router(suppliers.router)
app.include_router(alerts.router)
app.include_router(handoffs.router)
app.include_router(lookups.router)
app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {
        "message": "Inventory Agent API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }