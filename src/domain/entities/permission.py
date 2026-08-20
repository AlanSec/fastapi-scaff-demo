from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class Resource(str, Enum):
    USER = "user"
    TENANT = "tenant"
    ROLE = "role"
    PERMISSION = "permission"


@dataclass(frozen=True, eq=True)
class Permission:
    id: UUID
    action: PermissionAction
    resource: Resource
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, action: PermissionAction, resource: Resource, description: str) -> "Permission":
        now = datetime.now()
        return cls(
            id=uuid4(),
            action=action,
            resource=resource,
            description=description,
            is_active=True,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def create_crud(cls, resource: Resource, action: PermissionAction) -> "Permission":
        action_verb = action.value
        resource_name = resource.value
        description = f"{action_verb.capitalize()} {resource_name} permission"
        return cls.create(action, resource, description)

    def deactivate(self) -> "Permission":
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now()
        )

    def activate(self) -> "Permission":
        return replace(
            self,
            is_active=True,
            updated_at=datetime.now()
        )
