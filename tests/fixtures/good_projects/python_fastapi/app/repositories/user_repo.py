from typing import Any, Dict, List


class UserRepository:
    def find_all(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        # Mock safe query with pagination
        return [{"id": "1", "username": "alice"}]

    def save(self, username: str) -> Dict[str, Any]:
        return {"id": "2", "username": username}
