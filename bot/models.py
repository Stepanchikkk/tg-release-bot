from dataclasses import dataclass
from typing import List, Optional

@dataclass
class App:
    key: str
    title: str
    link: str
    repo: str
    asset_filters: List[str]
    subscribers_users: List[int]
    subscribers_chats: List[int]
    latest_release: Optional[str] = None