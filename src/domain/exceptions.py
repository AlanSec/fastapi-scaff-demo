"""领域异常体系——业务失败统一通过异常表达，由 API 层全局映射为 4xx。

约定：
- `DomainError` 继承 `ValueError`：现有调用方（路由 try/except、测试断言）保持兼容
- 精确子类映射：NotFound → 404，Conflict → 409，InvalidCredentials → 401，其余 → 400
- UseCase 不得直接抛裸 `ValueError` 表达业务失败（输入校验类错误除外，由兜底映射 400）
"""


class DomainError(ValueError):
    """领域异常基类（API 层映射为 4xx）"""


class EntityNotFoundError(DomainError):
    """资源不存在（→ 404，与跨租户防枚举的 404 语义一致）"""


class ConflictError(DomainError):
    """资源冲突：重复创建/唯一性约束（→ 409）"""


class InvalidCredentialsError(DomainError):
    """凭证无效：密码错误、token 无效/过期（→ 401）"""


class InvalidInputError(DomainError):
    """业务输入无效：租户不存在、角色名非法等（→ 400）"""
