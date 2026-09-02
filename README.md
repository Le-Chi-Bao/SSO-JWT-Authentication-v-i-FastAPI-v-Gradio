# SSO + JWT Authentication với FastAPI và Gradio

> Demo project môn ATTT - Hệ thống Xác thực người dùng sử dụng JWT Token

---

## 1. Giới thiệu Project

### Tổng quan

Đây là một hệ thống **Single Sign-On (SSO) + JWT Authentication** được xây dựng bằng:

- **FastAPI** - Framework API hiệu năng cao
- **PyJWT** - Thư viện tạo và xác thực JWT tokens
- **Pydantic** - Validation cho request/response
- **Gradio** - Giao diện web đẹp mắt
- **Docker** - Đóng gói và triển khai

### Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GRADIO APP (Port 7860)                       │
│                    Giao diện người dùng (UI)                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
          │ Auth Server  │ │Product Svc  │ │ Auth Server  │
          │  (Port 8000) │ │(Port 8001)  │ │  /verify     │
          │   /login     │ │/products    │ │              │
          └──────────────┘ └──────────────┘ └──────────────┘
                 │               │
                 ▼               ▼
          ┌──────────────┐ ┌──────────────┐
          │ JWT Token    │ │ Protected    │
          │ Generated    │ │ Resources    │
          └──────────────┘ └──────────────┘
```

### Các thành phần

| Service | Port | Mô tả |
|---------|------|-------|
| `auth_server.py` | 8000 | Xác thực user, tạo JWT token |
| `product_service.py` | 8001 | Quản lý sản phẩm (protected) |
| `gradio_app.py` | 7860 | Giao diện web UI |
| Docker | - | Đóng gói tất cả services |

---

## 2. Yêu cầu hệ thống

### Phần mềm cần thiết

| Yêu cầu | Phiên bản tối thiểu |
|----------|---------------------|
| Python | 3.8+ |
| pip | Latest |
| Docker (optional) | 20.10+ |
| Docker Compose (optional) | 1.29+ |

### Cài đặt Python

Nếu chưa có Python, tải tại: https://www.python.org/downloads/

**Lưu ý:** Chọn "Add Python to PATH" khi cài đặt.

---

## 3. Cài đặt

### Cách 1: Cài đặt thủ công

```bash
# Clone/Download project
cd "e:\Desktop\Các môn học năm 2\ATTT"

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Cài đặt dependencies
pip install fastapi uvicorn pyjwt pydantic gradio requests
```

### Cách 2: Dùng requirements.txt

```bash
# Tạo file requirements.txt trước (nếu chưa có)
pip freeze > requirements.txt

# Cài đặt từ requirements.txt
pip install -r requirements.txt
```

### Cách 3: Dùng Docker

```bash
# Build và chạy tất cả services
docker-compose up --build

# Hoặc chạy dev mode (không cần build)
docker-compose -f docker-compose.dev.yml up
```

---

## 4. Cách chạy

### Chạy từng service riêng lẻ

Mở **3 terminal** và chạy đồng thời:

```bash
# ============================================
# TERMINAL 1: Auth Server (Port 8000)
# ============================================
cd "e:\Desktop\Các môn học năm 2\ATTT"
python auth_server.py

# Output:
# ==================================================
# 🚀 Auth Server đang khởi động...
# 📖 Swagger Docs: http://localhost:8000/docs
# ==================================================
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
# ============================================
# TERMINAL 2: Product Service (Port 8001)
# ============================================
cd "e:\Desktop\Các môn học năm 2\ATTT"
python product_service.py

# Output:
# ==================================================
# 🚀 Product Service đang khởi động...
# 📖 Swagger Docs: http://localhost:8001/docs
# ==================================================
# INFO:     Uvicorn running on http://0.0.0.0:8001
```

```bash
# ============================================
# TERMINAL 3: Gradio App (Port 7860)
# ============================================
cd "e:\Desktop\Các môn học năm 2\ATTT"
python gradio_app.py

# Output:
# ==================================================
# 🚀 Gradio App đang khởi động...
# 🌐 URL: http://localhost:7860
# ==================================================
# Running on local URL: http://0.0.0.0:7860
```

### Kiểm tra services đang chạy

```bash
# Kiểm tra các port đang listen
netstat -an | findstr "8000 8001 7860"
```

---

## 5. Cách test với Postman

### Bước 1: Login để lấy Token

**POST** `http://localhost:8000/api/auth/login`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Response thành công:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "role": "admin",
    "expires_in": 1800
}
```

> Copy giá trị `access_token` để sử dụng ở bước tiếp theo.

---

### Bước 2: Gọi API Protected

#### 2a. Xem sản phẩm (tất cả user đều được)

**GET** `http://localhost:8001/api/products/protected`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Laptop",
        "price": 15000000,
        "stock": 10,
        "created_by": "admin"
    },
    {
        "id": 2,
        "name": "Điện thoại",
        "price": 8000000,
        "stock": 25,
        "created_by": "admin"
    }
]
```

#### 2b. Tạo sản phẩm (chỉ admin)

**POST** `http://localhost:8001/api/products`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Body:**
```json
{
    "name": "Laptop Gaming",
    "price": 25000000,
    "stock": 5
}
```

**Response:**
```json
{
    "id": 5,
    "name": "Laptop Gaming",
    "price": 25000000,
    "stock": 5
}
```

---

### Bước 3: Verify Token

**GET** `http://localhost:8000/api/auth/verify`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
    "valid": true,
    "username": "admin",
    "role": "admin",
    "exp": 1725273890
}
```

---

### Các lỗi thường gặp

| Mã lỗi | Nguyên nhân | Cách khắc phục |
|--------|-------------|----------------|
| 401 Unauthorized | Token hết hạn hoặc không hợp lệ | Đăng nhập lại để lấy token mới |
| 403 Forbidden | Không có quyền admin | Dùng token của admin |
| 400 Bad Request | Body JSON sai format | Kiểm tra lại JSON |
| Connection Refused | Service chưa chạy | Chạy service tương ứng |

---

## 6. Demo Gradio

### Truy cập giao diện

Mở trình duyệt và truy cập:

```
http://localhost:7860
```

### Các Tab trong Gradio

#### Tab 1: 🔑 Đăng nhập
1. Nhập username/password
2. Click "Đăng nhập"
3. Copy token từ kết quả

#### Tab 2: 📦 Xem sản phẩm
1. Paste token vào ô JWT Token
2. Click "Xem sản phẩm"
3. Xem danh sách sản phẩm

#### Tab 3: ➕ Tạo sản phẩm (Admin only)
1. Paste token của admin
2. Nhập thông tin sản phẩm
3. Click "Tạo sản phẩm"
4. Xem kết quả

#### Tab 4: 🔍 Verify Token
1. Paste token cần kiểm tra
2. Click "Kiểm tra Token"
3. Xem thông tin chi tiết

### Tài khoản test

| Username | Password | Role | Quyền |
|----------|----------|------|-------|
| admin | admin123 | admin | Tất cả chức năng |
| user | user123 | user | Xem sản phẩm |
| viewer | viewer123 | viewer | Xem sản phẩm |

---

## 7. Cấu trúc thư mục

```
e:\Desktop\Các môn học năm 2\ATTT\
│
├── auth_server.py          # Auth Service - Tạo & verify JWT
├── product_service.py      # Product Service - CRUD sản phẩm
├── gradio_app.py           # Gradio UI - Giao diện web
│
├── docker-compose.yml      # Docker compose (production)
├── docker-compose.dev.yml  # Docker compose (development)
├── Dockerfile.auth         # Docker image cho Auth
├── Dockerfile.product      # Docker image cho Product
├── Dockerfile.grado       # Docker image cho Gradio
│
└── README.md               # File này
```

### Mô tả chi tiết

| File | Mô tả | Port |
|------|-------|------|
| `auth_server.py` | Server xác thực, login, verify JWT | 8000 |
| `product_service.py` | Server quản lý sản phẩm | 8001 |
| `gradio_app.py` | Giao diện web Gradio | 7860 |
| `docker-compose.yml` | Cấu hình Docker multi-services | - |

---

## 8. Giải thích luồng SSO + JWT

### 8.1. SSO (Single Sign-On) là gì?

**SSO** cho phép user đăng nhập **một lần** và truy cập **nhiều services** khác nhau mà không cần đăng nhập lại.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LUỒNG SSO TRADITIONAL                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   User đăng nhập 1 lần                                               │
│         │                                                            │
│         ▼                                                            │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│   │  Service A  │     │  Service B  │     │  Service C  │          │
│   │  login()    │     │  login()    │     │  login()    │          │
│   │  ❌ Lỗi     │     │  ❌ Lỗi     │     │  ❌ Lỗi     │          │
│   └─────────────┘     └─────────────┘     └─────────────┘          │
│                                                                      │
│   User phải đăng nhập 3 lần riêng cho mỗi service!                 │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    LUỒNG SSO VỚI JWT                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   User đăng nhập 1 lần → Nhận JWT Token                             │
│         │                                                            │
│         ▼                                                            │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│   │  Service A  │     │  Service B  │     │  Service C  │          │
│   │  JWT Token  │     │  JWT Token  │     │  JWT Token  │          │
│   │  ✅ OK      │     │  ✅ OK      │     │  ✅ OK      │          │
│   └─────────────┘     └─────────────┘     └─────────────┘          │
│                                                                      │
│   Token được share giữa tất cả services!                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.2. JWT (JSON Web Token) là gì?

**JWT** là một chuẩn token dạng string, chia thành 3 phần ngăn cách bởi dấu `.`:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
─────────────────────────────────────────────── ──────────────────────  ───────────
              Header                                  Payload                        Signature
           (thuật toán)                          (dữ liệu)                    (xác minh)
```

#### Cấu trúc JWT

```json
// 1. HEADER - Thông tin thuật toán
{
    "alg": "HS256",
    "typ": "JWT"
}

// 2. PAYLOAD - Dữ liệu (claims)
{
    "sub": "admin",           // Subject - username
    "role": "admin",          // Role - vai trò
    "exp": 1725273890,        // Expiration - hết hạn
    "iat": 1725271090         // Issued at - thời gian tạo
}

// 3. SIGNATURE - Chữ ký số
HMAC-SHA256(
    base64UrlEncode(header) + "." + base64UrlEncode(payload),
    SECRET_KEY
)
```

### 8.3. Luồng hoạt động chi tiết

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LUỒNG JWT AUTHENTICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. USER LOGIN                                                       │
│  ┌──────────┐      POST /login        ┌──────────────┐              │
│  │  Client  │ ──────────────────────▶ │  Auth Server │              │
│  └──────────┘   {u,p}                 └──────────────┘              │
│                                            │                         │
│                                            ▼                         │
│                                     Verify username/password         │
│                                            │                         │
│                                            ▼                         │
│                                     Create JWT Token                 │
│                                     (sign with SECRET_KEY)          │
│                                                                      │
│  2. RECEIVE TOKEN                                                    │
│  ┌──────────┐      {access_token}    ┌──────────────┐              │
│  │  Client  │ ◀────────────────────── │  Auth Server │              │
│  └──────────┘                         └──────────────┘              │
│         │                                                            │
│         │ Store token (localStorage/Cookie)                         │
│         │                                                            │
│  3. ACCESS PROTECTED API                                            │
│  ┌──────────┐      GET /products        ┌──────────────┐              │
│  │  Client  │ ──────────────────────▶ │  Product Svc  │              │
│  └──────────┘   Bearer <token>        └──────────────┘              │
│                                            │                         │
│                                            ▼                         │
│                                     Extract token                   │
│                                            │                         │
│                                            ▼                         │
│                                     Decode & Verify                  │
│                                     (check signature, exp)           │
│                                            │                         │
│                         ┌──────────────────┴──────────────────┐    │
│                         │                                         │    │
│                         ▼                                         ▼    │
│                   ✅ Valid                                 ❌ Invalid │
│                         │                                         │    │
│                         ▼                                         ▼    │
│                  Return data                             Return 401 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.4. Security Features

| Tính năng | Mô tả |
|-----------|-------|
| **Signature** | Token được sign bằng SECRET_KEY, không thể giả mạo |
| **Expiration** | Token có thời hạn (30 phút), tự hết hạn |
| **Role-based** | Payload chứa role để phân quyền |
| **Stateless** | Server không lưu session, token tự chứa thông tin |

### 8.5. So sánh Session vs JWT

| Tiêu chí | Session | JWT |
|----------|---------|-----|
| Lưu trữ | Server-side | Client-side |
| Scalability | Khó scale | Dễ scale |
| Stateless | Cần database | Không cần |
| Size | Nhỏ | Lớn hơn |
| Logout | Server-side | Khó revoke |

---

## 9. API Endpoints Summary

### Auth Server (Port 8000)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/auth/login` | Đăng nhập | ❌ |
| GET | `/api/auth/verify` | Verify token | ✅ |
| GET | `/` | Health check | ❌ |

### Product Service (Port 8001)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| GET | `/api/products` | Danh sách sản phẩm (public) | ❌ |
| GET | `/api/products/protected` | Danh sách sản phẩm (private) | ✅ |
| POST | `/api/products` | Tạo sản phẩm | ✅ Admin |

---

## 10. Troubleshooting

### Lỗi "Connection Refused"

```bash
# Kiểm tra port đang chạy
netstat -an | findstr "8000"

# Restart service
python auth_server.py
```

### Lỗi "Token expired"

```bash
# Token hết hạn sau 30 phút
# Đăng nhập lại để lấy token mới
```

### Lỗi "Permission denied"

```bash
# Chỉ admin mới được tạo sản phẩm
# Dùng username: admin, password: admin123
```

### Docker issues

```bash
# Xóa container và build lại
docker-compose down
docker-compose up --build

# Xem logs
docker-compose logs -f
```

---

## 11. License

MIT License - Dùng cho mục đích học tập.

---

**Made with ❤️ for ATTT Course**
