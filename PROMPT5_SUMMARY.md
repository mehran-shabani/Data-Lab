# خلاصه پرامپت ۵: گسترش Connectors + Resilience + Monitoring

## ✅ تکمیل شده

### Backend (FastAPI)

#### ۱. وابستگی‌ها
- ✅ افزودن `motor>=3.3.0` برای MongoDB
- ✅ افزودن `boto3>=1.34.0` برای S3/MinIO
- ✅ GraphQL از همان `httpx` استفاده می‌کند

#### ۲. گسترش مدل و اسکیماها
- ✅ اضافه شدن `MONGODB`, `GRAPHQL`, `S3` به `DataSourceType` enum
- ✅ اسکیماهای Create/Update/TestCheck برای انواع جدید
- ✅ اعتبارسنجی کامل با Pydantic validators
- ✅ Migration برای اضافه کردن enum values جدید

#### ۳. لایه انتزاع کانکتور
**فایل‌های جدید:**
- `backend/apps/connectors/base.py` - Interface انتزاعی Connector
- `backend/apps/connectors/registry.py` - ثبت و ساخت کانکتورها
- `backend/apps/connectors/resilience.py` - Retry/Backoff/Circuit-Breaker
- `backend/apps/connectors/metrics.py` - سیستم متریک‌ها
- `backend/apps/connectors/impl_postgres.py` - کانکتور PostgreSQL
- `backend/apps/connectors/impl_rest.py` - کانکتور REST
- `backend/apps/connectors/impl_mongodb.py` - کانکتور MongoDB (جدید)
- `backend/apps/connectors/impl_graphql.py` - کانکتور GraphQL (جدید)
- `backend/apps/connectors/impl_s3.py` - کانکتور S3/MinIO (جدید)

**Base Interface:**
```python
class Connector(ABC):
    async def ping() -> tuple[bool, str]
    async def sample(params: dict) -> Any
    async def close() -> None
```

#### ۴. Resilience Patterns
**Retry with Exponential Backoff:**
- پارامترهای پیش‌فرض: `retries=2, base_ms=250, max_ms=2000`
- فقط برای خطاهای transient (network, timeout)
- دکوراتور `@with_retry` برای استفاده آسان

**Circuit Breaker:**
- States: `CLOSED` → `OPEN` → `HALF_OPEN` → `CLOSED`
- پارامترهای پیش‌فرض: `failure_threshold=5, timeout_seconds=30`
- ذخیره‌سازی state در حافظه (per DataSource)
- پیام فارسی برای OPEN state: "اتصال موقتاً تعلیق شد؛ چند ثانیه دیگر تلاش کنید."

#### ۵. Metrics & Monitoring
**متریک‌های DataSource:**
- `calls_total`: تعداد کل فراخوانی‌ها
- `errors_total`: تعداد خطاها
- `avg_latency_ms`: میانگین تأخیر (EMA)
- `p95_ms`: تأخیر P95 (تقریبی)
- `last_ok_ts`: آخرین اتصال موفق
- `last_err_ts`: آخرین خطا
- `state`: وضعیت Circuit Breaker

**Endpoints جدید:**
- `GET /orgs/{org_id}/datasources/{ds_id}/metrics`
- `GET /orgs/{org_id}/datasources/health`
- `POST /orgs/{org_id}/datasources/{ds_id}/ping`
- `POST /orgs/{org_id}/datasources/{ds_id}/sample`

#### ۶. Service & Router
- ✅ بروزرسانی `DataSourceService` برای استفاده از کانکتورها
- ✅ گسترش `router.py` با endpoint های جدید
- ✅ ادغام Metrics و Circuit Breaker
- ✅ پشتیبانی از تمام انواع جدید DataSource

#### ۷. تست‌ها (۴۰ تست سبز ✅)
- ✅ `test_connectors_registry.py` (۷ تست)
- ✅ `test_connectors_resilience.py` (۱۲ تست)
- ✅ `test_connectors_metrics.py` (۱۱ تست)
- ✅ `test_connectors_integration.py` (۱۰ تست با Mock)

### Frontend (Next.js)

#### ۱. API Client
**فایل: `web/lib/api.ts`**
- ✅ افزودن types برای MongoDB, GraphQL, S3
- ✅ توابع جدید:
  - `pingDataSource(orgId, dsId)`
  - `sampleDataSource(orgId, dsId, params)`
  - `getDataSourceMetrics(orgId, dsId)`
  - `getDataSourcesHealth(orgId)`

#### ۲. ویزارد سه مرحله‌ای
**فایل: `web/app/dashboard/datasources/new/page.tsx`**
- ✅ مرحله ۱: انتخاب نوع (با آیکون و توضیحات)
- ✅ مرحله ۲: واردکردن تنظیمات (فرم داینامیک)
- ✅ مرحله ۳: تست اتصال + ایجاد
- ✅ Progress indicator
- ✅ نمایش خلاصه تنظیمات
- ✅ هشدار امنیتی

#### ۳. صفحه جزییات DataSource
**فایل: `web/app/dashboard/datasources/[id]/page.tsx`**
- ✅ تب Overview: اطلاعات پایه + وضعیت اتصال
- ✅ تب Metrics: نمایش تمام متریک‌ها
- ✅ تب Playground: اجرای Sample با پارامترهای JSON
- ✅ دکمه Ping
- ✅ نمایش Circuit Breaker state
- ✅ Placeholder های مناسب برای هر نوع

#### ۴. بهبود لیست DataSource
**فایل: `web/app/dashboard/datasources/page.tsx`**
- ✅ ستون وضعیت با Badge رنگی (سالم/خطا/نامشخص)
- ✅ ستون "آخرین OK" با فرمت تاریخ فارسی
- ✅ دکمه "بررسی سلامت همه" (Ping All)
- ✅ نمایش state تعلیق (OPEN) در صورت وجود
- ✅ رنگ‌های مختلف برای انواع DataSource

### مستندات

#### ۱. Architecture.md
- ✅ بخش "Connector Abstraction & Registry"
- ✅ نمودار Mermaid برای جریان Circuit Breaker
- ✅ توضیح Resilience Patterns
- ✅ لیست Metrics و Endpoints

#### ۲. Security.md
- ✅ سیاست Timeout برای هر نوع کانکتور
- ✅ پارامترهای Circuit Breaker
- ✅ محدودیت‌های Sample/Playground
- ✅ خطرات و راهکارها

#### ۳. Getting-Started.md
- ✅ مثال‌های استفاده از MongoDB
- ✅ مثال‌های استفاده از GraphQL
- ✅ مثال‌های استفاده از S3/MinIO
- ✅ دستورات Ping و Metrics
- ✅ توضیح Circuit Breaker States

#### ۴. Decisions.md (ADR-0004)
- ✅ تصمیم: لایه انتزاع کانکتور + Resilience Patterns
- ✅ گزینه‌های بررسی شده
- ✅ پیامدهای مثبت و منفی
- ✅ محدودیت‌های MVP

## 📊 آمار

- **Backend:**
  - ۹ فایل جدید در `apps/connectors/`
  - ۴ فایل تست جدید
  - ۴۰ تست سبز
  - ~۱۵۰۰ خط کد جدید

- **Frontend:**
  - ۳ صفحه بازنویسی/ایجاد شده
  - ۱ فایل API client بروزرسانی
  - ~۱۰۰۰ خط کد جدید
  - پشتیبانی کامل RTL

- **مستندات:**
  - ۴ فایل بروزرسانی شده
  - ۱ ADR جدید

## 🎯 معیارهای پذیرش (تکمیل ۱۰۰%)

- ✅ پشتیبانی از MONGODB، GRAPHQL، S3
- ✅ Ping/Sample برای همه انواع (با Mock در CI)
- ✅ Retry/Backoff بر خطاهای شبکه‌ای
- ✅ Circuit-Breaker با پیام 503 استاندارد
- ✅ Metrics سطح DataSource با 7 فیلد
- ✅ Health summary سازمانی
- ✅ UI ویزارد سه مرحله‌ای
- ✅ UI صفحه جزییات با ۳ تب
- ✅ عدم نشت اسرار (ماسک در UI، لاگ‌ها)
- ✅ تست‌ها سبز (۴۰ تست کانکتورها)

## 🔒 امنیت

- ✅ Connection configs رمزشده با Envelope Encryption
- ✅ هیچ credential در API responses نمایش داده نمی‌شود
- ✅ فیلدهای password در UI ماسک شده
- ✅ Timeouts برای جلوگیری از hang
- ✅ Circuit Breaker برای جلوگیری از DoS
- ✅ محدودیت Sample (max items، no dangerous operations)

## 🚀 نحوه استفاده

```bash
# Backend
cd backend
pip install -e ".[dev]"
pytest tests/test_connectors_*.py  # 40 تست سبز

# Web
cd web
npm install
npm run dev

# Compose
cd ops/compose
docker compose up -d --build
```

## 📝 نکات مهم

1. **Circuit Breaker State در حافظه است** - در restart از بین می‌رود (V1: Redis)
2. **Metrics در حافظه است** - در restart reset می‌شود (V1: TimescaleDB)
3. **Sample/Playground محدودیت‌های MVP دارد** - Query whitelisting در V1
4. **تست‌های قدیمی User model** - نیاز به بروزرسانی `hashed_password` → `password_hash`

## 🎉 نتیجه

پرامپت ۵ با موفقیت کامل شد:
- ✅ ۵ نوع DataSource (Postgres, REST, MongoDB, GraphQL, S3)
- ✅ لایه انتزاع کامل و قابل گسترش
- ✅ Resilience Patterns کامل (Retry/Backoff/Circuit-Breaker)
- ✅ Monitoring و Metrics در سطح DataSource
- ✅ UI ویزارد و صفحات مانیتورینگ
- ✅ مستندات جامع
- ✅ تست‌های سبز

سیستم آماده برای پرامپت‌های بعدی است! 🚀
