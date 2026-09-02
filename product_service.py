"""
Product Service - FastAPI Demo với JWT Authentication
Môn ATTT - Xác thực và Phân quyền
"""

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
import jwt
from datetime import datetime, timedelta

# ============================================================
# CẤU HÌNH CƠ BẢN
# ============================================================

app = FastAPI(
    title="Product Service API",
    description="API quản lý sản phẩm với JWT Authentication",
    version="1.0.0"
)

# Cùng SECRET_KEY với auth_server.py để có thể share token
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

# Instance security cho Bearer token
security = HTTPBearer()

# ============================================================
# FAKE DATABASE - Lưu trữ sản phẩm mẫu
# ============================================================

# Danh sách sản phẩm mẫu
FAKE_PRODUCTS_DB = [
    {"id": 1, "name": "Laptop", "price": 15000000, "stock": 10},
    {"id": 2, "name": "Điện thoại", "price": 8000000, "stock": 25},
    {"id": 3, "name": "Tai nghe", "price": 500000, "stock": 50},
    {"id": 4, "name": "Bàn phím", "price": 300000, "stock": 30},
]

# Biến đếm ID cho sản phẩm mới
product_id_counter = 5

# ============================================================
# PYDANTIC MODELS - Định nghĩa schemas
# ============================================================

class ProductCreate(BaseModel):
    """Schema để tạo sản phẩm mới"""
    name: str = Field(..., min_length=1, max_length=100, description="Tên sản phẩm")
    price: float = Field(..., gt=0, description="Giá sản phẩm (phải > 0)")
    stock: int = Field(..., ge=0, description="Số lượng tồn kho (phải >= 0)")

class ProductResponse(BaseModel):
    """Schema response sản phẩm"""
    id: int
    name: str
    price: float
    stock: int

class ProductWithOwner(BaseModel):
    """Schema response sản phẩm kèm thông tin owner"""
    id: int
    name: str
    price: float
    stock: int
    created_by: str

class ErrorResponse(BaseModel):
    """Schema response lỗi"""
    detail: str

# ============================================================
# JWT VERIFICATION - Các hàm xác thực token
# ============================================================

def decode_jwt_token(token: str) -> dict:
    """
    Giải mã và xác thực JWT token

    Cách hoạt động của JWT Verification:
    1. Nhận token dạng string (VD: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    2. Tách token thành 3 phần (header.payload.signature) bằng dấu "."
    3. Verify signature bằng SECRET_KEY và thuật toán HS256
    4. Kiểm tra expiration time (exp) trong payload
    5. Trả về payload đã giải mã nếu hợp lệ

    Args:
        token: JWT token string

    Returns:
        Dictionary chứa payload đã giải mã

    Raises:
        HTTPException: Khi token hết hạn hoặc không hợp lệ
    """
    try:
        # jwt.decode() sẽ:
        # - Tự động tách token thành 3 phần
        # - Verify signature với SECRET_KEY
        # - Kiểm tra exp (expiration)
        # - Trả về payload dạng dict
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        # Token đã hết hạn (exp time đã qua)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn. Vui lòng đăng nhập lại."
        )

    except jwt.InvalidTokenError:
        # Token không hợp lệ:
        # - Signature không đúng
        # - Token bị corrupt/modify
        # - Thuật toán không khớp
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ."
        )

def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Dependency để verify JWT từ header Authorization

    Args:
        credentials: Bearer token từ HTTP Authorization header

    Returns:
        Payload đã giải mã từ token
    """
    token = credentials.credentials
    return decode_jwt_token(token)

def require_admin(current_user: dict = Depends(verify_token)) -> dict:
    """
    Dependency để yêu cầu quyền admin

    Sử dụng khi cần kiểm tra user có role "admin" hay không

    Args:
        current_user: Payload từ token đã được verify

    Returns:
        Payload của user nếu là admin

    Raises:
        HTTPException 403: Khi user không có quyền admin
    """
    role = current_user.get("role")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này. Chỉ admin mới được phép."
        )

    return current_user

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", summary="Health Check")
async def root():
    """Endpoint kiểm tra server có đang chạy không"""
    return {
        "status": "ok",
        "service": "Product Service",
        "port": 8001
    }

# ----------------------------------------------------------
# PUBLIC API - Không cần JWT
# ----------------------------------------------------------

@app.get(
    "/api/products",
    response_model=List[ProductResponse],
    summary="Lấy danh sách sản phẩm (Public)",
    description="Endpoint công khai, không cần xác thực JWT"
)
async def get_products():
    """
    Trả về danh sách tất cả sản phẩm.

    API này PUBLIC - ai cũng có thể truy cập mà không cần token.
    Thường dùng để hiển thị sản phẩm cho khách hàng.
    """
    return FAKE_PRODUCTS_DB

# ----------------------------------------------------------
# PROTECTED API - Cần JWT
# ----------------------------------------------------------

@app.get(
    "/api/products/protected",
    response_model=List[ProductWithOwner],
    summary="Lấy danh sách sản phẩm (Protected)",
    description="Endpoint yêu cầu JWT token"
)
async def get_products_protected(
    current_user: dict = Depends(verify_token)
):
    """
    Trả về danh sách sản phẩm kèm thông tin người tạo.

    API này PROTECTED - cần có JWT token hợp lệ.
    Token được extract từ header: Authorization: Bearer <token>

    Quy trình xử lý:
    1. Đọc Authorization header
    2. Tách "Bearer " prefix và lấy token
    3. Gọi verify_token() để decode và xác thực
    4. Nếu hợp lệ, trả về dữ liệu kèm username
    5. Nếu không hợp lệ, trả về lỗi 401
    """
    username = current_user.get("sub", "unknown")

    # Trả về products với thông tin người truy cập
    result = []
    for product in FAKE_PRODUCTS_DB:
        result.append({
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "stock": product["stock"],
            "created_by": username  # Thêm thông tin từ JWT
        })

    return result

# ----------------------------------------------------------
# ADMIN ONLY API - Cần JWT + role admin
# ----------------------------------------------------------

@app.post(
    "/api/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Không có quyền admin"}
    },
    summary="Tạo sản phẩm mới (Admin only)",
    description="Chỉ admin mới được phép tạo sản phẩm"
)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Tạo sản phẩm mới trong database.

    API này yêu cầu:
    1. JWT token hợp lệ
    2. Token phải có role = "admin"

    Quy trình xử lý:
    1. verify_token() - Kiểm tra token có hợp lệ không
    2. require_admin() - Kiểm tra role có phải admin không
    3. Nếu cả 2 đều OK → tạo sản phẩm
    4. Nếu token lỗi → 401 Unauthorized
    5. Nếu không phải admin → 403 Forbidden
    """
    global product_id_counter

    # Tạo sản phẩm mới
    new_product = {
        "id": product_id_counter,
        "name": product.name,
        "price": product.price,
        "stock": product.stock
    }

    # Thêm vào database
    FAKE_PRODUCTS_DB.append(new_product)
    product_id_counter += 1

    return new_product

# ============================================================
# CHẠY SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Product Service đang khởi động...")
    print("📖 Swagger Docs: http://localhost:8001/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8001)
