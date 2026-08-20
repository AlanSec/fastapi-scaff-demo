import re
from dataclasses import dataclass, field


@dataclass(frozen=True, eq=True)
class Email:
    value: str = field()

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError("invalid email")
        object.__setattr__(self, 'value', self.value.lower())

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Email('{self.value}')"
