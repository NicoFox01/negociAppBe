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
---
## Roles del Sistema
| Rol | Descripción |
|-----|-------------|
| `ADMIN` | Administrador del sistema |
| `COMPANY` | Dueño de empresa/tenant |
| `EMPLOYEE` | Empleado de la empresa |
---
## Endpoints
### Auth (`/auth`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/auth/register` | Registrar empresa + usuario admin | Público |
| POST | `/auth/login` | Iniciar sesión | Público |
| POST | `/auth/change-password` | Cambiar contraseña | COMPANY, EMPLOYEE |
| POST | `/auth/recover-password` | Recuperar contraseña | Público |
| PATCH | `/auth/reset-password/{user_id}` | Resetear contraseña | COMPANY |
---
### Users (`/users`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/users/` | Listar usuarios del tenant | COMPANY |
| GET | `/users/mi-usuario` | Ver mi usuario | COMPANY, EMPLOYEE |
| GET | `/users/{user_id}` | Ver usuario por ID | COMPANY |
| GET | `/users/tenant/{tenant_id}` | Listar usuarios de empresa | COMPANY |
| POST | `/users/` | Crear usuario | COMPANY |
| DELETE | `/users/{user_id}` | Eliminar usuario | COMPANY |
| PATCH | `/users/activar/{user_id}` | Activar usuario | COMPANY |
| PATCH | `/users/desactivar/{user_id}` | Desactivar usuario | COMPANY |
| PATCH | `/users/{user_id}/password` | Cambiar contraseña de usuario | COMPANY |
---
### Tenants (`/tenants`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/tenants/` | Listar empresas | ADMIN |
| GET | `/tenants/{tenant_id}` | Ver empresa por ID | ADMIN |
| GET | `/tenants/mi-empresa` | Ver mi empresa | COMPANY |
| POST | `/tenants/` | Crear empresa | ADMIN |
| DELETE | `/tenants/{tenant_id}` | Eliminar empresa | ADMIN |
| PATCH | `/tenants/activar/{tenant_id}` | Activar empresa | ADMIN |
| PATCH | `/tenants/desactivar/{tenant_id}` | Desactivar empresa | ADMIN |
---
### Products (`/products`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/products/` | Listar productos (paginado) | COMPANY, EMPLOYEE |
| GET | `/products/{product_id}` | Ver producto | COMPANY, EMPLOYEE |
| GET | `/products/supplier/{supplier_id}` | Productos por proveedor | COMPANY |
| POST | `/products/` | Crear producto | COMPANY |
| PATCH | `/products/{product_id}` | Actualizar producto | COMPANY |
| DELETE | `/products/{product_id}` | Eliminar producto | COMPANY |
| DELETE | `/products/{supplier_id}` | Eliminar productos de proveedor | COMPANY |
---
### Suppliers (`/suppliers`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/suppliers/` | Listar proveedores | COMPANY |
| GET | `/suppliers/{supplier_id}` | Ver proveedor | COMPANY |
| POST | `/suppliers/` | Crear proveedor | COMPANY |
| PATCH | `/suppliers/{supplier_id}` | Actualizar proveedor | COMPANY |
| DELETE | `/suppliers/{supplier_id}` | Eliminar proveedor | COMPANY |
---
### Inventory (`/inventory`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/inventory/transaction` | Registrar transacción de inventario | COMPANY, EMPLOYEE |
| GET | `/inventory/history/{product_id}` | Historial de inventario de producto | COMPANY, EMPLOYEE |
| POST | `/inventory/adjust` | Ajuste manual de stock | COMPANY |
---
### Production (`/production`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/production/transform` | Crear transformación de producción | COMPANY, EMPLOYEE |
| GET | `/production/transforms` | Listar transformaciones (paginado) | COMPANY, EMPLOYEE |
| GET | `/production/transforms/{transform_id}` | Ver transformación por ID | COMPANY, EMPLOYEE |
---
### Sales (`/sales`)
#### Canales de Venta
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/sales/channels` | Crear canal de venta | COMPANY |
| GET | `/sales/channels` | Listar canales | COMPANY |
| GET | `/sales/channels/{channel_id}` | Ver canal | COMPANY |
| PATCH | `/sales/channels/{channel_id}` | Actualizar canal | COMPANY |
| DELETE | `/sales/channels/{channel_id}` | Eliminar canal | COMPANY |
#### Precios por Canal
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/sales/channels/{channel_id}/prices/{product_id}` | Establecer precio | COMPANY |
| GET | `/sales/channels/{channel_id}/prices` | Listar precios | COMPANY |
| GET | `/sales/channels/{channel_id}/prices/{product_id}` | Ver precio | COMPANY |
| DELETE | `/sales/channels/{channel_id}/prices/{product_id}` | Eliminar precio | COMPANY |
#### Promociones
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/sales/channels/{channel_id}/promotions` | Crear promoción | COMPANY |
| GET | `/sales/channels/{channel_id}/promotions` | Listar promociones | COMPANY |
| GET | `/sales/channels/{channel_id}/promotions/active` | Promociones activas | COMPANY |
| GET | `/sales/channels/{channel_id}/promotions/{promotion_id}` | Ver promoción | COMPANY |
| PATCH | `/sales/channels/{channel_id}/promotions/{promotion_id}` | Actualizar promoción | COMPANY |
| DELETE | `/sales/channels/{channel_id}/promotions/{promotion_id}` | Eliminar promoción | COMPANY |
#### Pedidos de Clientes
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/sales/clientOrder` | Crear pedido | COMPANY, EMPLOYEE |
| GET | `/sales/clientOrder` | Listar pedidos | COMPANY, EMPLOYEE |
| GET | `/sales/clientOrder/{order_id}` | Ver pedido | COMPANY, EMPLOYEE |
| PATCH | `/sales/clientOrder/{order_id}` | Modificar pedido | COMPANY, EMPLOYEE |
| DELETE | `/sales/clientOrder/{order_id}` | Cancelar pedido | COMPANY, EMPLOYEE |
---
### Orders (`/orders`) - Órdenes de Compra
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/orders/` | Crear orden de compra | COMPANY |
| POST | `/orders/generate` | Generar órdenes desde solicitudes | COMPANY |
| GET | `/orders/` | Listar órdenes | COMPANY |
| GET | `/orders/{order_id}` | Ver orden | COMPANY |
| PATCH | `/orders/{order_id}/receive` | Recepciones | COMPANY |
| PATCH | `/orders/{order_id}` | Actualizar orden | COMPANY |
| DELETE | `/orders/{order_id}` | Cancelar orden | COMPANY |
---
### Request (`/request`) - Solicitudes de Compra
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/request/` | Listar solicitudes | COMPANY, EMPLOYEE |
| GET | `/request/{request_id}` | Ver solicitud | COMPANY, EMPLOYEE |
| POST | `/request/` | Crear solicitud | COMPANY, EMPLOYEE |
| PATCH | `/request/{request_id}/{status}` | Aprobar/rechazar | COMPANY |
| DELETE | `/request/{request_id}` | Eliminar solicitud | COMPANY |
---
### Payments (`/payments`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| POST | `/payments/` | Crear pago | COMPANY |
| POST | `/payments/notify` | Notificar pago | Público |
| GET | `/payments/mis-pagos` | Mis pagos | COMPANY |
| GET | `/payments/pagos` | Todos los pagos | ADMIN |
| PATCH | `/payments/{payment_id}` | Aprobar/rechazar pago | ADMIN |
| PATCH | `/payments/cancelar/{payment_id}` | Cancelar pago | COMPANY |
---
### Notifications (`/notifications`)
| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/notifications/` | Listar notificaciones | COMPANY, EMPLOYEE |
| POST | `/notifications/{username_request}` | Crear notificación | COMPANY, EMPLOYEE |
| PATCH | `/notifications/{notification_id}` | Actualizar notificación | COMPANY, EMPLOYEE |
---
## Estados Enum
### PlanType
- `FREE_FOREVER` - Gratuito forever
- `FREE_TRIAL_1_MONTH` - Trial 1 mes
- `PAID_MONTHLY` - Pago mensual
- `PAID_YEARLY` - Pago anual
### PaymentStatus
- `PENDING` - Pendiente
- `APPROVED` - Aprobado
- `REJECTED` - Rechazado
- `CANCELED` - Cancelado
### OrderStatus (Pedidos de clientes)
- `PENDING` - Pendiente
- `CONFIRMED` - Confirmado
- `PREPARING` - Preparando
- `READY` - Listo
- `COMPLETED` - Completado
- `CANCELLED` - Cancelado
### PurchaseOrderStatus (Órdenes de compra)
- `DRAFT` - Borrador
- `SENT` - Enviado
- `RECEIVED` - Recibido
- `PARTIALLY_RECEIVED` - Parcialmente recibido
- `CANCELLED` - Cancelado
### TransactionType (Inventario)
- `IN` - Entrada
- `OUT` - Salida
- `ADJUSTMENT` - Ajuste