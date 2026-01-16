# negociApp - Backend

Backend Serverless construido con **FastAPI** (Python) y **Supabase** (PostgreSQL).

## 🚀 Requisitos Previos
- Python 3.11+
- Cuenta en [Supabase](https://supabase.com/)
- Cuenta en [Vercel](https://vercel.com/) (para despliegue)

## 🛠️ Instalación y Configuración

### 1. Clonar y Preparar Entorno
El proyecto incluye un script de automatización para Windows:
```powershell
# Simplemente ejecutá:
./run_dev.bat
```
*Esto creará el entorno virtual (`.venv`), instalará las dependencias y levantará el servidor.*

**Opción Manual:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variables de Entorno
Copiá el archivo de ejemplo y completalo con tus credenciales de Supabase:
```bash
cp .env.example .env
```
*Asegurate de definir `DATABASE_URL` (formato `postgresql+asyncpg://...`) y las keys de Supabase.*

## ▶️ Ejecución
Para desarrollo local con hot-reload:
```bash
uvicorn app.main:app --reload
```
O usando el script: `run_dev`

La API estará disponible en: `http://localhost:8000`
Docs interactivos: `http://localhost:8000/docs`

## 🗄️ Migraciones
Para realizar las migraciones vamos a generar las migraciones con el siguiente comando:
* `alembic revision --autogenerate -m "nombre_de_migracion"` (entre comillas va el nombre)
* `alembic upgrade head` (para aplicar las migraciones en Supabase)

## 🔄 Versionado (Workflow)

### 1. Nueva Rama
`git checkout develop` -> `git pull origin develop` -> `git checkout -b GES-XX`

### 2. Ciclo de Desarrollo
`git status` -> `git add .` -> `git commit -m "GES-XX: descripción corta del cambio"`

### 3. Subida a GitHub
`git push origin GES-XX`

### 4. Integración (En la web de GitHub)
Entrar al repo y hacer clic en "Compare & pull request" asegurando como destino base: **develop**.
Merge pull request & Delete branch.

### 5. Limpieza y Sincronización Local
`git checkout develop` -> `git pull origin develop` -> `git branch -d GES-XX` -> `git fetch --prune`

## 🧪 Testing
Para correr los tests (asegurarse de tener `pytest` instalado):
```bash
pytest
```

## 📂 Estructura
- `app/`
    - `main.py`: Punto de entrada.
    - `models/`: Modelos SQLAlchemy.
    - `schemas/`: Esquemas Pydantic.
    - `endpoints/`: Rutas de la API.
    - `core/`: Configuración y DB.
- `alembic/`: Versiones de migraciones.
