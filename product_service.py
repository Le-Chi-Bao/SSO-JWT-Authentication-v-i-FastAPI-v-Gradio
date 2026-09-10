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
# FAKE DATABASE - Lưu trữ sản phẩm mẫu (30 sản phẩm demo)
# ============================================================

FAKE_PRODUCTS_DB = [
    # Electronics - Máy tính & Laptop
    {"id": 1, "name": "Laptop Gaming ASUS ROG", "price": 32000000, "stock": 15},
    {"id": 2, "name": "MacBook Pro 14 inch M3", "price": 45000000, "stock": 8},
    {"id": 3, "name": "Laptop Dell XPS 15", "price": 28000000, "stock": 12},
    {"id": 4, "name": "MacBook Air M2", "price": 25000000, "stock": 20},
    {"id": 5, "name": "Laptop HP Pavilion 15", "price": 18000000, "stock": 18},

    # Điện thoại & Tablet
    {"id": 6, "name": "iPhone 15 Pro Max", "price": 32000000, "stock": 25},
    {"id": 7, "name": "Samsung Galaxy S24 Ultra", "price": 28000000, "stock": 22},
    {"id": 8, "name": "Xiaomi 14 Pro", "price": 15000000, "stock": 30},
    {"id": 9, "name": "OPPO Find X7", "price": 18000000, "stock": 15},
    {"id": 10, "name": "iPad Pro 12.9 M4", "price": 35000000, "stock": 10},

    # Phụ kiện âm thanh
    {"id": 11, "name": "AirPods Pro 2", "price": 6500000, "stock": 50},
    {"id": 12, "name": "Sony WH-1000XM5", "price": 8500000, "stock": 35},
    {"id": 13, "name": "Samsung Galaxy Buds2 Pro", "price": 4500000, "stock": 40},
    {"id": 14, "name": "Tai nghe Bluetooth JBL", "price": 2200000, "stock": 60},
    {"id": 15, "name": "Loa JBL Flip 6", "price": 3500000, "stock": 45},

    # Phụ kiện máy tính
    {"id": 16, "name": "Chuột Logitech MX Master 3S", "price": 2800000, "stock": 55},
    {"id": 17, "name": "Bàn phím cơ Keychron K8", "price": 3500000, "stock": 40},
    {"id": 18, "name": "Màn hình LG 27 inch 4K", "price": 12000000, "stock": 20},
    {"id": 19, "name": "Webcam Logitech Brio 4K", "price": 5500000, "stock": 30},
    {"id": 20, "name": "Micro USB Elgato Wave 3", "price": 3800000, "stock": 25},

    # Thiết bị lưu trữ
    {"id": 21, "name": "Ổ SSD Samsung 1TB", "price": 2500000, "stock": 80},
    {"id": 22, "name": "USB SanDisk 128GB", "price": 350000, "stock": 100},
    {"id": 23, "name": "Ổ cứng HDD 4TB WD", "price": 2200000, "stock": 35},
    {"id": 24, "name": "Card đồ họa RTX 4060", "price": 12000000, "stock": 12},

    # Thiết bị thông minh
    {"id": 25, "name": "Apple Watch Ultra 2", "price": 22000000, "stock": 18},
    {"id": 26, "name": "Samsung Galaxy Watch 6", "price": 8500000, "stock": 28},
    {"id": 27, "name": "Xiaomi Band 8 Pro", "price": 1500000, "stock": 70},
    {"id": 28, "name": "Kính Meta Quest 3", "price": 18000000, "stock": 15},

    # Smart Home
    {"id": 29, "name": "Loa thông minh Alexa", "price": 2500000, "stock": 40},
    {"id": 30, "name": "Robot hút bụi Xiaomi", "price": 6500000, "stock": 25},
]

# Biến đếm ID cho sản phẩm mới
product_id_counter = 31  # ID tiếp theo cho sản phẩm mới

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
    Giai ma va xac thuc JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token da het han. Vui long dang nhap lai."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token khong hop le."
        )

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency de verify JWT tu header Authorization.
    """
    return decode_jwt_token(credentials.credentials)

def require_admin(current_user: dict = Depends(verify_token)) -> dict:
    """
    Dependency yeu cau quyen admin
    """
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ban khong co quyen. Chi admin duoc phep."
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

    API nay yeu cau:
    1. JWT token hop le
    2. Token phai co role = "admin"

    Quy trinh xu ly:
    1. verify_token() - Kiem tra token co hop le khong
    2. require_admin() - Kiem tra role co phai admin khong
    3. Neu ca 2 deu OK -> tao san pham
    4. Neu token loi -> 401 Unauthorized
    5. Neu khong phai admin -> 403 Forbidden
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
