import logging

from src.bootstrap.config import settings as new_settings
from src.bootstrap.container import get_container
from src.domain.entities.tenant import Tenant as NewTenant
from src.domain.entities.user import User as NewUser
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password

logger = logging.getLogger(__name__)


async def ensure_admin_user():
    """Create default admin user and tenant using new domain entities.

    Uses the configured Container repositories (currently InMemory).
    """
    container = get_container()

    tenant_repo = container.tenant_repository
    user_repo = container.user_repository
    hasher = container.password_hasher

    # Ensure default tenant exists
    tenant = await tenant_repo.find_by_name("Default Tenant")
    if tenant is None:
        tenant = NewTenant.create(name="Default Tenant", domain="default.example.com")
        await tenant_repo.save(tenant)

    # Check if admin user already exists
    existing = await user_repo.find_by_email(new_settings.admin_email, tenant.id)
    if existing:
        logger.info("Admin user already exists: %s", new_settings.admin_email)
        return

    # Create admin user with new domain entities
    new_user = NewUser.create(
        email=Email(new_settings.admin_email),
        password=hasher.hash(Password(new_settings.admin_password)),
        tenant_id=tenant.id,
        is_superuser=True,
    )
    await user_repo.save(new_user)
    logger.info("Admin user created: %s", new_settings.admin_email)
