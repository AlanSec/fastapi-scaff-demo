"""Bcrypt 密码哈希器实现"""
import bcrypt

from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.password import Password, HashedPassword


class BcryptPasswordHasher(PasswordHasher):
    """基于 Bcrypt 的密码哈希器"""
    
    def hash(self, password: Password) -> HashedPassword:
        """哈希密码"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.value.encode('utf-8'), salt)
        return HashedPassword(hashed.decode('utf-8'))
    
    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            password.value.encode('utf-8'), 
            hashed.value.encode('utf-8')
        )
