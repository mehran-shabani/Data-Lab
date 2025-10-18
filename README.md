# Farda MCP

سامانه مدیریت چندمستأجری با پروتکل MCP - یک پلتفرم مدرن، امن و مقیاس‌پذیر برای مدیریت چندین تنانت با معماری مونو‌ریپو.

[![CI](https://github.com/your-org/farda-mcp/workflows/CI/badge.svg)](https://github.com/your-org/farda-mcp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 ویژگی‌ها

* **🏗️ معماری مونو‌ریپو**: Backend (FastAPI) و Frontend (Next.js) در یک مخزن
* **⚡ عملکرد بالا**: Async/await در backend، Server Components در frontend
* **🔒 امنیت پیشرفته**: احراز هویت چندلایه، RBAC، چندمستأجری امن (پرامپت ۲)
* **🌐 پشتیبانی کامل RTL**: رابط کاربری فارسی با تقویم جلالی
* **🐳 Docker-ready**: راه‌اندازی آسان با Docker Compose
* **✅ CI/CD**: GitHub Actions برای lint, test, build خودکار
* **📚 مستندسازی کامل**: اسناد فارسی جامع و به‌روز

## 📋 پیش‌نیازها

### برای اجرای محلی:
* Python 3.11+
* Node.js 20+
* PostgreSQL 16+

### برای اجرای کانتینری (توصیه می‌شود):
* Docker 24+
* Docker Compose v2+

## 🏃 شروع سریع

### با Docker Compose (راه حل توصیه شده)

```bash
# کلون مخزن
git clone https://github.com/your-org/farda-mcp.git
cd farda-mcp

# تنظیم متغیرهای محیطی
cd ops/compose
cp .env.example .env

# اجرای سرویس‌ها
docker compose up -d --build

# مشاهده لاگ‌ها
docker compose logs -f
```

سرویس‌ها در دسترس:
* **Web**: http://localhost:8080
* **API**: http://localhost:8080/api/healthz
* **API Docs**: http://localhost:8080/docs

### اجرای محلی (بدون Docker)

#### Backend

```bash
cd backend

# ایجاد و فعال‌سازی محیط مجازی
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# یا: .venv\Scripts\activate  # Windows

# نصب وابستگی‌ها
pip install -e ".[dev]"

# تنظیم متغیرها
cp .env.example .env

# اجرای سرور
uvicorn apps.core:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd web

# نصب وابستگی‌ها
npm install

# تنظیم متغیرها
cp .env.example .env.local

# اجرای سرور توسعه
npm run dev
```

## 📁 ساختار پروژه

```
farda-mcp/
├── backend/              # FastAPI backend
│   ├── apps/
│   │   ├── core/        # ماژول اصلی
│   │   ├── mcp/         # پروتکل MCP (رزرو شده)
│   │   └── connectors/  # کانکتورها (رزرو شده)
│   ├── tests/           # تست‌ها
│   └── alembic/         # Database migrations
├── web/                 # Next.js frontend
│   ├── app/             # App Router
│   ├── components/      # کامپوننت‌ها
│   └── lib/             # Utilities
├── docs/                # مستندات فارسی
├── ops/                 # DevOps configs
│   ├── docker/          # Dockerfiles
│   └── compose/         # Docker Compose
└── .github/
    └── workflows/       # CI/CD pipelines
```

## 🧪 تست

### Backend

```bash
cd backend
source .venv/bin/activate
pytest
```

### Frontend

```bash
cd web
npm run test
npm run typecheck
npm run lint
```

### همه تست‌ها (در CI)

```bash
# توسط GitHub Actions اجرا می‌شود
# می‌توانید به‌صورت دستی نیز اجرا کنید:
cd backend && pytest && cd ../web && npm run test
```

## 📚 مستندات

* [معماری سیستم](./docs/architecture.md) - نمای کلی معماری و جریان داده
* [راهنمای شروع](./docs/getting-started.md) - راه‌اندازی قدم‌به‌قدم
* [امنیت](./docs/security.md) - اصول و بهترین شیوه‌های امنیتی
* [تصمیمات معماری](./docs/decisions.md) - ADR های پروژه
* [Backend README](./backend/README.md) - مستندات backend
* [Web README](./web/README.md) - مستندات frontend

## 🛠️ تکنولوژی‌ها

### Backend
* **FastAPI** - فریم‌ورک وب مدرن و سریع
* **SQLAlchemy 2** - ORM قدرتمند با پشتیبانی async
* **Pydantic v2** - اعتبارسنجی داده با type hints
* **PostgreSQL 16** - دیتابیس relational
* **Alembic** - مدیریت migration ها

### Frontend
* **Next.js 15** - فریم‌ورک React با App Router
* **React 19** - با Server Components
* **TypeScript** - Type safety
* **Tailwind CSS** - Utility-first CSS
* **Vazirmatn** - فونت فارسی زیبا

### DevOps
* **Docker** - کانتینرسازی
* **Docker Compose** - Orchestration محلی
* **Nginx** - Reverse proxy
* **GitHub Actions** - CI/CD

## 🔄 CI/CD

پروژه از GitHub Actions برای CI/CD استفاده می‌کند:

* ✅ Lint (ruff برای Python, eslint برای TypeScript)
* ✅ Type check (mypy, tsc)
* ✅ Tests (pytest, jest)
* ✅ Docker build
* 🔜 Deployment (پرامپت‌های بعدی)

## 🗺️ نقشه راه

### ✅ فاز ۱: اسکلت و اسناد (فعلی)
* [x] ساختار مونو‌ریپو
* [x] Backend FastAPI
* [x] Frontend Next.js با RTL
* [x] Docker و CI
* [x] مستندات فارسی

### 🔜 فاز ۲: احراز هویت و چندمستأجری (پرامپت بعدی)
* [ ] JWT/OIDC authentication
* [ ] RBAC (نقش‌ها و دسترسی‌ها)
* [ ] مدیریت چندمستأجری
* [ ] جداسازی داده‌های تنانت‌ها

### 🔜 فاز ۳: پروتکل MCP
* [ ] پیاده‌سازی MCP server
* [ ] کانکتورهای خارجی
* [ ] مدیریت context

### 🔜 فاز ۴: پیشرفته
* [ ] Redis caching
* [ ] Background jobs
* [ ] Real-time notifications
* [ ] Audit logging
* [ ] Monitoring و Observability

## 🤝 مشارکت

مشارکت‌ها خوش‌آمد هستند! لطفاً:

1. Fork کنید
2. یک branch ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات خود را commit کنید (`git commit -m 'Add amazing feature'`)
4. به branch خود push کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request باز کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است - فایل [LICENSE](LICENSE) را برای جزئیات مشاهده کنید.

## 👥 نویسندگان

* **تیم توسعه Farda MCP** - توسعه و نگهداری

## 🙏 تشکر

* [FastAPI](https://fastapi.tiangolo.com/)
* [Next.js](https://nextjs.org/)
* [Model Context Protocol](https://modelcontextprotocol.io/)
* جامعه متن‌باز

---

**نسخه**: 0.1.0 (MVP)  
**وضعیت**: 🚧 در حال توسعه  
**آخرین به‌روزرسانی**: 2025-10-18
