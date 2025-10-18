# Farda MCP Backend

بک‌اند Farda MCP بر پایهٔ FastAPI، با معماری Async و پشتیبانی از PostgreSQL.

## نیازمندی‌ها

* Python 3.11+
* PostgreSQL 16+
* pip یا Poetry برای مدیریت وابستگی‌ها

## نصب و راه‌اندازی محلی

### ۱. ایجاد محیط مجازی

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# یا
.venv\Scripts\activate  # Windows
```

### ۲. نصب وابستگی‌ها

```bash
pip install -e ".[dev]"
```

### ۳. تنظیم متغیرهای محیطی

```bash
cp .env.example .env
# فایل .env را ویرایش کنید
```

### ۴. اجرای Migration ها (در صورت وجود)

```bash
alembic upgrade head
```

### ۵. اجرای سرور توسعه

```bash
uvicorn backend.apps.core:app --reload --host 0.0.0.0 --port 8000
```

سرور در آدرس `http://localhost:8000` در دسترس خواهد بود.

## تست

```bash
pytest
```

برای دیدن coverage:

```bash
pytest --cov=backend --cov-report=html
```

## Lint و Format

```bash
# بررسی کد
ruff check .

# فرمت کردن کد
ruff format .
```

## Endpoints

* `GET /healthz` - بررسی سلامت سرویس
* `GET /version` - نسخهٔ بک‌اند و وب
* `GET /docs` - مستندات تعاملی Swagger (فقط در محیط local)
* `GET /redoc` - مستندات ReDoc (فقط در محیط local)

## ساختار پروژه

```
backend/
  apps/
    core/          # ماژول اصلی برنامه
      models/      # مدل‌های SQLAlchemy
      schemas/     # Pydantic schemas
      routers/     # API endpoints
    mcp/           # ماژول MCP (رزرو شده)
    connectors/    # کانکتورهای خارجی (رزرو شده)
  tests/           # تست‌های واحد و یکپارچگی
  alembic/         # Migration های دیتابیس
```

## توسعه

این پروژه از استانداردهای زیر پیروی می‌کند:

* **PEP 8** برای استایل کد
* **Type hints** برای همهٔ توابع عمومی
* **Async/await** برای عملیات IO
* **Pydantic** برای اعتبارسنجی داده
* **SQLAlchemy 2.0** برای ORM
* **Alembic** برای مدیریت migration

برای اطلاعات بیشتر، به مستندات در پوشهٔ `docs/` مراجعه کنید.
