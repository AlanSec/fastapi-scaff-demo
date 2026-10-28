import logging

from src.bootstrap.config import settings
from src.bootstrap.container import get_container
from src.domain.entities.tenant import Tenant
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password

logger = logging.getLogger(__name__)


async def ensure_admin_user():
    """创建默认租户与 admin 超级用户（幂等，启动时执行）。

    使用 DI 容器中的仓储（SQLModel 持久化实现）。
    """
    container = get_container()

    tenant_repo = container.tenant_repository
    user_repo = container.user_repository
    hasher = container.password_hasher

    # Ensure default tenant exists
    tenant = await tenant_repo.find_by_name("Default Tenant")
    if tenant is None:
        tenant = Tenant.create(name="Default Tenant", domain="default.example.com")
        await tenant_repo.save(tenant)

    # Check if admin user already exists
    existing = await user_repo.find_by_email(settings.admin_email, tenant.id)
    if existing:
        logger.info("Admin user already exists: %s", settings.admin_email)
        return

    # Create admin user with domain entities
    new_user = User.create(
        email=Email(settings.admin_email),
        password=hasher.hash(Password(settings.admin_password)),
        tenant_id=tenant.id,
        is_superuser=True,
    )
    await user_repo.save(new_user)
    logger.info("Admin user created: %s", settings.admin_email)
