from typing import Any, Dict, List

from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self, repo: UserRepository | None = None) -> None:
        self.repo = repo or UserRepository()

    def get_users(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        return self.repo.find_all(limit=limit, offset=offset)

    def create_user(self, username: str) -> Dict[str, Any]:
        return self.repo.save(username)
