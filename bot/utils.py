import re
import logging

logger = logging.getLogger(__name__)

def validate_repo(repo: str) -> bool:
    """Проверяет, соответствует ли строка формату GitHub-репозитория (owner/repo)."""
    pattern = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, repo))

def validate_key(key: str) -> bool:
    """Проверяет, содержит ли ключ приложения только буквенно-цифровые символы и подчеркивания."""
    pattern = r"^[a-zA-Z0-9_]+$"
    return bool(re.match(pattern, key))