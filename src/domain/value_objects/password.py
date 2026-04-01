from dataclasses import dataclass, field


@dataclass(frozen=True, eq=True)
class Password:
    value: str = field()
    
    def __post_init__(self):
        self._validate_password_strength(self.value)
    
    @staticmethod
    def _validate_password_strength(password: str) -> None:
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        
        if not any(c.isupper() for c in password):
            raise ValueError("password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("password must contain at least one digit")
    
    def __str__(self) -> str:
        return "********"
    
    def __repr__(self) -> str:
        return "Password(********)"


@dataclass(frozen=True, eq=True)
class HashedPassword:
    value: str = field()
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("hashed password cannot be empty")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"HashedPassword('{self.value[:10]}...')"