import asyncio
import logging
from app.core.database import AsyncSessionLocal
from app.models.user import Users
from app.models.tenant import Tenants
from app.models.enums import Roles, PlanType
from app.core.security import get_password_hash
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_admin_user():
    async with AsyncSessionLocal() as db:
        try:
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

            target_username = "nicovid"
            
            result_user = await db.execute(select(Users).where(Users.username == target_username))
            existing_user = result_user.scalars().first()

            if existing_user:
                logger.warning(f"⚠️ El usuario {target_username} ya existe.")
                return

            new_admin = Users(
                username=target_username,
                hashed_password=get_password_hash("admin123"),
                full_name="Nico Admin",
                role=Roles.ADMIN,
                tenant_id=system_tenant.id,
                is_active=True
            )

            db.add(new_admin)
            await db.commit()
            logger.info(f"✅ Usuario Admin creado exitosamente: {target_username}")
            logger.info(f"🔑 Password: admin123")
            logger.info(f"👑 Rol: {Roles.ADMIN}")

        except Exception as e:
            import traceback
            logger.error(f"❌ Error creando usuario: {e}")
            logger.error(traceback.format_exc())
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_admin_user())
