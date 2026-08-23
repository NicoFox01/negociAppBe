import asyncio
import argparse
import logging
from app.core.database import AsyncSessionLocal
from app.models.user import Users
from app.models.tenant import Tenants
from app.models.notifications import Notification
from app.models.payments import Payments
from app.models.enums import Roles, PlanType
from app.core.security import get_password_hash
from sqlalchemy import select

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_superuser(username: str, password: str, full_name: str):
    async with AsyncSessionLocal() as db:
        try:
            # 1. Verificar/Crear Tenant "Plataforma" (Requerido por FK en Users)
            # Como la DB exige un tenant_id, crearemos un Tenant "Fantasma" para el Admin
            logger.info("Verificando Tenant de Sistema...")
            result = await db.execute(select(Tenants).where(Tenants.name == "NegociApp Admin Platform"))
            system_tenant = result.scalars().first()

            if not system_tenant:
                system_tenant = Tenants(
                    name="NegociApp Admin Platform",
                    contact_name="System Administrator",
                    contact_email="admin@negociapp.com",
                    plan_type=PlanType.FREE_FOREVER,
                    is_active=True
                )
                db.add(system_tenant)
                await db.commit()
                await db.refresh(system_tenant)
                logger.info(f"✅ Tenant de Sistema creado con ID: {system_tenant.id}")
            else:
                logger.info(f"ℹ️ Tenant de Sistema ya existe: {system_tenant.id}")

            # 2. Verificar/Crear Usuario Admin
            target_username = username

            result_user = await db.execute(select(Users).where(Users.username == target_username))
            existing_user = result_user.scalars().first()

            if existing_user:
                logger.warning(f"⚠️ El usuario {target_username} ya existe.")
                return

            new_superuser = Users(
                username=target_username,
                hashed_password=get_password_hash(password),  # Hash seguro (nunca se loguea)
                full_name=full_name,
                role=Roles.ADMIN,
                tenant_id=system_tenant.id, # Vinculado al Tenant de Sistema
                is_active=True
            )

            db.add(new_superuser)
            await db.commit()
            logger.info(f"✅ Usuario Admin creado exitosamente: {target_username}")
            logger.info(f"👑 Rol: {Roles.ADMIN}")

        except Exception as e:
            import traceback
            logger.error(f"❌ Error creando superusuario: {e}")
            logger.error(traceback.format_exc())
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crea un usuario con rol ADMIN")
    parser.add_argument("--username", required=True, help="Nombre de usuario")
    parser.add_argument("--password", required=True, help="Contraseña en texto plano")
    parser.add_argument("--full-name", dest="full_name", help="Nombre completo (opcional)")
    args = parser.parse_args()

    full_name = args.full_name or args.username.replace("_", " ").title()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        create_superuser(args.username, args.password, full_name)
    )
