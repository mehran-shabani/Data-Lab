# معماری Farda MCP

## نمای کلی

Farda MCP یک سامانه چندمستأجری (Multi-tenant) مبتنی بر پروتکل MCP است که با معماری مونو‌ریپو پیاده‌سازی شده است.

## نمودار معماری سطح‌بالا

```
┌─────────────────────────────────────────────────────────┐
│                      کاربر نهایی                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                 │
│                   پورت 8080                              │
└────────┬───────────────────────────────────────┬────────┘
         │                                       │
         │ /api/*                                │ /*
         ▼                                       ▼
┌─────────────────────┐              ┌──────────────────────┐
│   Backend (FastAPI) │              │   Web (Next.js)      │
│   پورت 8000         │              │   پورت 3000          │
│                     │              │                      │
│  • REST API         │              │  • App Router        │
│  • MCP Protocol     │              │  • RTL Support       │
│  • Authentication   │◄─────────────│  • Jalali Date       │
│  • Multi-tenancy    │   API Calls  │  • Dashboard         │
└──────────┬──────────┘              └──────────────────────┘
           │
           ▼
┌─────────────────────┐
│  PostgreSQL 16      │
│  پورت 5432          │
│                     │
│  • Tenant Data      │
│  • User Data        │
│  • Audit Logs       │
└─────────────────────┘
```

## لایه‌های معماری

### ۱. لایه ارائه (Presentation Layer)

**فرانت‌اند (Next.js 15)**
* **مسیر**: `web/`
* **مسئولیت**: رابط کاربری، تجربه کاربری، راست‌به‌چپ
* **تکنولوژی**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS

**ویژگی‌های کلیدی**:
* پشتیبانی کامل RTL
* تقویم جلالی
* Server-side rendering (SSR)
* Static generation (SSG)
* API routes برای BFF pattern

### ۲. لایه منطق تجاری (Business Logic Layer)

**بک‌اند (FastAPI)**
* **مسیر**: `backend/apps/core/`
* **مسئولیت**: منطق تجاری، پردازش داده، احراز هویت
* **تکنولوژی**: FastAPI, Pydantic v2, SQLAlchemy 2

**ماژول‌های اصلی**:
* `config.py` - مدیریت تنظیمات با Pydantic Settings
* `db.py` - مدیریت اتصال دیتابیس (Async)
* `security.py` - امنیت و رمزنگاری
* `auth.py` - احراز هویت و RBAC (رزرو شده)
* `deps.py` - وابستگی‌های مشترک
* `routers/` - API endpoints

### ۳. لایه داده (Data Layer)

**دیتابیس (PostgreSQL 16)**
* **مسیر**: سرویس `db` در Docker Compose
* **مسئولیت**: ذخیره‌سازی پایدار داده‌ها
* **تکنولوژی**: PostgreSQL 16 با Async driver (asyncpg)

**مدیریت Schema**:
* Alembic برای migration ها
* SQLAlchemy 2 ORM
* Async queries

## ماژول‌های سیستم

### Backend Modules

```
backend/
  apps/
    core/              # هسته اصلی برنامه
      models/          # مدل‌های دیتابیس (SQLAlchemy)
      schemas/         # Pydantic schemas برای validation
      routers/         # API endpoints
        health.py      # Health check و version
    mcp/              # پروتکل MCP (رزرو شده برای پرامپت بعدی)
    connectors/       # کانکتورهای خارجی (رزرو شده)
  tests/              # تست‌های واحد و یکپارچگی
  alembic/            # Database migrations
```

### Web Modules

```
web/
  app/
    (auth)/           # گروه Route برای احراز هویت
      signin/         # صفحه ورود
    dashboard/        # داشبورد اصلی
    api/              # API Routes (BFF)
      health/         # Health check
    layout.tsx        # Layout اصلی با RTL
    page.tsx          # صفحه خانه
  components/         # کامپوننت‌های قابل استفاده مجدد
  lib/                # توابع کمکی
    api.ts            # کلاینت API
    i18n.ts           # ترجمه و بین‌المللی‌سازی
    jalali.ts         # تقویم جلالی
```

## جریان داده (Data Flow)

### درخواست معمولی API

```
کاربر → Next.js (SSR/Client) → Nginx → FastAPI → PostgreSQL
                                  ↓
                            Response ← ─ ─ ─ ─ ┘
```

### احراز هویت (پرامپت ۲)

```
کاربر → صفحه Login → POST /api/auth/login → FastAPI
                                                ↓
                                          Validate credentials
                                                ↓
                                          Generate JWT Token
                                                ↓
                                          Return token ← ─ ─
                                                         ↓
کاربر ← Cookie/LocalStorage ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

## مرزبندی و جداسازی (Boundaries)

### مرزهای ماژولی

1. **Frontend ↔ Backend**: تنها از طریق REST API
2. **Backend ↔ Database**: تنها از طریق SQLAlchemy ORM
3. **Modules**: هر ماژول مسئولیت مشخص دارد (SRP)

### اصول جداسازی

* **No direct DB access from frontend**
* **No business logic in frontend** (except validation)
* **Clear API contracts** با Pydantic schemas
* **Async by default** در backend

## امنیت (Security Boundaries)

```
┌─────────────────────────────────────────┐
│          DMZ (Nginx)                    │
│  • Rate limiting                        │
│  • SSL termination                      │
│  • Header security                      │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│     Application Layer (FastAPI)         │
│  • Authentication (JWT/OIDC)            │
│  • Authorization (RBAC)                 │
│  • Input validation (Pydantic)          │
│  • SQL injection prevention (ORM)       │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│        Data Layer (PostgreSQL)          │
│  • Encrypted at rest                    │
│  • Row-level security (future)          │
│  • Audit logging                        │
└─────────────────────────────────────────┘
```

## الگوهای طراحی (Design Patterns)

### Backend

* **Repository Pattern**: جداسازی منطق دسترسی به داده
* **Dependency Injection**: با استفاده از FastAPI Depends
* **Factory Pattern**: `create_app()` برای ساخت application
* **Settings Pattern**: مدیریت تنظیمات با Pydantic

### Frontend

* **Component Composition**: کامپوننت‌های قابل استفاده مجدد
* **Server Components**: استفاده از RSC در Next.js
* **BFF Pattern**: API routes به‌عنوان Backend for Frontend
* **Layout Pattern**: استفاده از nested layouts

## مقیاس‌پذیری (Scalability)

### افقی (Horizontal)

* **Stateless backend**: قابل scale با load balancer
* **Database pooling**: اتصالات کارآمد به دیتابیس
* **Async I/O**: پشتیبانی از concurrent requests

### عمودی (Vertical)

* **Indexed queries**: برای عملکرد بهتر دیتابیس
* **Caching layers**: آماده برای Redis (پرامپت بعدی)
* **CDN ready**: فایل‌های استاتیک Next.js

## مانیتورینگ و Observability

### Logs

* **Structured logging**: JSON format
* **Log levels**: DEBUG, INFO, WARNING, ERROR
* **Request ID tracking**: برای trace کردن

### Metrics (آینده)

* **Health checks**: `/healthz` در backend و web
* **Performance metrics**: response time, throughput
* **Business metrics**: user activity, tenant usage

### Tracing (آینده)

* **Distributed tracing**: OpenTelemetry
* **Database query tracing**: SQLAlchemy events

## توسعه و تست

### محیط‌های اجرایی

1. **Local**: Docker Compose برای توسعه
2. **CI**: GitHub Actions برای تست خودکار
3. **Production**: (آینده) Kubernetes/Cloud

### استراتژی تست

* **Unit Tests**: pytest برای backend, Jest برای web
* **Integration Tests**: TestClient برای API
* **E2E Tests**: (آینده) Playwright

## محدودیت‌ها و Trade-offs

### فعلی

* **No Redis**: کش و صف در پرامپت‌های بعدی
* **Simple auth**: احراز هویت کامل در پرامپت ۲
* **Single DB**: چندمستأجری منطقی (نه فیزیکی)

### آینده

* **Add Redis**: برای caching و background jobs
* **Add message queue**: برای async processing
* **Add CDC**: برای event-driven architecture

## مراجع

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [Next.js Documentation](https://nextjs.org/docs)
* [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
* [MCP Protocol Specification](https://modelcontextprotocol.io/)
