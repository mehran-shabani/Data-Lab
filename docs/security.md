# اصول امنیتی Farda MCP

این سند اصول و بهترین شیوه‌های امنیتی مورد استفاده در Farda MCP را شرح می‌دهد.

## اصول امنیتی کلیدی

### ۱. Defense in Depth

سیستم از چندین لایه امنیتی استفاده می‌کند:

```
کاربر
  ↓
[Nginx - Rate Limiting, Headers]
  ↓
[Application - Authentication, Authorization]
  ↓
[ORM - SQL Injection Prevention]
  ↓
[Database - Encryption, Access Control]
```

### ۲. Principle of Least Privilege

* هر کامپوننت تنها دسترسی‌های ضروری را دارد
* User در Docker بدون root اجرا می‌شود
* Database users دسترسی محدود دارند

### ۳. Zero Trust

* هیچ ورودی بدون اعتبارسنجی قبول نمی‌شود
* همه داده‌های ورودی validate می‌شوند
* هیچ trust به client-side data نداریم

## مدیریت Secrets و متغیرهای محیطی

### قوانین طلایی

✅ **انجام دهید:**
* استفاده از `.env` files برای تنظیمات محلی
* نگهداری `.env.example` با مقادیر placeholder
* استفاده از Vault یا Secret Manager در production
* Rotate کردن منظم secrets

❌ **انجام ندهید:**
* commit کردن `.env` files به Git
* hardcode کردن secrets در کد
* به اشتراک گذاشتن secrets در کانال‌های ناامن
* استفاده از secrets یکسان در محیط‌های مختلف

### فایل‌های .env

همیشه `.env` files را در `.gitignore` قرار دهید:

```gitignore
# Environment files
.env
.env.local
.env.production
.env.*.local
```

### ساختار Secrets

```bash
# ❌ بد - hardcoded
SECRET_KEY=abc123

# ✅ خوب - در .env.example
SECRET_KEY=your-secret-key-change-in-production

# ✅ بهتر - در production
SECRET_KEY=${VAULT_SECRET}
```

## احراز هویت (Authentication)

### نسخه فعلی (پرامپت ۲ - پیاده‌سازی شده)

سیستم احراز هویت کامل با JWT و چندمستأجری پیاده‌سازی شده است:

#### JWT Tokens

```python
# backend/apps/core/security.py
from jose import jwt
from datetime import datetime, timedelta, UTC

def create_access_token(claims: dict, ttl_min: int = None) -> str:
    """Create JWT access token with HS256."""
    if ttl_min is None:
        ttl_min = settings.AUTH_ACCESS_TTL_MIN
    
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=ttl_min)
    
    to_encode = claims.copy()
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    })
    
    return jwt.encode(to_encode, settings.AUTH_SECRET, algorithm="HS256")
```

#### Token Claims Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "org_id": "organization-uuid",
  "roles": ["ORG_ADMIN"],
  "iat": 1234567890,
  "exp": 1234571490
}
```

#### Dev Login (محیط‌های local/ci)

برای سهولت توسعه، یک endpoint ساده ورود وجود دارد:

```python
# POST /auth/dev/login
{
  "email": "user@example.com",
  "org_name": "Acme Corp"
}
```

این endpoint فقط در `APP_ENV=local` یا `APP_ENV=ci` فعال است و در production غیرفعال می‌شود.

#### OIDC Support (آماده برای production)

اسکلت OIDC برای SSO آماده است:

* `GET /auth/oidc/.well-known` - دریافت تنظیمات OIDC
* `POST /auth/oidc/exchange` - مبادله authorization code

در production، با تنظیم متغیرهای زیر فعال می‌شود:

```bash
OIDC_ISSUER=https://your-idp.com
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-secret
OIDC_REDIRECT_URI=https://your-app.com/auth/callback
```

## مجوزدهی (Authorization)

### RBAC (Role-Based Access Control)

سیستم RBAC پایه پیاده‌سازی شده است:

```
User → Membership → Organization
        ↓
      Roles[]
```

#### مدل داده

```python
class Membership(Base):
    """رابطه کاربر-سازمان با نقش‌ها."""
    user_id: UUID
    org_id: UUID
    roles: list[str]  # ["ORG_ADMIN", "ORG_MEMBER"]
```

#### استفاده از Guards

```python
from apps.core.deps import get_current_user, require_roles, org_guard

# دریافت کاربر جاری
@router.get("/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user

# بررسی نقش
@router.delete("/admin/resource")
async def delete_resource(
    _: CurrentUser = Depends(require_roles("ORG_ADMIN"))
):
    # فقط ORG_ADMIN دسترسی دارد
    pass

# بررسی دسترسی به سازمان
@router.get("/orgs/{org_id}/whoami")
async def whoami(
    org_id: UUID,
    current_user: CurrentUser = Depends(org_guard())
):
    # فقط اگر current_user.org_id == org_id
    return current_user
```

### نقش‌های پیش‌فرض

* `ORG_ADMIN` - مدیر سازمان، دسترسی کامل به منابع سازمان
* `ORG_MEMBER` - عضو معمولی (نقش پیش‌فرض)

## حفاظت از داده‌ها

### ۱. Input Validation

**همیشه** ورودی‌ها را validate کنید:

```python
# با Pydantic
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    email: EmailStr  # اعتبارسنجی ایمیل
    password: constr(min_length=8)  # حداقل 8 کاراکتر
    name: constr(max_length=100)  # محدودیت طول
```

### ۲. SQL Injection Prevention

**همیشه** از ORM استفاده کنید:

```python
# ❌ بد - مستعد SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ خوب - از ORM استفاده می‌کند
user = await session.execute(
    select(User).where(User.email == email)
)
```

### ۳. XSS Prevention

* Frontend: React به‌طور پیش‌فرض از XSS محافظت می‌کند
* Backend: خروجی‌های JSON خطر XSS ندارند
* HTML rendering: از `dangerouslySetInnerHTML` اجتناب کنید

```tsx
// ❌ بد
<div dangerouslySetInnerHTML={{__html: userInput}} />

// ✅ خوب
<div>{userInput}</div>
```

### ۴. CSRF Protection

در **پرامپت ۲**:

* استفاده از CSRF tokens
* SameSite cookies
* Origin/Referer validation

## رمزنگاری

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

### Sensitive Data Encryption with Envelope Encryption (پرامپت ۳)

سیستم از الگوی **Envelope Encryption** برای نگهداری امن اعتبارنامه‌های DataSource استفاده می‌کند:

#### معماری Envelope Encryption

```
┌──────────────────────────────────────────────────────────┐
│  Connection Config (plaintext)                           │
│  {username, password, host, ...}                         │
└────────────────────┬─────────────────────────────────────┘
                     │ AES-GCM
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Data Key (32 bytes random)                              │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        │                          │
        ▼ Encrypt                  ▼ Encrypt with Master Key
┌──────────────────┐         ┌─────────────────────────────┐
│ config_enc       │         │ data_key_enc                │
│ (stored in DB)   │         │ (stored in DB)              │
└──────────────────┘         └─────────────────────────────┘
```

#### پیاده‌سازی

```python
# backend/apps/core/crypto.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def generate_data_key() -> bytes:
    """Generate random 32-byte data key."""
    return os.urandom(32)

def encrypt_with_data_key(plaintext_data: dict, data_key: bytes) -> bytes:
    """Encrypt data with AES-GCM using data key."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(data_key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)
    return nonce + ciphertext_with_tag  # [nonce|tag|ciphertext]

def wrap_key_with_master(data_key: bytes, master_key: bytes) -> bytes:
    """Encrypt data key with master key."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(master_key)
    return nonce + aesgcm.encrypt(nonce, data_key, None)
```

#### Master Key Management

**MVP (فعلی):**
* Master Key از متغیر محیطی `SECRETS_MASTER_KEY` خوانده می‌شود
* باید ۳۲ بایت (۲۵۶ بیت) باشد
* می‌تواند به صورت hex (۶۴ کاراکتر) یا base64 ارائه شود
* در production باید از Vault یا AWS Secrets Manager خوانده شود

```bash
# .env
SECRETS_MASTER_KEY=0123456789abcdef...  # 64 hex chars
```

**V1 (برنامه آتی):**
* یکپارچه‌سازی با HashiCorp Vault
* یا استفاده از AWS KMS / Azure Key Vault
* Automatic key rotation
* Audit logging برای دسترسی به کلیدها

#### اصول امنیتی

1. **No Secrets in Logs**: هیچ لاگ یا endpoint اسرار را نمایش نمی‌دهد
2. **Masked in UI**: فیلدهای حساس در UI به صورت `•••••` نمایش داده می‌شوند
3. **No Secrets in API**: هیچ endpoint اسرار را در پاسخ برنمی‌گرداند
4. **Encryption at Rest**: تمام اعتبارنامه‌ها رمزشده در DB ذخیره می‌شوند
5. **Key Separation**: Data Key جدا از Master Key نگهداری می‌شود

#### مزایای Envelope Encryption

* **Performance**: رمزگشایی سریع با Data Key محلی
* **Key Rotation**: تغییر Master Key بدون بازرمز تمام داده‌ها
* **Scalability**: هر DataSource کلید مستقل دارد
* **Flexibility**: امکان استفاده از KMS‌های مختلف در آینده

## امنیت شبکه

### CORS Configuration

```python
# backend/apps/core/__init__.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # از .env می‌خواند
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

در production، `CORS_ORIGINS` را محدود کنید:

```bash
# Production .env
CORS_ORIGINS=["https://yourdomain.com"]
```

### Security Headers (Nginx)

```nginx
# ops/docker/nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Rate Limiting

در **production** باید rate limiting اضافه شود:

```nginx
# nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend/;
}
```

## چندمستأجری (Multi-tenancy) امن

### معماری چندمستأجری

سیستم از معماری org-scoped استفاده می‌کند:

```
Organization (tenant)
  ↓
Membership
  ├─ User
  └─ Roles[]
```

### جداسازی داده‌ها

جداسازی در سطح application با استفاده از `org_guard`:

```python
@router.get("/orgs/{org_id}/resources")
async def get_resources(
    org_id: UUID,
    current_user: CurrentUser = Depends(org_guard()),
    db: AsyncSession = Depends(get_db)
):
    # org_guard اطمینان می‌دهد current_user.org_id == org_id
    
    # حالا می‌توانیم داده‌های این سازمان را برگردانیم
    return await db.execute(
        select(Resource).where(Resource.org_id == org_id)
    )
```

### Tenant Isolation

```
Request → JWT (org_id) → org_guard() → Database Query
                ↓                            ↓
         current_user.org_id        WHERE org_id = ...
```

**قوانین طلایی:**

1. همیشه از `org_guard()` برای endpoint‌های org-scoped استفاده کنید
2. هرگز به `org_id` از query parameters اعتماد نکنید
3. همیشه `org_id` را از JWT token استخراج کنید

## Audit Logging

### الزامات

تمام عملیات حساس باید log شوند:

* ورود/خروج کاربر
* تغییرات در permissions
* دسترسی به داده‌های حساس
* تغییرات در tenant settings

### پیاده‌سازی (پرامپت‌های بعدی)

```python
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    action: Mapped[str]  # "login", "update_user", etc.
    resource: Mapped[str]  # "user", "tenant", etc.
    resource_id: Mapped[str]
    timestamp: Mapped[datetime]
    ip_address: Mapped[str]
    user_agent: Mapped[str]
```

## دیتابیس

### Connection Security

```python
# استفاده از SSL در production
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

### Backup Security

* Backups باید encrypted شوند
* دسترسی محدود به backup files
* تست منظم restore process

### Password Policy

در **پرامپت ۲**:

```python
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_MAX_AGE_DAYS = 90
```

## Docker Security

### Non-root User

```dockerfile
# ✅ خوب
RUN useradd -m -u 1000 appuser
USER appuser
```

### Image Security

```dockerfile
# استفاده از official base images
FROM python:3.11-slim  # ✅

# نه از images ناشناس
FROM random/python  # ❌
```

### Secrets در Docker

```yaml
# ❌ بد - hardcoded
environment:
  SECRET_KEY: abc123

# ✅ خوب - از .env می‌خواند
environment:
  SECRET_KEY: ${SECRET_KEY}

# ✅ بهتر - Docker secrets (production)
secrets:
  - db_password
```

## برنامه آینده

### پرامپت ۲

* احراز هویت کامل JWT/OIDC
* RBAC با roles و permissions
* چندمستأجری با tenant isolation
* CSRF protection
* MFA (optional)

### پرامپت‌های بعدی

* HashiCorp Vault integration
* AWS KMS/Secrets Manager
* Advanced audit logging
* Security scanning در CI/CD
* Penetration testing
* OWASP compliance checks

## Checklist امنیتی

قبل از deploy در production:

- [ ] همه `.env` files در `.gitignore`
- [ ] Secrets از Vault/KMS خوانده می‌شوند
- [ ] CORS به دامنه‌های مجاز محدود شده
- [ ] Rate limiting فعال است
- [ ] SSL/TLS برای همه connections
- [ ] Database backups encrypted
- [ ] Audit logging فعال است
- [ ] Security headers تنظیم شده
- [ ] Password policy اعمال شده
- [ ] Dependencies به‌روز هستند
- [ ] Security scanning در CI/CD

## مراجع

* [OWASP Top 10](https://owasp.org/www-project-top-ten/)
* [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
* [Next.js Security](https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy)
* [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

**یادآوری**: امنیت یک فرآیند مداوم است، نه یک هدف یکباره.
