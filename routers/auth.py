"""
认证路由模块。

用途：
1. 提供用户注册接口。
2. 提供用户登录并签发访问令牌接口。
3. 提供当前登录用户信息查询接口。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from services.auth import (
    create_access_token,
    hash_password,
    require_current_user,
    verify_password,
)


USERNAME_PATTERN = r"^[A-Za-z0-9_]+$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=USERNAME_PATTERN,
        description="用户名，3-50位，只允许字母、数字和下划线",
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=100,
        pattern=EMAIL_PATTERN,
        description="用户邮箱，需为合法邮箱格式",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="登录密码，最少8位",
    )


class RegisterResponse(BaseModel):
    message: str = Field(
        ...,
        description="注册结果提示信息",
    )
    username: str = Field(
        ...,
        description="注册成功后的用户名",
    )


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="登录用户名，对应标准表单字段 username",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="登录密码，对应标准表单字段 password",
    )

    @classmethod
    def as_form(
        cls,
        username: str = Form(
            ...,
            min_length=3,
            max_length=50,
            description="登录用户名，对应标准表单字段 username",
        ),
        password: str = Form(
            ...,
            min_length=8,
            description="登录密码，对应标准表单字段 password",
        ),
    ) -> "LoginRequest":
        return cls(username=username, password=password)


class LoginResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT 访问令牌",
    )
    token_type: str = Field(
        ...,
        description="令牌类型，固定为 bearer",
    )
    username: str = Field(
        ...,
        description="当前登录用户名",
    )


class CurrentUserResponse(BaseModel):
    id: int = Field(
        ...,
        description="当前用户ID",
    )
    username: str = Field(
        ...,
        description="当前用户名",
    )
    email: str = Field(
        ...,
        description="当前用户邮箱",
    )
    created_at: datetime = Field(
        ...,
        description="用户创建时间",
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
def register(
    request_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse | JSONResponse:
    username_exists = db.scalar(
        select(User).where(User.username == request_data.username)
    )
    if username_exists is not None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "用户名已被占用"},
        )

    email_exists = db.scalar(select(User).where(User.email == request_data.email))
    if email_exists is not None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "邮箱已被注册"},
        )

    user = User(
        username=request_data.username,
        email=request_data.email,
        hashed_password=hash_password(request_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="注册成功",
        username=user.username,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
)
def login(
    form_data: LoginRequest = Depends(LoginRequest.as_form),
    db: Session = Depends(get_db),
) -> LoginResponse | JSONResponse:
    user = db.scalar(select(User).where(User.username == form_data.username))
    if user is None:
        user = db.scalar(select(User).where(User.email == form_data.username))

    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "该用户名/邮箱未注册"},
        )

    if not verify_password(
        form_data.password, user.hashed_password
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "密码错误"},
        )

    access_token = create_access_token({"sub": user.username})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="获取当前登录用户信息",
)
def get_me(
    current_user: User = Depends(require_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
    )
