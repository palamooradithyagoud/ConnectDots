from fastapi import APIRouter
from app.api.v1.endpoints import crimes, nlp, search

api_router = APIRouter()
api_router.include_router(crimes.router)
api_router.include_router(nlp.router, prefix="/nlp", tags=["NLP & Crime Understanding"])
api_router.include_router(search.router, prefix="/search", tags=["Semantic Crime Search"])
