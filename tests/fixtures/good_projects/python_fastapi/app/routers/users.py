from typing import List

from app.services.user_service import UserService
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

router = APIRouter(tags=["users"])


class UserResponse(BaseModel):
    id: str
    username: str


@router.get("/users", response_model=List[UserResponse])
def list_users(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(),
) -> List[UserResponse]:
    return service.get_users(limit=limit, offset=offset)


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    username: str,
    service: UserService = Depends(),
) -> UserResponse:
    return service.create_user(username)
