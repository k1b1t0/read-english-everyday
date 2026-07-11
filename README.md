# Children's Daily English Zalo Bot

Hệ thống Zalo Bot chạy tự động hàng ngày qua GitHub Actions hoặc chạy thử nghiệm trực tiếp trên môi trường local để biên soạn và gửi các bài học tiếng Anh cho trẻ em.

## 📁 Cấu Trúc Thư Mục (Project Structure)

```text
english-kid-zalo-bot/
├── .github/workflows/          # Các file cấu hình GitHub Actions
│   └── english_bot.yml         # Workflow gửi bài đọc tiếng Anh (6h sáng VN)
├── english_bot/                # 📚 Gửi bài đọc tiếng Anh
│   ├── curator.py              # Dịch bài/tóm tắt bằng Gemini API
│   ├── dedup.py                # Quản lý lọc trùng bài viết đã gửi
│   ├── feeds.py                # Cào RSS từ các nguồn giáo dục
│   ├── main.py                 # File thực thi chính của English Bot
│   └── topic_rotation.py       # Xoay vòng chủ đề đọc theo ngày
├── shared/                     # ⚙️ Thư mục chứa thư viện dùng chung
│   ├── __init__.py
│   └── zalo.py                 # Tiện ích gửi tin nhắn qua Zalo Bot API
├── tests/                      # 🧪 Bộ Unit Test tự động
├── plan/                       # 📝 Kế hoạch & Tài liệu hướng dẫn
│   ├── deploy.md               # Hướng dẫn tạo Zalo Bot và config GitHub Secrets
│   ├── how-to-test.md          # Hướng dẫn chạy thử nghiệm bot dưới local
│   └── plan.md                 # Kế hoạch phát triển dự án
├── pyproject.toml              # Cấu hình dự án Python & package dependencies
├── sent_urls.txt               # File lưu trạng thái URL đã gửi
└── README.md                   # Tài liệu giới thiệu tổng quan dự án (file này)
```

---

## 🚀 Cách Thử Nghiệm Nhanh Dưới Local

Trước tiên, hãy chắc chắn bạn đã cài đặt [uv](https://astral.sh/uv/) và đồng bộ hóa thư viện:
```bash
# Đồng bộ môi trường ảo và thư viện
uv sync

# Chạy thử Bot Tiếng Anh (Mock / Dry-Run)
uv run python english_bot/main.py --dry-run --mock
```
*Chi tiết các kịch bản test và cách thiết lập file `.env` vui lòng xem tại [plan/how-to-test.md](plan/how-to-test.md).*

---

## 🛠 Hướng Dẫn Mở Rộng Thêm Bot Mới (Extensibility Guide)

Khi muốn thêm một tính năng gửi thông báo tự động mới (ví dụ: nhắc việc, dự báo thời tiết, tin tức tài chính...):

1. **Tạo thư mục cho bot mới:**
   Tạo thư mục con ở thư mục gốc (ví dụ: `weather_bot/`).

2. **Tạo file code xử lý chính:**
   Tạo file `weather_bot/main.py`. Bạn có thể dễ dàng gọi API Zalo dùng chung bằng cách import:
   ```python
   import sys
   import os

   # Thêm thư mục gốc vào sys.path để import được module shared
   root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
   if root_path not in sys.path:
       sys.path.insert(0, root_path)

   from shared.zalo import send_zalo_message

   # Logic xử lý của bạn...
   message = "Nội dung thông báo cần gửi..."
   send_zalo_message(message)
   ```

3. **Cấu hình lịch chạy tự động:**
   Tạo thêm file workflow trong `.github/workflows/` (ví dụ: `.github/workflows/weather_bot.yml`) với lịch chạy cron và các secrets tương tự như `english_bot.yml`.
