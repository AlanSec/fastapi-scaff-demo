from enum import Enum


class Status(Enum):
    """业务状态码枚举

    错误码分段设计：
    - 0: 成功
    - 1: 通用失败
    - 4xx: HTTP 客户端错误
    - 5xx: HTTP 服务端错误
    - 1xxxx: 业务通用错误
    - 2xxxx: 文件相关错误
    - 3xxxx: JWT/认证相关错误
    - 4xxxx: 数据库相关错误
    - 5xxxx: 租户相关错误
    - 6xxxx: 任务相关错误
    """

    # ==================== 成功 ====================
    SUCCESS = (0, '操作成功')
    FAILURE = (1, '操作失败')

    # ==================== HTTP 错误 ====================
    BAD_REQUEST = (400, '请求参数错误')
    UNAUTHORIZED = (401, '未认证')
    FORBIDDEN = (403, '权限不足')
    NOT_FOUND = (404, '资源不存在')
    METHOD_NOT_ALLOWED = (405, '请求方法不允许')
    CONFLICT = (409, '资源冲突')
    GONE = (410, '资源已失效')
    UNPROCESSABLE_ENTITY = (422, '请求无法处理')
    TOO_MANY_REQUESTS = (429, '请求过于频繁')
    INTERNAL_SERVER_ERROR = (500, '服务器内部错误')
    SERVICE_UNAVAILABLE = (503, '服务不可用')

    # ==================== 参数验证 ====================
    PARAMS_ERROR = (10001, '参数错误')
    PARAMS_MISSING = (10002, '缺少必要参数')
    PARAMS_TYPE_ERROR = (10003, '参数类型错误')

    # ==================== 通用业务错误 ====================
    RECORD_NOT_EXIST_ERROR = (10100, '记录不存在')
    RECORD_EXISTS_ERROR = (10101, '记录已存在')
    CREATE_ERROR = (10102, '创建失败')
    UPDATE_ERROR = (10103, '更新失败')
    DELETE_ERROR = (10104, '删除失败')

    # ==================== 文件相关 ====================
    UPLOAD_FILE_ERROR = (20000, '上传文件失败')
    DOWNLOAD_FILE_ERROR = (20001, '下载文件失败')
    LIST_FILE_ERROR = (20002, '获取文件列表失败')
    DELETE_FILE_ERROR = (20003, '删除文件失败')
    FILE_NOT_FOUND = (20004, '文件不存在')
    FILE_SIZE_EXCEEDED = (20005, '文件大小超出限制')
    FILE_TYPE_NOT_ALLOWED = (20006, '文件类型不允许')

    # ==================== JWT / 认证相关 ====================
    TOKEN_INVALID = (30001, '令牌无效')
    TOKEN_EXPIRED = (30002, '令牌已过期')
    TOKEN_MISSING = (30003, '缺少认证令牌')
    TOKEN_REVOKED = (30004, '令牌已被撤销')
    REFRESH_TOKEN_INVALID = (30005, '刷新令牌无效')
    REFRESH_TOKEN_EXPIRED = (30006, '刷新令牌已过期')
    LOGIN_FAILED = (30007, '用户名或密码错误')
    ACCOUNT_LOCKED = (30008, '账户已被锁定')
    ACCOUNT_DISABLED = (30009, '账户已被禁用')
    PASSWORD_ERROR = (30010, '密码错误')
    EMAIL_NOT_VERIFIED = (30011, '邮箱未验证')

    # ==================== 数据库相关 ====================
    DATABASE_ERROR = (40001, '数据库操作失败')
    DATABASE_CONNECTION_ERROR = (40002, '数据库连接失败')
    DATABASE_INTEGRITY_ERROR = (40003, '数据完整性错误')
    DATABASE_TIMEOUT_ERROR = (40004, '数据库操作超时')

    # ==================== 租户相关 ====================
    MISSING_TENANT_IDENTIFIER_ERROR = (50001, '缺少租户标识')
    TENANT_DISABLED_ERROR = (50002, '租户已禁用')
    TENANT_NOT_MATCH_ERROR = (50003, '租户不匹配')
    TENANT_NOT_EXIST_ERROR = (50004, '租户不存在')
    TENANT_EXISTS_ERROR = (50005, '租户已存在')
    TENANT_CREATE_ERROR = (50006, '租户创建失败')
    TENANT_UPDATE_ERROR = (50007, '租户更新失败')
    TENANT_DELETE_ERROR = (50008, '租户删除失败')

    # ==================== 权限相关 ====================
    PERMISSION_DENIED_ERROR = (50100, '权限不足')

    # ==================== 速率限制 ====================
    RATE_LIMIT_ERROR = (42901, '请求过于频繁，请稍后再试')

    # ==================== 任务相关 ====================
    DUPLICATED_TASK = (60000, '任务在进行中')
    CONFIG_MISSING = (60001, '配置缺失')
    QUEUE_FULL = (60002, '队列已满')
    CONFIG_ERROR = (60003, '配置错误')
    REDIS_ERROR = (60004, 'Redis错误')
    UNKNOWN_ERROR = (60005, '未知错误')

    TASK_GENERATE_FAILED = (60100, '结果生成失败')
    TASK_IS_CANCELED = (60101, '任务已取消')
    TASK_IS_RUNNING = (60102, '任务正在运行')
    TASK_IS_FINISHED = (60103, '任务已完成')
    TASK_IS_FAILED = (60104, '任务执行失败')
    TASK_IS_TIMEOUT = (60105, '任务执行超时')
    TASK_IS_NOT_EXIST = (60106, '任务不存在')
    TASK_IS_NOT_RUNNING = (60107, '任务未运行')
    TASK_IS_NOT_FINISHED = (60108, '任务未完成')
    TASK_IS_NOT_FAILED = (60109, '任务未失败')
    TASK_IS_NOT_TIMEOUT = (60110, '任务未超时')
    CANCEL_TASK_ERROR = (60111, '取消任务失败')

    @property
    def code(self):
        return self.value[0]

    @property
    def msg(self):
        return self.value[1]

    @classmethod
    def collect_status(cls):
        text = ""
        for s in cls:
            text += f"{s.code} {s.msg}\n"
        return text