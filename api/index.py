from http.server import BaseHTTPRequestHandler
import os


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        target_url = os.environ.get("STREAMLIT_APP_URL", "")
        if target_url:
            self.send_response(302)
            self.send_header("Location", target_url)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hưng Phát WMS — Hệ Thống Đánh Giá Thị Trường Mở Rộng</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 50%, #fbcfe8 100%);
            color: #4a154b;
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .card {
            max-width: 720px;
            background: rgba(255, 255, 255, 0.94);
            border: 2px solid #f472b6;
            border-radius: 28px;
            padding: 38px 44px;
            box-shadow: 0 20px 50px rgba(131, 24, 67, 0.14);
        }
        h1 {
            color: #831843;
            margin-top: 0;
            font-size: 1.75rem;
        }
        .badge {
            display: inline-block;
            background: #fdf2f8;
            color: #be185d;
            border: 1.5px solid #f472b6;
            border-radius: 999px;
            padding: 6px 16px;
            font-weight: 700;
            font-size: 0.9rem;
            margin-bottom: 16px;
        }
        .step-box {
            background: #fffbfe;
            border: 1.5px solid #fce7f3;
            border-radius: 18px;
            padding: 18px 22px;
            margin: 16px 0;
            line-height: 1.65;
        }
        code {
            background: #fce7f3;
            color: #831843;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 700;
        }
        a.btn {
            display: inline-block;
            margin-top: 12px;
            background: linear-gradient(135deg, #ec4899, #be185d);
            color: #ffffff;
            text-decoration: none;
            font-weight: 700;
            padding: 12px 24px;
            border-radius: 999px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">🌸 Hưng Phát WMS — AI Agent Đánh Giá Thị Trường</div>
        <h1>Build Vercel Thành Công! Hướng Dẫn Chạy Full Streamlit</h1>
        <p>Vercel chỉ hỗ trợ hàm Serverless tĩnh (không hỗ trợ kết nối <strong>WebSocket liên tục</strong> của Streamlit). Để chạy trực tiếp toàn bộ giao diện 3 bước của <code>app.py</code> miễn phí 100%, bạn có 2 cách:</p>
        <div class="step-box">
            <strong>Cách 1 (Khuyên dùng - 1 Click trên Streamlit Community Cloud):</strong><br>
            1. Truy cập <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a> và đăng nhập bằng GitHub.<br>
            2. Chọn kho code GitHub này, chọn file chính là <code>app.py</code> rồi bấm <strong>Deploy</strong>.<br>
            3. (Tùy chọn) Dán link Streamlit vừa tạo vào biến môi trường <code>STREAMLIT_APP_URL</code> trên Vercel để tên miền Vercel tự động chuyển hướng sang ứng dụng!
        </div>
        <div class="step-box">
            <strong>Cách 2 (Chạy trên Render / Railway):</strong><br>
            Dự án đã có sẵn <code>Procfile</code> và <code>requirements.txt</code> đầy đủ. Bạn chỉ cần kết nối GitHub vào Render hoặc Railway là web sẽ tự động chạy.
        </div>
        <a class="btn" href="https://share.streamlit.io" target="_blank">🚀 Deploy Miễn Phí Lên Streamlit Cloud Ngay</a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

