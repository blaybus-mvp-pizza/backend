from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import Base, engine
from app.core.errors import (
    business_error_handler,
    internal_error_handler,
    BusinessError,
)

# Import entities to register with Base before create_all
from app.schemas.products import Product, ProductImage, ProductTag, Tag  # noqa: F401
from app.schemas.stores import PopupStore  # noqa: F401
from app.schemas.auctions import (
    Auction,
    Bid,
    AuctionOffer,
    AuctionDeposit,
)  # noqa: F401

# Create tables on startup (MVP convenience; migrate later with Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(Exception, internal_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict:
    return {"message": "Welcome to MVP API"}
