from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Cross-Origin Resource Sharing)
# Permite que el Frontend (puerto 5500/3000/etc) hable con el Backend (8000)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://negociapp-fe-git-main-nicofox01s-projects.vercel.app",
        "https://negociapp-fe-nicofox01s-projects.vercel.app",
    ], # En producción, cambia esto por la URL real de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos todas las rutas bajo /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to NegociApp API"}
