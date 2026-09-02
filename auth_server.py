"""
Auth Server - FastAPI JWT Authentication Demo
Môn ATTT - Xác thực JWT
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt
from datetime import datetime, timedelta
from typing import Optional

# ============================================================
# CẤU HÌNH CƠ BẢN
# ============================================================

app = FastAPI(
    title="Auth Server API",
    description="API xác thực người dùng sử dụng JWT Token",
    version="1.0.0"
)

# Khóa bí mật để mã hóa/giải mã JWT
SECRET_KEY = "supersecretkey"
# Thuật toán mã hóa
ALGORITHM = "HS256"
# Thời gian hết hạn token (30 phút)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Instance của security scheme cho Bearer token
security = HTTPBearer()

# ============================================================
# FAKE DATABASE - Lưu trữ tạm thông tin users
# ============================================================

# Dictionary chứa thông tin users: username -> {password, role}
FAKE_USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },
    "user": {
        "password": "user123",
        "role": "user"
    },
    "viewer": {
        "password": "viewer123",
        "role": "viewer"
    }
}

# ============================================================
# PYDANTIC MODELS - Định nghĩa request/response schemas
# ============================================================

class LoginRequest(BaseModel):
    """Schema cho request đăng nhập"""
    username: str = Field(..., min_length=1, description="Tên đăng nhập")
    password: str = Field(..., min_length=1, description="Mật khẩu")

class LoginResponse(BaseModel):
    """Schema cho response đăng nhập thành công"""
    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Loại token")
    role: str = Field(..., description="Vai trò người dùng")
    expires_in: int = Field(..., description="Thời gian hết hạn (giây)")

class VerifyResponse(BaseModel):
    """Schema cho response xác thực token"""
    valid: bool = Field(..., description="Token có hợp lệ không")
    username: Optional[str] = Field(None, description="Tên người dùng")
    role: Optional[str] = Field(None, description="Vai trò người dùng")
    exp: Optional[int] = Field(None, description="Thời gian hết hạn (timestamp)")

class ProtectedResponse(BaseModel):
    """Schema cho response route được bảo vệ"""
    message: str = Field(..., description="Lời chào")

class ErrorResponse(BaseModel):
    """Schema cho response lỗi"""
    detail: str = Field(..., description="Chi tiết lỗi")

# ============================================================
# HELPER FUNCTIONS - Các hàm hỗ trợ
# ============================================================

def create_access_token(username: str, role: str) -> dict:
    """
    Tạo JWT token mới cho người dùng

    Args:
        username: Tên đăng nhập
        role: Vai trò người dùng

    Returns:
        Dictionary chứa token và thông tin liên quan
    """
    # Tính toán thời gian hết hạn
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Tạo payload cho JWT
    payload = {
        "sub": username,          # Subject - tên người dùng
        "role": role,             # Vai trò
        "exp": expire,            # Expiration time - thời gian hết hạn
        "iat": datetime.utcnow()  # Issued at - thời gian tạo
    }

    # Mã hóa JWT token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Chuyển sang giây
    }

def verify_token(token: str) -> dict:
    """
    Xác thực và giải mã JWT token

    Args:
        token: JWT token cần xác thực

    Returns:
        Dictionary chứa thông tin từ token

    Raises:
        HTTPException: Khi token không hợp lệ hoặc hết hạn
    """
    try:
        # Giải mã và xác thực token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "exp": payload.get("exp")
        }
    except jwt.ExpiredSignatureError:
        # Token đã hết hạn
        raise HTTPException(
            status_code=401,
            detail="Token đã hết hạn"
        )
    except jwt.InvalidTokenError:
        # Token không hợp lệ
        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency để lấy thông tin user hiện tại từ token

    Args:
        credentials: Bearer token từ header Authorization

    Returns:
        Dictionary chứa thông tin user đã giải mã

    Raises:
        HTTPException: Khi xác thực thất bại
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token đã hết hạn. Vui lòng đăng nhập lại."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ. Vui lòng đăng nhập lại."
        )

# ============================================================
# API ENDPOINTS - Các endpoint chính
# ============================================================

@app.post(
    "/api/auth/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Đăng nhập và nhận JWT token",
    description="Xác thực username/password và trả về JWT token"
)
async def login(request: LoginRequest):
    """
    Endpoint đăng nhập

    - **username**: Tên đăng nhập (admin, user, viewer)
    - **password**: Mật khẩu tương ứng
    """
    # Kiểm tra username có tồn tại trong database không
    if request.username not in FAKE_USERS_DB:
        raise HTTPException(
            status_code=401,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )

    # Lấy thông tin user từ database
    user = FAKE_USERS_DB[request.username]

    # Kiểm tra password có đúng không
    if user["password"] != request.password:
        raise HTTPException(
            status_code=401,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )

    # Tạo và trả về JWT token
    return create_access_token(request.username, user["role"])

@app.get(
    "/api/auth/verify",
    response_model=VerifyResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Xác thực JWT token",
    description="Kiểm tra token có hợp lệ không"
)
async def verify_token_endpoint(
    authorization: str = Header(..., description="Bearer token")
):
    """
    Endpoint xác thực token

    - Header: `Authorization: Bearer <token>`
    """
    # Tách Bearer prefix khỏi token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Định dạng Authorization header không hợp lệ"
        )

    token = authorization.replace("Bearer ", "")

    # Xác thực token
    return verify_token(token)

@app.get(
    "/api/auth/protected",
    response_model=ProtectedResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Route được bảo vệ",
    description="Endpoint yêu cầu xác thực JWT token"
)
async def protected_route(current_user: dict = Depends(get_current_user)):
    """
    Endpoint chỉ accessible khi có token hợp lệ

    - Header: `Authorization: Bearer <token>`
    """
    username = current_user.get("sub")
    return ProtectedResponse(message=f"Xin chào {username}")

# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/", summary="Health Check")
async def root():
    """Endpoint kiểm tra server có đang chạy không"""
    return {"status": "ok", "message": "Auth Server đang chạy!"}

@app.get("/health", summary="Health Check")
async def health():
    """Endpoint kiểm tra health"""
    return {"status": "healthy"}

# ============================================================
# CHẠY SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Auth Server đang khởi động...")
    print("📖 Swagger Docs: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
