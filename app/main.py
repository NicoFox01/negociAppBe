from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Cross-Origin Resource Sharing)
# Permite que el Frontend hable con el Backend.
#
# Backend desplegado en:
#   - https://negociapp-be.vercel.app
#   - https://negociapp-be-git-main-nicofox01s-projects.vercel.app
#   - https://negociapp-1ysx4re7p-nicofox01s-projects.vercel.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Producción
        "https://negociapp-fe.vercel.app",
        "https://negociapp-fe-git-main-nicofox01s-projects.vercel.app",
        "https://negociapp-jbowgz4g5-nicofox01s-projects.vercel.app",
        "https://negociapp.online",
        "https://www.negociapp.online",
        # Desarrollo local
        "http://localhost:5173",
        "http://localhost:5500",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos todas las rutas bajo /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to NegociApp API"}
