# پرامپت ۴ - خلاصه پیاده‌سازی MCP Manager

## تاریخ: 2025-10-19

این سند خلاصه‌ای از پیاده‌سازی کامل **MCP Manager** شامل بک‌اند (FastAPI)، فرانت‌اند (Next.js)، و اسناد است.

---

## ۱. بک‌اند (FastAPI)

### 1.1 وابستگی‌ها

✅ **افزوده شد**: `limits>=3.7.0` به `backend/pyproject.toml`

### 1.2 مدل‌ها

فایل‌های ایجاد شده:

#### `backend/apps/core/models/tool.py`
- **Tool** Model با فیلدها:
  - `id`, `org_id`, `name`, `version`, `type` (POSTGRES_QUERY/REST_CALL/CUSTOM)
  - `datasource_id` (nullable FK)
  - `input_schema`, `output_schema`, `exec_config` (JSONB)
  - `rate_limit_per_min` (nullable)
  - `enabled` (boolean)
  - Timestamps و relationships

#### `backend/apps/core/models/mcp_server.py`
- **MCPServer** Model:
  - `id`, `org_id`, `name`, `status` (ENABLED/DISABLED)
  - `api_key_hash` (bcrypt hashed, LargeBinary)
  - Timestamps و relationships

#### `backend/apps/core/models/policy.py`
- **Policy** Model:
  - `id`, `org_id`, `name`, `effect` (ALLOW/DENY)
  - `resource_type` (TOOL/DATASOURCE), `resource_id`
  - `conditions` (JSONB - مثلاً role check)
  - `field_masks` (JSONB - مثلاً `{"remove": ["phone"]}`)
  - `enabled`, timestamps

### 1.3 مهاجرت‌ها

✅ **ایجاد شد**: `backend/alembic/versions/001_add_mcp_tool_policy_tables.py`
- Migrations برای tools, mcp_servers, policies
- Enums: tool_type, mcp_server_status, policy_effect, policy_resource_type
- Indexes برای org_id و composite keys

### 1.4 اسکیماهای Pydantic

✅ **ایجاد شد**: `backend/apps/core/schemas/mcp.py`

**Schemas:**
- **Tool**: `ToolCreate`, `ToolUpdate`, `ToolOut`
- **MCP Server**: `MCPServerCreate`, `MCPServerOut`, `MCPServerRotateKeyIn`
- **Policy**: `PolicyCreate`, `PolicyUpdate`, `PolicyOut`
- **Invoke**: `InvokeIn` (params dict), `InvokeOut` (ok, data, masked, trace_id, error)

### 1.5 سرویس‌ها

#### `backend/apps/mcp/ratelimit.py`
✅ **پیاده‌سازی**: Token Bucket Algorithm
- In-memory rate limiter (MVP)
- Per-tool (org_id, tool_id) bucket
- `check_rate_limit()`: بررسی و مصرف token

#### `backend/apps/mcp/service.py`
✅ **پیاده‌سازی کامل MCPService**:

**Tool Registry:**
- `create_tool()`: اعتبارسنجی exec_config، بررسی datasource
- `get_tool()`, `list_tools()`, `update_tool()`, `delete_tool()`

**MCP Server Management:**
- `create_mcp_server()`: تولید API key امن (bcrypt hash)
- `rotate_mcp_api_key()`: گردش کلید با لاگ ممیزی
- `toggle_mcp_server()`: enable/disable

**Policy Management:**
- CRUD کامل policies

**Invoke Pipeline:**
- `invoke_tool()`: pipeline کامل با مراحل:
  1. AuthZ/Org Guard
  2. بررسی Tool.enabled
  3. Policy Resolution (DENY → 403)
  4. Rate Limit (429 با پیام فارسی)
  5. Load DataSource
  6. Execute Tool (POSTGRES_QUERY/REST_CALL/CUSTOM)
  7. Field Masking
  8. Audit & Metrics (trace_id, logging)

**Execution Handlers:**
- `_execute_postgres_query()`: با psycopg parameterized queries (امن)
- `_execute_rest_call()`: با httpx
- `_execute_custom()`: echo ساده (MVP)

### 1.6 روترها

✅ **ایجاد شد**: `backend/apps/mcp/router.py`

**Tools Router** (`/orgs/{org_id}/tools`):
- POST `/` - ایجاد tool (DEVELOPER/ORG_ADMIN)
- GET `/` - لیست tools
- GET `/{tool_id}` - جزئیات tool
- PUT `/{tool_id}` - ویرایش tool
- DELETE `/{tool_id}` - حذف tool
- POST `/{tool_id}/invoke` - اجرای tool (همه کاربران با policy)

**MCP Router** (`/orgs/{org_id}/mcp`):
- POST `/servers` - ایجاد server (ORG_ADMIN فقط)
- GET `/servers` - لیست servers
- GET `/servers/{id}` - جزئیات server
- POST `/servers/{id}/rotate-key` - گردش کلید
- POST `/servers/{id}/enable` - فعال‌سازی
- POST `/servers/{id}/disable` - غیرفعال‌سازی

**Policies Router** (`/orgs/{org_id}/policies`):
- CRUD کامل (DATA_STEWARD/ORG_ADMIN)

**Integration:**
✅ روترها به `backend/apps/core/__init__.py` متصل شدند

### 1.7 تست‌ها

✅ **ایجاد شد**:

#### `backend/tests/test_mcp_tool_crud.py`
- ✅ ساخت POSTGRES_QUERY tool با query_template
- ✅ ساخت REST_CALL tool با method/path
- ✅ لیست/دریافت/ویرایش/حذف tools
- ✅ بررسی duplicate name
- ✅ بررسی exec_config validation

#### `backend/tests/test_mcp_invoke.py`
- ✅ Invoke موفق CUSTOM tool
- ✅ Policy DENY → 403
- ✅ Field masking (حذف فیلدها)
- ✅ Rate limit → 429
- ✅ Tool disabled → 403
- ✅ Tool non-existent → 404
- ✅ POSTGRES_QUERY با mock (psycopg)

#### `backend/tests/test_mcp_server_crud.py`
- ✅ ساخت MCP server (دریافت plain_api_key)
- ✅ Rotate key (دریافت کلید جدید)
- ✅ Enable/Disable server
- ✅ بررسی duplicate name
- ✅ لیست servers (بدون plain_api_key)
- ✅ نقش ORG_ADMIN الزامی

---

## ۲. فرانت‌اند (Next.js)

### 2.1 API Client

✅ **به‌روزرسانی شد**: `web/lib/api.ts`

**افزوده شد**:
- Types: `ToolType`, `ToolOut`, `ToolCreate`, `ToolUpdate`, `InvokeIn`, `InvokeOut`
- Types: `MCPServerOut`, `MCPServerCreate`, `MCPServerStatus`
- Types: `PolicyOut`, `PolicyCreate`, `PolicyUpdate`
- Helper: `apiRequest<T>()` برای درخواست‌های authenticated

**API Modules:**
- `ToolAPI`: list, get, create, update, delete, invoke
- `MCPServerAPI`: list, get, create, rotateKey, enable, disable
- `PolicyAPI`: list, get, create, update, delete

### 2.2 صفحات Tool

✅ **ایجاد شد**:

#### `web/app/dashboard/tools/page.tsx`
- لیست ابزارها با جدول
- ستون‌ها: نام، نوع، نسخه، وضعیت، Rate Limit
- دکمه‌های: تست، ویرایش، حذف
- دکمه "ابزار جدید"

#### `web/app/dashboard/tools/new/page.tsx`
- فرم ساخت Tool کامل
- انتخاب نوع (POSTGRES_QUERY/REST_CALL/CUSTOM)
- انتخاب DataSource (با بارگذاری لیست)
- ویرایشگر JSON برای schemas و exec_config
- Placeholder متناسب با نوع tool

#### `web/app/dashboard/tools/[id]/edit/page.tsx`
- فرم ویرایش Tool
- بارگذاری داده‌های موجود
- ذخیره تغییرات

#### `web/app/dashboard/tools/[id]/test/page.tsx`
- صفحه تست Invoke کامل
- ورودی پارامترها (JSON editor)
- دکمه "اجرای ابزار"
- نمایش نتیجه با:
  - Status (موفق/ناموفق)
  - Trace ID
  - هشدار Field Masking
  - داده‌های خروجی (JSON formatted)
  - پیام خطا (در صورت وجود)
- نمایش Execution Config و Rate Limit

### 2.3 صفحات MCP Server

✅ **ایجاد شد**:

#### `web/app/dashboard/mcp/servers/page.tsx`
- لیست MCP Servers
- ستون‌ها: نام، وضعیت، تاریخ ایجاد
- دکمه‌های: جزئیات، فعال/غیرفعال

#### `web/app/dashboard/mcp/servers/new/page.tsx`
- فرم ساخت سرور
- **نمایش یک‌بارهٔ API Key** پس از ایجاد:
  - هشدار قرمز: "فقط یک بار نمایش"
  - دکمه کپی کلید
  - بلوک سبز برای تأکید

#### `web/app/dashboard/mcp/servers/[id]/page.tsx`
- جزئیات سرور (نام، وضعیت، تاریخ‌ها)
- دکمه "گردش کلید API"
- **نمایش یک‌بارهٔ کلید جدید** پس از rotate:
  - مشابه صفحه ساخت
  - هشدار و دکمه کپی

### 2.4 UX Highlights

✅ **ویژگی‌های UI/UX**:
- **RTL** کامل (dir="rtl")
- پیام‌های فارسی
- رنگ‌بندی: سبز (موفق)، قرمز (خطا)، زرد (هشدار)
- **API Key Management**: نمایش یکباره با تأکید بصری
- **JSON Editors**: با syntax highlighting (font-mono)
- **تست آنلاین**: فرم تعاملی با نتایج فوری
- **Trace ID**: برای debugging و audit

---

## ۳. اسناد

### 3.1 Architecture Documentation

✅ **افزوده شد**: `docs/architecture.md`

**بخش MCP Manager**:
- نمای کلی سیستم
- کامپوننت‌ها: Tool Registry, MCP Server, Policy Engine, Rate Limiter, Audit
- **مخطوطه Mermaid** از Invoke Pipeline (14 مرحله)
- اقدامات امنیتی
- ملاحظات Performance
- محدودیت‌های MVP و بهبودهای V1

### 3.2 Security Documentation

✅ **افزوده شد**: `docs/security.md`

**بخش MCP Manager Security**:
- **API Key Management**: پروتکل one-time display
- **SQL Injection Prevention**: query_template و parameterized queries
- **Policy-Based Access Control**: pipeline اجرا
- **Field Masking**: POST-execution masking
- **Rate Limiting**: token bucket
- **Audit Trail**: اطلاعات لاگ شده

### 3.3 ADR (Architecture Decision Record)

✅ **افزوده شد**: `docs/decisions.md` → **ADR-0003**

**موضوع**: عدم اجازه به SQL دلخواه در MVP

**تصمیم**:
- فقط query_template با named parameters
- منع arbitrary SQL
- استفاده از psycopg parameterized queries

**دلایل**:
- امنیت بالا (SQL Injection غیرممکن)
- Audit trail واضح
- Performance بهتر (query plan caching)

**جایگزین‌ها**: SQL Validation, Read-Only User, Query Builder (رد شدند)

### 3.4 Getting Started

✅ **افزوده شد**: `docs/getting-started.md`

**سناریوی نمونه کامل**:
1. ساخت DataSource (Postgres)
2. ساخت Tool (get_patient_by_id)
3. ایجاد Policy (Mask SSN)
4. تست Invoke
5. مشاهده Metrics

با مثال‌های curl کامل و پاسخ‌های نمونه

---

## ۴. معیارهای پذیرش (Acceptance Criteria)

### ✅ AC1: CRUD کامل
- ✅ Tool: create, list, get, update, delete با org guard و role check
- ✅ MCP Server: create, list, get, rotate, enable, disable (ORG_ADMIN فقط)
- ✅ Policy: CRUD کامل (DATA_STEWARD/ORG_ADMIN)

### ✅ AC2: Invoke امن
- ✅ Policy DENY → 403
- ✅ Field Masking اعمال می‌شود
- ✅ Rate Limit → 429 (پیام فارسی)
- ✅ Audit & Metrics (trace_id برگشت داده می‌شود)

### ✅ AC3: عدم SQL دلخواه
- ✅ POSTGRES_QUERY فقط با query_template
- ✅ Parameterized queries (psycopg)
- ✅ Validation در service layer

### ✅ AC4: UI
- ✅ ساخت/ویرایش Tool
- ✅ تست Invoke در صفحه اختصاصی
- ✅ نمایش متریک (trace_id, masked flag)
- ✅ مدیریت MCP Server
- ✅ ساخت/Rotate Key با نمایش یکبار

### ✅ AC5: تست‌ها
- ✅ 3 فایل تست backend (tool_crud, invoke, server_crud)
- ✅ تمام سناریوهای اصلی پوشش داده شده

### ✅ AC6: اسناد
- ✅ Architecture (با Mermaid diagram)
- ✅ Security
- ✅ ADR-0003
- ✅ Getting Started (سناریوی نمونه)

---

## ۵. فایل‌های ایجاد/تغییر شده

### Backend
```
backend/pyproject.toml                              [MODIFIED]
backend/alembic/env.py                               [MODIFIED]
backend/alembic/versions/001_add_mcp_tool_policy_tables.py [NEW]
backend/apps/core/models/tool.py                     [NEW]
backend/apps/core/models/mcp_server.py               [NEW]
backend/apps/core/models/policy.py                   [NEW]
backend/apps/core/models/__init__.py                 [MODIFIED]
backend/apps/core/models/organization.py             [MODIFIED]
backend/apps/core/models/datasource.py               [MODIFIED]
backend/apps/core/schemas/mcp.py                     [NEW]
backend/apps/core/schemas/__init__.py                [MODIFIED]
backend/apps/core/__init__.py                        [MODIFIED]
backend/apps/mcp/ratelimit.py                        [NEW]
backend/apps/mcp/service.py                          [NEW]
backend/apps/mcp/router.py                           [NEW]
backend/tests/test_mcp_tool_crud.py                  [NEW]
backend/tests/test_mcp_invoke.py                     [NEW]
backend/tests/test_mcp_server_crud.py                [NEW]
```

### Frontend
```
web/lib/api.ts                                       [MODIFIED]
web/app/dashboard/tools/page.tsx                     [NEW]
web/app/dashboard/tools/new/page.tsx                 [NEW]
web/app/dashboard/tools/[id]/edit/page.tsx           [NEW]
web/app/dashboard/tools/[id]/test/page.tsx           [NEW]
web/app/dashboard/mcp/servers/page.tsx               [NEW]
web/app/dashboard/mcp/servers/new/page.tsx           [NEW]
web/app/dashboard/mcp/servers/[id]/page.tsx          [NEW]
```

### Documentation
```
docs/architecture.md                                 [MODIFIED]
docs/security.md                                     [MODIFIED]
docs/decisions.md                                    [MODIFIED]
docs/getting-started.md                              [MODIFIED]
PROMPT4_SUMMARY.md                                   [NEW]
```

---

## ۶. دستورات اجرا

### Backend Setup
```bash
cd backend

# نصب وابستگی‌ها (اگر pip موجود است)
pip install -e .[dev]

# اجرای migrations (نیاز به DB و ENV vars)
export APP_ENV=local
export AUTH_SECRET=dev-secret-32-chars-minimum
export SECRETS_MASTER_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
export DATABASE_URL=postgresql://user:pass@localhost:5432/farda_mcp

# اجرای تست‌ها
pytest tests/test_mcp*.py -v
```

### Frontend Setup
```bash
cd web
npm install
npm run dev
```

صفحات در دسترس:
- http://localhost:3000/dashboard/tools
- http://localhost:3000/dashboard/tools/new
- http://localhost:3000/dashboard/mcp/servers

### Docker Compose
```bash
cd ops/compose
docker compose --env-file .env.example up -d --build
```

---

## ۷. نکات مهم

### امنیت
1. **API Keys**: هرگز ذخیره plain-text نمی‌شوند
2. **SQL Injection**: غیرممکن (query_template فقط)
3. **Policy Enforcement**: تمام invocation ها چک می‌شوند
4. **Rate Limiting**: جلوگیری از سوءاستفاده

### MVP Limitations
1. **Rate Limiter**: In-memory (تک-پردازه) → در production به Redis منتقل شود
2. **Metrics**: In-memory counters → Prometheus/StatsD
3. **Audit**: stdout logging → جدول/سرویس اختصاصی
4. **REST_CALL**: ساده → retry, circuit breaker در V1

### سازگاری با پرامپت‌های قبل
- ✅ Multi-tenancy (org_id guard)
- ✅ Role-based access (ORG_ADMIN, DEVELOPER, DATA_STEWARD)
- ✅ DataSource integration (رمزنگاری envelope)
- ✅ Audit trail (trace_id)
- ✅ Persian UI/UX

---

## ۸. نتیجه

✅ **MCP Manager کامل پیاده‌سازی شد**:
- Backend: مدل‌ها، سرویس‌ها، روترها، تست‌ها
- Frontend: صفحات مدیریت Tool و MCP Server، تست Invoke
- Documentation: معماری، امنیت، ADR، سناریوی نمونه

✅ **همه معیارهای پذیرش برآورده شدند**

✅ **آماده برای تست و استقرار MVP**

---

**تاریخ تکمیل**: 2025-10-19
**نسخه**: 0.1.0 (MVP)
