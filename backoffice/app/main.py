from fastapi import FastAPI

from .routes import stock, users


# Central FastAPI application for the HBntory Backoffice.
app = FastAPI(title="HBntory Backoffice")

# Make the stock and user routes available under /api.
app.include_router(stock.router, prefix="/api")
app.include_router(users.router, prefix="/api")