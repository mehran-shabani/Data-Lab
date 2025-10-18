# تصمیمات معماری (Architecture Decision Records)

این سند تصمیمات معماری کلیدی پروژه Farda MCP را ثبت می‌کند.

## ADR-0001: انتخاب FastAPI برای Backend

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به یک فریم‌ورک Python مدرن برای ساخت REST API با پشتیبانی از:
* Async/await برای عملکرد بالا
* Type hints و validation خودکار
* مستندات خودکار
* پشتیبانی از استانداردهای مدرن (OpenAPI, JSON Schema)

### گزینه‌های بررسی شده

1. **FastAPI** ⭐
   * ✅ Async/await native
   * ✅ Pydantic integration
   * ✅ مستندات خودکار (Swagger/ReDoc)
   * ✅ عملکرد بسیار بالا
   * ✅ جامعه فعال

2. **Django + DRF**
   * ✅ Mature و battle-tested
   * ✅ Admin panel داخلی
   * ❌ Sync by default
   * ❌ Overhead بیشتر
   * ❌ کمتر مناسب برای API-only

3. **Flask**
   * ✅ سبک و انعطاف‌پذیر
   * ❌ بدون validation داخلی
   * ❌ بدون async native
   * ❌ نیاز به extension های زیاد

### تصمیم

**FastAPI** به دلایل زیر انتخاب شد:
* عملکرد بالا برای چندمستأجری
* Type safety با Python type hints
* Async برای scalability
* مستندات تعاملی خودکار
* مناسب برای microservices (آینده)

### پیامدها

* **مثبت**:
  * کد تمیزتر با type hints
  * Performance بهتر با async
  * مستندات همیشه به‌روز
  * توسعه سریع‌تر

* **منفی**:
  * نیاز به یادگیری async patterns
  * کمتر mature از Django
  * کمتر از منابع/آموزش‌های فارسی

### منابع

* https://fastapi.tiangolo.com/
* https://www.techempower.com/benchmarks/

---

## ADR-0002: انتخاب Next.js 15 برای Frontend

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به یک فریم‌ورک React مدرن با:
* Server-side rendering (SSR)
* پشتیبانی عالی از RTL
* Performance بالا
* Developer experience خوب

### گزینه‌های بررسی شده

1. **Next.js 15** ⭐
   * ✅ App Router با React Server Components
   * ✅ SSR و SSG خودکار
   * ✅ API Routes (BFF pattern)
   * ✅ Built-in optimization
   * ✅ پشتیبانی RTL

2. **Remix**
   * ✅ Nested routing عالی
   * ✅ Data loading patterns خوب
   * ❌ جامعه کوچک‌تر
   * ❌ کمتر mature

3. **Create React App**
   * ✅ ساده
   * ❌ فقط client-side
   * ❌ نیاز به setup زیاد
   * ❌ deprecated

4. **Vite + React**
   * ✅ بسیار سریع در development
   * ✅ سبک و انعطاف‌پذیر
   * ❌ بدون SSR خودکار
   * ❌ نیاز به configuration بیشتر

### تصمیم

**Next.js 15** با App Router به دلایل زیر:
* React 19 و Server Components
* پشتیبانی عالی از i18n و RTL
* SEO-friendly با SSR
* Vercel ecosystem
* مناسب برای MVP تا Enterprise

### پیامدها

* **مثبت**:
  * Performance عالی با RSC
  * SEO بدون تلاش اضافی
  * Deployment آسان (Vercel/Docker)
  * جامعه بزرگ فارسی‌زبان

* **منفی**:
  * Learning curve برای App Router
  * تغییرات مکرر در Next.js
  * Bundle size بزرگ‌تر از alternatives

### منابع

* https://nextjs.org/docs
* https://react.dev/blog/2024/04/25/react-19

---

## ADR-0003: معماری مونو‌ریپو

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

تصمیم‌گیری بین monorepo و multi-repo برای سازماندهی کد.

### گزینه‌های بررسی شده

1. **Monorepo** ⭐
   * ✅ همگام‌سازی آسان changes
   * ✅ code sharing ساده
   * ✅ refactoring آسان‌تر
   * ✅ یک CI/CD pipeline
   * ❌ repo بزرگ‌تر

2. **Multi-repo**
   * ✅ جداسازی کامل
   * ✅ ownership مشخص‌تر
   * ❌ همگام‌سازی سخت
   * ❌ code duplication
   * ❌ چندین CI/CD

### تصمیم

**Monorepo** برای این MVP چون:
* تیم کوچک
* نیاز به refactoring مکرر
* همگام‌سازی API contracts
* یک product واحد

در آینده اگر تیم بزرگ شد، می‌توان به multi-repo مهاجرت کرد.

### ساختار

```
farda-mcp/
  backend/    # Python/FastAPI
  web/        # Next.js
  docs/       # Documentation
  ops/        # Docker/K8s
```

### پیامدها

* **مثبت**:
  * Atomic commits برای backend+frontend
  * یک version برای کل product
  * CI/CD ساده‌تر

* **منفی**:
  * نیاز به workspace tooling
  * احتمال conflict های بیشتر
  * clone time طولانی‌تر

---

## ADR-0004: PostgreSQL برای دیتابیس اصلی

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به دیتابیس relational با پشتیبانی از:
* ACID transactions
* JSONB برای flexibility
* Full-text search
* Row-level security (multi-tenancy)

### گزینه‌های بررسی شده

1. **PostgreSQL 16** ⭐
   * ✅ ACID کامل
   * ✅ JSONB عالی
   * ✅ Extensions غنی
   * ✅ Row-level security
   * ✅ شناخته شده

2. **MySQL**
   * ✅ عملکرد خوب برای read-heavy
   * ❌ JSON support ضعیف‌تر
   * ❌ کمتر extensible

3. **MongoDB**
   * ✅ Schema flexibility
   * ❌ بدون ACID کامل (پیش از 4.0)
   * ❌ کمتر مناسب برای relations

### تصمیم

**PostgreSQL 16** به دلایل:
* نیاز به ACID برای multi-tenancy
* JSONB برای flexible schemas
* RLS برای tenant isolation
* Full ecosystem (pgAdmin, timescaleDB, etc.)

### پیامدها

* **مثبت**:
  * Data integrity تضمین شده
  * Flexibility با JSONB
  * ابزارهای مدیریتی زیاد

* **منفی**:
  * پیچیده‌تر از NoSQL
  * نیاز به schema migrations
  * عملکرد write کمتر از NoSQL

---

## ADR-0005: SQLAlchemy 2.0 + Alembic

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به ORM و migration tool برای Python.

### گزینه‌های بررسی شده

1. **SQLAlchemy 2.0 + Alembic** ⭐
   * ✅ Async support
   * ✅ Type hints support
   * ✅ Mature و قدرتمند
   * ✅ Alembic عالی برای migrations

2. **Django ORM**
   * ✅ ساده‌تر
   * ❌ نیاز به Django
   * ❌ کمتر flexible

3. **Tortoise ORM**
   * ✅ Async-first
   * ✅ Django-like API
   * ❌ کمتر mature
   * ❌ جامعه کوچک

### تصمیم

**SQLAlchemy 2.0** چون:
* Async/await native
* قدرتمندترین ORM Python
* Alembic برای version control
* پشتیبانی عالی از type hints

---

## ADR-0006: Docker Compose برای توسعه محلی

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به راه‌اندازی آسان محیط توسعه.

### گزینه‌های بررسی شده

1. **Docker Compose** ⭐
   * ✅ یک دستور برای setup
   * ✅ همه چیز isolated
   * ✅ قابل استفاده در CI

2. **Manual Setup**
   * ✅ کنترل کامل
   * ❌ setup پیچیده
   * ❌ inconsistent بین developers

3. **Kubernetes (Kind/Minikube)**
   * ✅ نزدیک به production
   * ❌ overhead زیاد برای local
   * ❌ پیچیده برای MVP

### تصمیم

**Docker Compose** برای local dev و **Kubernetes** برای production (پرامپت‌های بعدی).

### پیامدها

* **مثبت**:
  * Onboarding سریع
  * Consistency بین developers
  * آماده برای CI/CD

* **منفی**:
  * نیاز به Docker
  * کمی کندتر از native

---

## ADR-0007: GitHub Actions برای CI/CD

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به CI/CD pipeline برای lint, test, build.

### گزینه‌های بررسی شده

1. **GitHub Actions** ⭐
   * ✅ Integration عالی با GitHub
   * ✅ رایگان برای public repos
   * ✅ marketplace بزرگ
   * ✅ matrix builds

2. **GitLab CI**
   * ✅ قدرتمند
   * ❌ نیاز به GitLab

3. **Jenkins**
   * ✅ بسیار flexible
   * ❌ نیاز به infrastructure
   * ❌ setup پیچیده

### تصمیم

**GitHub Actions** چون:
* استفاده از GitHub
* رایگان و ساده
* مناسب برای monorepo

---

## ADR-0008: Pydantic v2 برای Validation

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

نیاز به data validation و serialization.

### تصمیم

**Pydantic v2** چون:
* Integration عالی با FastAPI
* Performance بالا (Rust core)
* Type safety با Python type hints
* JSON Schema generation

### پیامدها

کد تمیزتر، سریع‌تر و امن‌تر.

---

## ADR-0009: TypeScript Strict Mode

**تاریخ**: 2025-10-18

**وضعیت**: پذیرفته شده ✅

### زمینه

تصمیم بین JavaScript و TypeScript.

### تصمیم

**TypeScript با strict mode** چون:
* Type safety در compile time
* بهتر برای refactoring
* IDE support عالی
* کمتر bug در runtime

### Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true
  }
}
```

---

## Template برای ADR های آینده

```markdown
## ADR-XXXX: عنوان تصمیم

**تاریخ**: YYYY-MM-DD

**وضعیت**: پیشنهادی | پذیرفته شده | رد شده | منسوخ شده

### زمینه
توضیح مسئله و نیازها

### گزینه‌های بررسی شده
1. گزینه ۱
2. گزینه ۲
3. ...

### تصمیم
گزینه انتخاب شده و دلیل

### پیامدها
* مثبت: ...
* منفی: ...

### منابع
* لینک ۱
* لینک ۲
```

---

## یادداشت نهایی

این تصمیمات برای **MVP فعلی** گرفته شده‌اند و ممکن است در آینده با رشد پروژه تغییر کنند. هر تغییری باید با ADR جدید مستند شود.
