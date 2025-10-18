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

### نسخه فعلی (MVP)

در حال حاضر احراز هویت ساده‌ای پیاده‌سازی شده است که در **پرامپت ۲** تکمیل خواهد شد.

```python
# backend/apps/core/security.py
# Placeholder implementation
def create_access_token(data: dict) -> str:
    # Will be implemented in prompt 2
    return "placeholder-token"
```

### پرامپت ۲ (آینده نزدیک)

احراز هویت کامل با:

* **JWT Tokens**: برای stateless authentication
* **OIDC Support**: برای SSO
* **Refresh Tokens**: برای امنیت بیشتر
* **Password Hashing**: با bcrypt
* **MFA**: Two-factor authentication (اختیاری)

```python
# نمونه (پرامپت 2)
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

## مجوزدهی (Authorization)

### RBAC (Role-Based Access Control)

در **پرامپت ۲** پیاده‌سازی خواهد شد:

```
User
  ├─ Roles (many-to-many)
  │   ├─ Admin
  │   ├─ Tenant Admin
  │   ├─ User
  │   └─ Guest
  └─ Permissions (via Roles)
      ├─ tenant.create
      ├─ tenant.read
      ├─ tenant.update
      └─ tenant.delete
```

### Resource-level Permissions

```python
# نمونه (پرامپت 2)
@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_permission("tenant.read"))
):
    # بررسی دسترسی کاربر به tenant
    if not current_user.has_access_to_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    return tenant
```

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

### Sensitive Data Encryption

برای داده‌های حساس در دیتابیس (پرامپت‌های بعدی):

```python
from cryptography.fernet import Fernet

# در production از Vault/KMS استفاده کنید
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt
encrypted = cipher.encrypt(b"sensitive data")

# Decrypt
decrypted = cipher.decrypt(encrypted)
```

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

### جداسازی داده‌ها

در **پرامپت ۲** پیاده‌سازی خواهد شد:

```python
# هر query باید tenant_id را بررسی کند
async def get_user_items(
    user: User,
    db: AsyncSession
):
    return await db.execute(
        select(Item)
        .where(Item.tenant_id == user.tenant_id)  # ✅ فیلتر tenant
        .where(Item.user_id == user.id)
    )
```

### Tenant Isolation

```
Tenant A         Tenant B
  ↓                ↓
Data A          Data B
  ↓                ↓
[Row-level Security Filter]
  ↓
PostgreSQL
```

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
