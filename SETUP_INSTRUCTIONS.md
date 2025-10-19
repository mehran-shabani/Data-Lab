# دستورالعمل راه‌اندازی - Farda MCP Manager

این سند دستورالعمل راه‌اندازی کامل پروژه Farda MCP با MCP Manager را شرح می‌دهد.

## پیش‌نیازها

- Python 3.11+
- Node.js 18+
- PostgreSQL 16
- Docker & Docker Compose (اختیاری)

---

## روش ۱: راه‌اندازی دستی (Development)

### مرحله ۱: Backend Setup

```bash
cd backend

# ایجاد محیط مجازی
python3 -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate

# نصب وابستگی‌ها
pip install -e .[dev]

# تنظیم متغیرهای محیطی
export APP_ENV=local
export APP_NAME="Farda MCP Backend"
export APP_VERSION="0.1.0"
export AUTH_SECRET="your-32-char-secret-key-here"
export SECRETS_MASTER_KEY="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
export DATABASE_URL="postgresql://postgres:password@localhost:5432/farda_mcp"
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# ایجاد دیتابیس
createdb farda_mcp

# اجرای migrations
alembic upgrade head

# اجرای تست‌ها
pytest -v

# راه‌اندازی سرور
uvicorn apps.core:app --host 0.0.0.0 --port 8000 --reload
```

### مرحله ۲: Frontend Setup

```bash
cd web

# نصب وابستگی‌ها
npm install

# تنظیم متغیرهای محیطی
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api' > .env.local

# راه‌اندازی dev server
npm run dev
```

دسترسی به UI: http://localhost:3000

---

## روش ۲: راه‌اندازی با Docker Compose (توصیه می‌شود)

```bash
cd ops/compose

# کپی فایل env نمونه
cp .env.example .env

# ویرایش .env و تنظیم متغیرها:
# - AUTH_SECRET (32 کاراکتر)
# - SECRETS_MASTER_KEY (64 کاراکتر hex)
# - DB_PASSWORD

# بیلد و اجرا
docker compose up -d --build

# بررسی لاگ‌ها
docker compose logs -f

# اجرای migrations
docker compose exec backend alembic upgrade head

# اجرای تست‌ها
docker compose exec backend pytest -v
```

دسترسی:
- Frontend: http://localhost:8080
- Backend API: http://localhost:8080/api
- Docs: http://localhost:8080/docs (فقط non-prod)

---

## مرحله ۳: داده‌های اولیه (Seed Data)

### ایجاد سازمان و کاربر نمونه

```bash
# از طریق API
curl -X POST http://localhost:8000/auth/dev/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "org_name": "Demo Organization"
  }'

# پاسخ شامل token است - آن را ذخیره کنید
export TOKEN="eyJ..."
```

### ساخت DataSource نمونه

```bash
curl -X POST http://localhost:8080/api/orgs/{org_id}/datasources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Postgres",
    "type": "POSTGRES",
    "host": "localhost",
    "port": 5432,
    "database": "demo",
    "username": "demo_user",
    "password": "demo_pass",
    "schema_version": "v1"
  }'
```

### ساخت Tool نمونه

```bash
curl -X POST http://localhost:8080/api/orgs/{org_id}/tools/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Get User by ID",
    "type": "POSTGRES_QUERY",
    "datasource_id": "{datasource_id}",
    "input_schema": {
      "type": "object",
      "properties": {"id": {"type": "integer"}},
      "required": ["id"]
    },
    "exec_config": {
      "query_template": "SELECT id, name, email FROM users WHERE id = %(id)s"
    },
    "rate_limit_per_min": 100,
    "enabled": true
  }'
```

---

## مرحله ۴: تست عملکرد

### تست Tool Invoke

```bash
# از طریق API
curl -X POST http://localhost:8080/api/orgs/{org_id}/tools/{tool_id}/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"params": {"id": 1}}'

# یا از طریق UI
# رفتن به: http://localhost:3000/dashboard/tools/{tool_id}/test
```

### تست MCP Server

```bash
# ساخت MCP Server
curl -X POST http://localhost:8080/api/orgs/{org_id}/mcp/servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test MCP Server"}'

# پاسخ شامل plain_api_key است - فقط یکبار نمایش داده می‌شود!
```

---

## اجرای تست‌ها

### Backend Tests

```bash
cd backend

# اجرای همه تست‌ها
pytest -v

# فقط تست‌های MCP
pytest tests/test_mcp*.py -v

# با coverage
pytest --cov=apps.mcp --cov-report=html
```

### Frontend Tests (اگر موجود باشد)

```bash
cd web
npm test
npm run lint
npm run typecheck
```

---

## عیب‌یابی رایج

### مشکل: ModuleNotFoundError

**راه‌حل**: نصب dependencies
```bash
cd backend
pip install -e .[dev]
```

### مشکل: Database connection error

**راه‌حل**: بررسی DATABASE_URL و PostgreSQL
```bash
# بررسی PostgreSQL
pg_isready

# تست اتصال
psql $DATABASE_URL -c "SELECT 1"
```

### مشکل: SECRETS_MASTER_KEY invalid

**راه‌حل**: باید 64 کاراکتر hex باشد
```bash
# تولید کلید جدید
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### مشکل: CORS errors در frontend

**راه‌حل**: بررسی CORS_ORIGINS در backend
```bash
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

### مشکل: Alembic migration fails

**راه‌حل**: 
```bash
# بررسی وضعیت
alembic current

# اجرای دستی
alembic upgrade head

# در صورت conflict
alembic downgrade -1
alembic upgrade head
```

---

## نکات امنیتی

### تولید Secrets برای Production

```bash
# AUTH_SECRET (32 chars)
openssl rand -base64 32

# SECRETS_MASTER_KEY (64 chars hex)
python3 -c "import secrets; print(secrets.token_hex(32))"

# DB_PASSWORD
openssl rand -base64 24
```

### چک‌لیست امنیتی قبل از Production

- [ ] تغییر همه secret ها از مقادیر dev
- [ ] غیرفعال کردن /docs و /redoc (APP_ENV=prod)
- [ ] تنظیم CORS_ORIGINS به domain واقعی
- [ ] استفاده از HTTPS برای همه endpoint ها
- [ ] فعال‌سازی rate limiting در nginx
- [ ] بررسی و تنظیم DATABASE_URL (SSL mode)
- [ ] فعال‌سازی backup های دیتابیس
- [ ] پیکربندی monitoring (logs, metrics)

---

## منابع بیشتر

- [Architecture Documentation](./docs/architecture.md)
- [Security Documentation](./docs/security.md)
- [Getting Started Guide](./docs/getting-started.md)
- [Decision Records](./docs/decisions.md)
- [Prompt 4 Summary](./PROMPT4_SUMMARY.md)

---

## پشتیبانی

برای گزارش مشکلات یا سؤالات، به مستندات پروژه مراجعه کنید یا issue ایجاد کنید.

**نسخه**: 0.1.0 (MVP)
**تاریخ**: 2025-10-19
