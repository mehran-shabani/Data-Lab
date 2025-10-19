# راهنمای شروع سریع Farda MCP

> **نکته**: این راهنما بعد از پیاده‌سازی پرامپت‌های ۱ تا ۳ نوشته شده است و شامل احراز هویت، چندمستأجری، و مدیریت DataSource است.

این راهنما شما را گام‌به‌گام در نصب و راه‌اندازی محلی Farda MCP همراهی می‌کند.

## پیش‌نیازها

### نرم‌افزارهای مورد نیاز

قبل از شروع، اطمینان حاصل کنید که موارد زیر را نصب کرده‌اید:

* **Python 3.11+** ([دانلود](https://www.python.org/downloads/))
* **Node.js 20+** ([دانلود](https://nodejs.org/))
* **PostgreSQL 16+** ([دانلود](https://www.postgresql.org/download/))
* **Docker & Docker Compose** (اختیاری، برای اجرای کانتینری)
* **Git** ([دانلود](https://git-scm.com/downloads))

### بررسی نصب

```bash
# بررسی Python
python --version  # باید 3.11 یا بالاتر باشد

# بررسی Node.js
node --version    # باید 20 یا بالاتر باشد

# بررسی Docker (اختیاری)
docker --version
docker compose version

# بررسی PostgreSQL
psql --version
```

## راه‌اندازی محلی (بدون Docker)

### ۱. کلون کردن مخزن

```bash
git clone https://github.com/your-org/farda-mcp.git
cd farda-mcp
```

### ۲. راه‌اندازی دیتابیس

#### ایجاد دیتابیس PostgreSQL

```bash
# ورود به PostgreSQL
psql -U postgres

# ایجاد دیتابیس
CREATE DATABASE farda_mcp;

# ایجاد کاربر (اختیاری)
CREATE USER farda_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE farda_mcp TO farda_user;

# خروج
\q
```

### ۳. راه‌اندازی Backend

```bash
cd backend

# ایجاد محیط مجازی
python -m venv .venv

# فعال‌سازی محیط مجازی
# در Linux/macOS:
source .venv/bin/activate
# در Windows:
.venv\Scripts\activate

# نصب وابستگی‌ها
pip install -e ".[dev]"

# کپی فایل محیطی
cp .env.example .env

# ویرایش .env و تنظیم DATABASE_URL و SECRETS_MASTER_KEY
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/farda_mcp
# SECRETS_MASTER_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# اجرای migration ها
alembic upgrade head

# اجرای سرور توسعه
uvicorn apps.core:app --reload --host 0.0.0.0 --port 8000
```

سرور backend در `http://localhost:8000` در دسترس است.

مستندات API: `http://localhost:8000/docs`

### ۴. راه‌اندازی Frontend

در یک ترمینال جدید:

```bash
cd web

# نصب وابستگی‌ها
npm install
# یا اگر از pnpm استفاده می‌کنید:
# pnpm install

# کپی فایل محیطی
cp .env.example .env.local

# ویرایش .env.local در صورت نیاز
# NEXT_PUBLIC_API_URL=http://localhost:8000

# اجرای سرور توسعه
npm run dev
```

وب‌سایت در `http://localhost:3000` در دسترس است.

### ۵. تست اتصال

مرورگر خود را باز کنید و به آدرس‌های زیر بروید:

* **Frontend**: http://localhost:3000
* **Backend API Docs**: http://localhost:8000/docs
* **Health Check Backend**: http://localhost:8000/healthz
* **Health Check Web**: http://localhost:3000/api/health

## راه‌اندازی با Docker Compose (توصیه می‌شود)

راه حل ساده‌تر برای اجرای کل stack:

### ۱. کلون کردن مخزن

```bash
git clone https://github.com/your-org/farda-mcp.git
cd farda-mcp
```

### ۲. تنظیم متغیرهای محیطی

```bash
cd ops/compose
cp .env.example .env

# ویرایش .env در صورت نیاز
nano .env  # یا ویرایشگر دلخواه
```

### ۳. بیلد و اجرا

```bash
# بیلد و اجرای تمام سرویس‌ها
docker compose up -d --build

# مشاهده لاگ‌ها
docker compose logs -f

# بررسی وضعیت سرویس‌ها
docker compose ps
```

### ۴. دسترسی به برنامه

پس از اجرای موفق:

* **Web (از طریق Nginx)**: http://localhost:8080
* **API (از طریق Nginx)**: http://localhost:8080/api/healthz
* **Backend مستقیم**: http://localhost:8000
* **Web مستقیم**: http://localhost:3000
* **PostgreSQL**: localhost:5432

### ۵. دستورات مفید Docker

```bash
# توقف سرویس‌ها
docker compose down

# توقف و حذف volumes
docker compose down -v

# مشاهده لاگ یک سرویس خاص
docker compose logs -f backend

# ورود به کانتینر
docker compose exec backend bash
docker compose exec web sh

# ریستارت یک سرویس
docker compose restart backend

# بیلد مجدد بدون کش
docker compose build --no-cache
```

## اجرای تست‌ها

### تست Backend

```bash
cd backend

# فعال‌سازی محیط مجازی
source .venv/bin/activate  # Linux/macOS
# یا
.venv\Scripts\activate     # Windows

# اجرای تست‌ها
pytest

# اجرای با coverage
pytest --cov=apps --cov-report=html

# مشاهده coverage report
open htmlcov/index.html  # macOS
# یا
xdg-open htmlcov/index.html  # Linux
# یا
start htmlcov/index.html  # Windows
```

### تست Frontend

```bash
cd web

# اجرای تست‌ها (فعلاً placeholder)
npm run test

# Type checking
npm run typecheck

# Linting
npm run lint
```

## توسعه

### Backend Development

#### افزودن یک endpoint جدید

1. ایجاد router جدید در `backend/apps/core/routers/`
2. ایجاد schemas در `backend/apps/core/schemas/`
3. ثبت router در `backend/apps/core/__init__.py`
4. نوشتن تست در `backend/tests/`

```python
# مثال: backend/apps/core/routers/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items():
    return {"items": []}
```

#### اضافه کردن migration

```bash
cd backend

# ایجاد migration جدید
alembic revision --autogenerate -m "describe your changes"

# اعمال migration
alembic upgrade head

# بازگشت migration
alembic downgrade -1
```

### Frontend Development

#### افزودن صفحه جدید

```bash
cd web/app

# ایجاد دایرکتوری برای route جدید
mkdir my-page
cd my-page

# ایجاد فایل صفحه
touch page.tsx
```

```tsx
// web/app/my-page/page.tsx
export default function MyPage() {
  return (
    <div>
      <h1>صفحه جدید من</h1>
    </div>
  )
}
```

#### افزودن کامپوننت

```tsx
// web/components/MyComponent.tsx
interface MyComponentProps {
  title: string
}

export default function MyComponent({ title }: MyComponentProps) {
  return <div>{title}</div>
}
```

## رفع مشکلات رایج

### مشکل اتصال به دیتابیس

```bash
# بررسی اجرای PostgreSQL
sudo systemctl status postgresql  # Linux
# یا
brew services list  # macOS

# بررسی اتصال
psql -U postgres -d farda_mcp -c "SELECT 1"
```

### مشکل پورت در حال استفاده

```bash
# یافتن process که از پورت استفاده می‌کند
# Linux/macOS:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# kill کردن process
kill -9 <PID>  # Linux/macOS
taskkill /F /PID <PID>  # Windows
```

### مشکل وابستگی‌های Python

```bash
# پاک کردن و نصب مجدد
pip uninstall -y -r <(pip freeze)
pip install -e ".[dev]"
```

### مشکل node_modules

```bash
cd web

# پاک کردن و نصب مجدد
rm -rf node_modules package-lock.json
npm install
```

### مشکل Docker

```bash
# پاک کردن همه چیز و شروع دوباره
docker compose down -v
docker system prune -a
docker compose up -d --build
```

## متغیرهای محیطی

### Backend (.env)

```bash
# Application
APP_NAME=Farda MCP
APP_VERSION=0.1.0
APP_ENV=local  # local | ci | prod

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/farda_mcp

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
# CORS_ORIGINS=["http://localhost:3000"]
```

### Web (.env.local)

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application
NEXT_PUBLIC_APP_NAME=Farda MCP
NEXT_PUBLIC_APP_VERSION=0.1.0
```

## استفاده از DataSource (پرامپت ۳)

### ایجاد DataSource از طریق API

```bash
# ورود و دریافت توکن
curl -X POST http://localhost:8000/auth/dev/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "org_name": "Acme Corp"
  }'

# ذخیره توکن
export TOKEN="your-jwt-token-here"

# ایجاد PostgreSQL DataSource
curl -X POST http://localhost:8000/api/orgs/{org_id}/datasources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production DB",
    "type": "POSTGRES",
    "host": "db.example.com",
    "port": 5432,
    "database": "mydb",
    "username": "dbuser",
    "password": "secret123"
  }'

# تست اتصال
curl -X POST http://localhost:8000/api/orgs/{org_id}/datasources/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "POSTGRES",
    "host": "db.example.com",
    "port": 5432,
    "database": "mydb",
    "username": "dbuser",
    "password": "secret123"
  }'

# لیست DataSource‌ها
curl -X GET http://localhost:8000/api/orgs/{org_id}/datasources/ \
  -H "Authorization: Bearer $TOKEN"
```

### ایجاد REST DataSource

```bash
# ایجاد REST API DataSource با API Key
curl -X POST http://localhost:8000/api/orgs/{org_id}/datasources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "External API",
    "type": "REST",
    "base_url": "https://api.example.com",
    "auth_type": "API_KEY",
    "api_key": "secret-api-key-123",
    "headers": {
      "X-Custom-Header": "value"
    }
  }'
```

### استفاده از UI

1. وارد داشبورد شوید: http://localhost:3000/dashboard
2. به بخش "منابع داده" بروید: http://localhost:3000/dashboard/datasources
3. روی "منبع داده جدید +" کلیک کنید
4. فرم را پر کنید و "تست اتصال" را بزنید
5. در صورت موفقیت، "ایجاد منبع داده" را بزنید

**نکته**: فیلدهای حساس (رمز عبور، API Key) به صورت امن با Envelope Encryption ذخیره می‌شوند و در UI ماسک شده نمایش داده می‌شوند (`•••••`).

## مراحل بعدی

پس از راه‌اندازی موفق:

1. مطالعه [معماری سیستم](./architecture.md)
2. مطالعه [اصول امنیتی](./security.md)
3. مطالعه [تصمیمات معماری](./decisions.md)
4. آزمایش مدیریت DataSource و تست اتصال

## دریافت کمک

در صورت مواجه با مشکل:

1. بررسی [Issues در GitHub](https://github.com/your-org/farda-mcp/issues)
2. ایجاد issue جدید با جزئیات کامل
3. مراجعه به مستندات backend و web در پوشه‌های مربوطه

---

**نکته**: این یک نسخه MVP است. ویژگی‌های بیشتر در پرامپت‌های بعدی اضافه خواهد شد.

## سناریوی نمونه: ساخت Tool و اجرای Invoke

### مرحله ۱: ساخت DataSource

```bash
curl -X POST http://localhost:8080/api/orgs/{org_id}/datasources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Patient DB",
    "type": "POSTGRES",
    "host": "localhost",
    "port": 5432,
    "database": "hospital",
    "username": "readonly",
    "password": "secure_password",
    "schema_version": "v1"
  }'
```

### مرحله ۲: ساخت Tool با Query Template

```bash
curl -X POST http://localhost:8080/api/orgs/{org_id}/tools/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_patient_by_id",
    "version": "v1",
    "type": "POSTGRES_QUERY",
    "datasource_id": "{datasource_id}",
    "input_schema": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"}
      },
      "required": ["id"]
    },
    "output_schema": {
      "type": "array"
    },
    "exec_config": {
      "query_template": "SELECT id, name, age FROM patients WHERE id = %(id)s"
    },
    "rate_limit_per_min": 100,
    "enabled": true
  }'
```

### مرحله ۳: ایجاد Policy (اختیاری)

```bash
# Policy برای Masking فیلدهای حساس
curl -X POST http://localhost:8080/api/orgs/{org_id}/policies/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mask SSN for Developers",
    "effect": "ALLOW",
    "resource_type": "TOOL",
    "resource_id": "{tool_id}",
    "conditions": {
      "roles_any_of": ["DEVELOPER"]
    },
    "field_masks": {
      "remove": ["ssn", "national_id"]
    },
    "enabled": true
  }'
```

### مرحله ۴: تست Tool Invoke

```bash
curl -X POST http://localhost:8080/api/orgs/{org_id}/tools/{tool_id}/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "id": 123
    }
  }'
```

**پاسخ موفق**:
```json
{
  "ok": true,
  "data": [
    {
      "id": 123,
      "name": "John Doe",
      "age": 45
    }
  ],
  "masked": false,
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "error": null
}
```

**پاسخ با Field Masking**:
```json
{
  "ok": true,
  "data": [
    {
      "id": 123,
      "name": "John Doe",
      "age": 45
      // "ssn" removed by policy
    }
  ],
  "masked": true,
  "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "error": null
}
```

### مرحله ۵: مشاهده Metrics

```bash
curl http://localhost:8080/api/orgs/{org_id}/tools/{tool_id}/metrics \
  -H "Authorization: Bearer $TOKEN"
```

