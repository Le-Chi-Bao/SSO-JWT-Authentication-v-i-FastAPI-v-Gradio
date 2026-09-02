"""
Gradio App - Giao diện Web cho Auth & Product Service
Môn ATTT - Demo giao diện người dùng với Gradio
"""

import gradio as gr
import requests
import json
from typing import Optional

# ============================================================
# CẤU HÌNH API
# ============================================================

import os

# URL của các service
# Local development: dùng localhost
# Docker: dùng service name trong network

def get_api_urls():
    """
    Lấy API URLs dựa trên môi trường chạy
    - Docker: dùng service name (auth_server, product_service)
    - Local: dùng localhost
    """
    # Kiểm tra xem có đang chạy trong Docker không
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')

    if in_docker:
        return {
            'auth': 'http://auth_server:8000/api/auth',
            'product': 'http://product_service:8001/api/products'
        }
    else:
        return {
            'auth': 'http://localhost:8000/api/auth',
            'product': 'http://localhost:8001/api/products'
        }

API_URLS = get_api_urls()
AUTH_API_URL = API_URLS['auth']
PRODUCT_API_URL = API_URLS['product']

# ============================================================
# HÀM GỌI API - Kết nối đến backend
# ============================================================

def login_api(username: str, password: str) -> str:
    """
    Gọi API đăng nhập

    Args:
        username: Tên đăng nhập
        password: Mật khẩu

    Returns:
        Chuỗi kết quả hiển thị cho user
    """
    try:
        # Gửi request POST đến auth service
        response = requests.post(
            f"{AUTH_API_URL}/login",
            json={"username": username, "password": password},
            timeout=10
        )

        # Xử lý response
        if response.status_code == 200:
            data = response.json()
            return f"""✅ Đăng nhập thành công!

🔑 Token: {data['access_token']}

👤 Role: {data['role']}
⏰ Hết hạn sau: {data['expires_in'] // 60} phút"""
        else:
            # Đăng nhập thất bại
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return f"❌ Đăng nhập thất bại!\n\nLỗi: {error_detail}"

    except requests.exceptions.ConnectionError:
        return "❌ Không thể kết nối đến Auth Server!\n\nHãy chắc chắn auth_server.py đang chạy trên port 8000."
    except Exception as e:
        return f"❌ Đã xảy ra lỗi: {str(e)}"

def view_products_api(token: str) -> str:
    """
    Gọi API xem sản phẩm (protected)

    Args:
        token: JWT token của user

    Returns:
        Chuỗi hiển thị danh sách sản phẩm
    """
    try:
        # Kiểm tra token có trống không
        if not token or token.strip() == "":
            return "⚠️ Vui lòng nhập JWT token!"

        # Gửi request GET với Bearer token
        headers = {"Authorization": f"Bearer {token.strip()}"}
        response = requests.get(
            f"{PRODUCT_API_URL}/protected",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            products = response.json()

            # Format hiển thị đẹp hơn
            result = f"📦 Tìm thấy {len(products)} sản phẩm:\n\n"

            # Tạo bảng hiển thị
            result += "+----+----------------------+------------+----------+\n"
            result += "| ID | Tên sản phẩm        | Giá        | Tồn kho  |\n"
            result += "+----+----------------------+------------+----------+\n"

            for p in products:
                result += f"| {p['id']:2} | {p['name']:<20} | {p['price']:>10,.0f} | {p['stock']:>8} |\n"

            result += "+----+----------------------+------------+----------+\n"
            result += f"\n👤 Người xem: {products[0].get('created_by', 'unknown')}"

            return result
        else:
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return f"❌ Lỗi: {error_detail}"

    except requests.exceptions.ConnectionError:
        return "❌ Không thể kết nối đến Product Service!\n\nHãy chắc chắn product_service.py đang chạy trên port 8001."
    except Exception as e:
        return f"❌ Đã xảy ra lỗi: {str(e)}"

def create_product_api(token: str, name: str, price: float, stock: int) -> str:
    """
    Gọi API tạo sản phẩm mới (chỉ admin)

    Args:
        token: JWT token của admin
        name: Tên sản phẩm
        price: Giá sản phẩm
        stock: Số lượng tồn kho

    Returns:
        Thông báo kết quả
    """
    try:
        # Validate input
        if not token or token.strip() == "":
            return "⚠️ Vui lòng nhập JWT token!"
        if not name or name.strip() == "":
            return "⚠️ Vui lòng nhập tên sản phẩm!"
        if price <= 0:
            return "⚠️ Giá phải lớn hơn 0!"
        if stock < 0:
            return "⚠️ Số lượng không được âm!"

        # Gửi request POST với Bearer token
        headers = {"Authorization": f"Bearer {token.strip()}"}
        payload = {
            "name": name.strip(),
            "price": float(price),
            "stock": int(stock)
        }

        response = requests.post(
            PRODUCT_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 201:
            product = response.json()
            return f"""✅ Tạo sản phẩm thành công!

📦 Sản phẩm đã tạo:
   • ID: {product['id']}
   • Tên: {product['name']}
   • Giá: {product['price']:,.0f} VNĐ
   • Tồn kho: {product['stock']} cái"""
        elif response.status_code == 403:
            return "🚫 Không có quyền!\n\nChỉ tài khoản ADMIN mới được tạo sản phẩm."
        elif response.status_code == 401:
            return "🔒 Token không hợp lệ hoặc đã hết hạn!\n\nVui lòng đăng nhập lại."
        else:
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return f"❌ Lỗi: {error_detail}"

    except requests.exceptions.ConnectionError:
        return "❌ Không thể kết nối đến Product Service!\n\nHãy chắc chắn product_service.py đang chạy trên port 8001."
    except Exception as e:
        return f"❌ Đã xảy ra lỗi: {str(e)}"

def verify_token_api(token: str) -> str:
    """
    Gọi API verify token

    Args:
        token: JWT token cần kiểm tra

    Returns:
        Thông tin chi tiết về token
    """
    try:
        if not token or token.strip() == "":
            return "⚠️ Vui lòng nhập JWT token!"

        # Gửi request GET với Bearer token
        headers = {"Authorization": f"Bearer {token.strip()}"}
        response = requests.get(
            f"{AUTH_API_URL}/verify",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Chuyển đổi timestamp exp sang ngày giờ đọc được
            from datetime import datetime
            exp_time = datetime.fromtimestamp(data['exp'])
            now = datetime.now()

            # Kiểm tra còn hạn không
            is_valid = exp_time > now

            # Decode token để hiển thị payload (base64)
            try:
                import base64
                parts = token.strip().split('.')
                payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
                payload_decoded = json.loads(base64.b64decode(payload_b64))
                token_info = json.dumps(payload_decoded, indent=2, ensure_ascii=False)
            except:
                token_info = "Không thể decode"

            result = f"""✅ Token HỢP LỆ

📋 Thông tin token:
   • Username: {data['username']}
   • Role: {data['role']}
   • Hết hạn: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}
   • Trạng thái: {'🟢 Còn hạn' if is_valid else '🔴 Đã hết hạn'}

📄 Raw Payload:
{token_info}"""

            return result
        else:
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return f"❌ Token không hợp lệ!\n\nLỗi: {error_detail}"

    except requests.exceptions.ConnectionError:
        return "❌ Không thể kết nối đến Auth Server!\n\nHãy chắc chắn auth_server.py đang chạy trên port 8000."
    except Exception as e:
        return f"❌ Đã xảy ra lỗi: {str(e)}"

# ============================================================
# TẠO GIAO DIỆN GRADIO
# ============================================================

# Tạo interface với Blocks để có layout tùy chỉnh
with gr.Blocks(
    title="Auth & Product Demo",
    theme=gr.themes.Soft(),
    css="""
    .main-title {text-align: center; font-size: 24px; font-weight: bold;}
    .subtitle {text-align: center; color: gray;}
    """
) as demo:

    # Tiêu đề
    gr.Markdown("""
    # 🔐 Auth & Product Service Demo
    ### Giao diện quản lý người dùng và sản phẩm
    """)

    # Tabs để chuyển đổi giữa các chức năng
    with gr.Tabs():
        # ----------------------------------------------------------
        # TAB 1: ĐĂNG NHẬP
        # ----------------------------------------------------------
        with gr.TabItem("🔑 Đăng nhập"):
            gr.Markdown("### Đăng nhập để nhận JWT Token")

            with gr.Row():
                with gr.Column(scale=1):
                    # Ô nhập username
                    username_input = gr.Textbox(
                        label="Username",
                        placeholder="Nhập username (admin, user, viewer)",
                        lines=1
                    )

                    # Ô nhập password
                    password_input = gr.Textbox(
                        label="Password",
                        placeholder="Nhập password",
                        lines=1,
                        type="password"
                    )

                    # Nút đăng nhập
                    login_btn = gr.Button("Đăng nhập", variant="primary")

                with gr.Column(scale=2):
                    # Kết quả đăng nhập
                    login_output = gr.Textbox(
                        label="Kết quả",
                        lines=8,
                        interactive=False
                    )

            # Tài khoản mẫu
            gr.Markdown("""
            **📌 Tài khoản mẫu:**
            - `admin` / `admin123` (role: admin - full quyền)
            - `user` / `user123` (role: user - xem sản phẩm)
            - `viewer` / `viewer123` (role: viewer - chỉ xem)
            """)

            # Sự kiện click nút đăng nhập
            login_btn.click(
                fn=login_api,
                inputs=[username_input, password_input],
                outputs=login_output
            )

        # ----------------------------------------------------------
        # TAB 2: XEM SẢN PHẨM
        # ----------------------------------------------------------
        with gr.TabItem("📦 Xem sản phẩm"):
            gr.Markdown("### Xem danh sách sản phẩm (cần đăng nhập)")

            with gr.Row():
                with gr.Column(scale=1):
                    # Ô nhập token
                    view_token_input = gr.Textbox(
                        label="JWT Token",
                        placeholder="Dán JWT token vào đây",
                        lines=3
                    )

                    # Nút xem sản phẩm
                    view_btn = gr.Button("Xem sản phẩm", variant="primary")

                with gr.Column(scale=2):
                    # Kết quả
                    view_output = gr.Textbox(
                        label="Danh sách sản phẩm",
                        lines=15,
                        interactive=False
                    )

            gr.Markdown("""
            **💡 Mẹo:** Sau khi đăng nhập, copy token từ tab "Đăng nhập" và dán vào đây.
            """)

            # Sự kiện
            view_btn.click(
                fn=view_products_api,
                inputs=[view_token_input],
                outputs=view_output
            )

        # ----------------------------------------------------------
        # TAB 3: TẠO SẢN PHẨM (Admin only)
        # ----------------------------------------------------------
        with gr.TabItem("➕ Tạo sản phẩm"):
            gr.Markdown("### Tạo sản phẩm mới (🔒 Chỉ Admin)")

            with gr.Row():
                with gr.Column(scale=1):
                    # Ô nhập token
                    create_token_input = gr.Textbox(
                        label="JWT Token (Admin)",
                        placeholder="Dán token của admin vào đây",
                        lines=3
                    )

                    # Ô nhập thông tin sản phẩm
                    product_name = gr.Textbox(
                        label="Tên sản phẩm",
                        placeholder="VD: Laptop Gaming",
                        lines=1
                    )

                    product_price = gr.Number(
                        label="Giá (VNĐ)",
                        placeholder="VD: 15000000",
                        minimum=0,
                        precision=0
                    )

                    product_stock = gr.Number(
                        label="Số lượng tồn kho",
                        placeholder="VD: 10",
                        minimum=0,
                        step=1
                    )

                    # Nút tạo
                    create_btn = gr.Button("Tạo sản phẩm", variant="primary")

                with gr.Column(scale=2):
                    # Kết quả
                    create_output = gr.Textbox(
                        label="Kết quả",
                        lines=8,
                        interactive=False
                    )

            gr.Markdown("""
            **⚠️ Lưu ý:** Chỉ tài khoản có role `admin` mới được phép tạo sản phẩm.
            Nếu dùng token của `user` hoặc `viewer`, sẽ trả về lỗi "Không có quyền".
            """)

            # Sự kiện
            create_btn.click(
                fn=create_product_api,
                inputs=[create_token_input, product_name, product_price, product_stock],
                outputs=create_output
            )

        # ----------------------------------------------------------
        # TAB 4: VERIFY TOKEN
        # ----------------------------------------------------------
        with gr.TabItem("🔍 Verify Token"):
            gr.Markdown("### Kiểm tra thông tin JWT Token")

            with gr.Row():
                with gr.Column(scale=1):
                    # Ô nhập token
                    verify_token_input = gr.Textbox(
                        label="JWT Token",
                        placeholder="Dán token cần kiểm tra vào đây",
                        lines=5
                    )

                    # Nút kiểm tra
                    verify_btn = gr.Button("Kiểm tra Token", variant="primary")

                with gr.Column(scale=2):
                    # Kết quả
                    verify_output = gr.Textbox(
                        label="Thông tin Token",
                        lines=12,
                        interactive=False
                    )

            gr.Markdown("""
            **🔐 JWT Token chứa:**
            - `sub`: Username của người dùng
            - `role`: Vai trò (admin/user/viewer)
            - `exp`: Thời gian hết hạn (timestamp)
            - `iat`: Thời gian tạo (timestamp)
            """)

            # Sự kiện
            verify_btn.click(
                fn=verify_token_api,
                inputs=[verify_token_input],
                outputs=verify_output
            )

    # Footer
    gr.Markdown("""
    ---
    ### 📝 Hướng dẫn sử dụng
    1. **Đăng nhập** để lấy JWT token
    2. **Xem sản phẩm** bằng token (user/viewer/admin đều được)
    3. **Tạo sản phẩm** chỉ dùng được với token của admin
    4. **Verify token** để xem thông tin chi tiết của token

    ### ⚙️ Yêu cầu hệ thống
    - Auth Server chạy trên **port 8000**
    - Product Service chạy trên **port 8001**
    """)

# ============================================================
# CHẠY APP
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Gradio App đang khởi động...")
    print("🌐 URL: http://localhost:7860")
    print("📖 Swagger Auth: http://localhost:8000/docs")
    print("📖 Swagger Product: http://localhost:8001/docs")
    print("=" * 50)

    # Chạy Gradio app
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False  # True nếu muốn tạo public link
    )
