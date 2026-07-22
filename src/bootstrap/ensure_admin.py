"""Admin user initialization module.

Uses new domain entities internally, still depends on legacy DB session
for persistence until new UserRepository supports Database-backed storage.
"""
import logging
from pathlib import Path

from sqlalchemy import select

from src.bootstrap.config import settings as new_settings
from src.domain.entities.tenant import Tenant as NewTenant
from src.domain.entities.user import User as NewUser
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher

logger = logging.getLogger(__name__)


async def ensure_admin_user():
    """Create default admin user and tenant using new domain entities.

    Still writes to the legacy database via app.db.session because the new
    InMemoryUserRepository does not persist across restarts.
    Will be fully migrated when a Database-backed UserRepository replaces it.
    """
    from app.db.session import get_session
    from app.models.tenant import Tenant as LegacyTenant
    from app.models.user import User as LegacyUser

    async for session in get_session():
        admin_email = new_settings.admin_email

        # Check if admin already exists
        result = await session.execute(
            select(LegacyUser).where(LegacyUser.email == admin_email)
        )
        if result.scalar_one_or_none():
            logger.info("Admin user already exists: %s", admin_email)
            return

        # Ensure default tenant exists
        result = await session.execute(
            select(LegacyTenant).where(LegacyTenant.name == "Default Tenant")
        )
        legacy_tenant = result.scalar_one_or_none()

        if not legacy_tenant:
            new_tenant = NewTenant.create(
                name="Default Tenant",
                domain="default.example.com",
            )
            legacy_tenant = LegacyTenant(
                id=new_tenant.id,
                name=new_tenant.name,
                domain=new_tenant.domain,
                is_active=new_tenant.is_active,
                created_at=new_tenant.created_at,
                updated_at=new_tenant.updated_at,
                description="System default tenant",
            )
            session.add(legacy_tenant)
            await session.commit()
            await session.refresh(legacy_tenant)

        # Create admin user using new domain entities, map to legacy model
        hasher = BcryptPasswordHasher()
        new_user = NewUser.create(
            email=Email(admin_email),
            password=hasher.hash(Password(new_settings.admin_password)),
            tenant_id=legacy_tenant.id,
        )
        legacy_user = LegacyUser(
            id=new_user.id,
            email=str(new_user.email),
            username=new_settings.admin_username,
            hashed_password=new_user.password.value,
            is_active=new_user.is_active,
            is_superuser=new_settings.admin_is_superuser,
            email_verified=True,
            tenant_id=new_user.tenant_id,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )
        session.add(legacy_user)
        await session.commit()
        logger.info("Admin user created: %s", admin_email)
