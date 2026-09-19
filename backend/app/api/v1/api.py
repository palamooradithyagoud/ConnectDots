from fastapi import APIRouter
from app.api.v1.endpoints import crimes, nlp, search, ml, graph, investigation, telecom, network, reviews, agent

api_router = APIRouter()
api_router.include_router(crimes.router)
api_router.include_router(nlp.router, prefix="/nlp", tags=["NLP & Crime Understanding"])
api_router.include_router(search.router, prefix="/search", tags=["Semantic Crime Search"])
api_router.include_router(ml.router, prefix="/ml", tags=["ML & Pattern Analysis"])
api_router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph (Neo4j)"])
api_router.include_router(investigation.router, prefix="/investigation", tags=["Investigation Intelligence (Graph RAG)"])
api_router.include_router(telecom.router, prefix="/telecom", tags=["Telecommunications & CDR Intelligence"])
api_router.include_router(network.router, prefix="/network", tags=["Person Network & Key Individual Intelligence"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Human Validation Reviews"])
api_router.include_router(agent.router, prefix="/agent", tags=["Domain AI Investigation Agent"])

