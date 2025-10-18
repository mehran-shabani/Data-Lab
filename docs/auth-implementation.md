# پیاده‌سازی احراز هویت - پرامپت ۲

این سند جزئیات فنی پیاده‌سازی احراز هویت در پرامپت ۲ را شرح می‌دهد.

## معماری کلی

```
Frontend (Next.js)
  ↓ POST /api/dev-login
  ↓
Next.js API Route
  ↓ POST /auth/dev/login
  ↓
Backend (FastAPI)
  ↓ Create User/Org/Membership
  ↓ Generate JWT
  ↓
Return token → Set HTTP-only Cookie
  ↓
Frontend stores cookie
  ↓
Subsequent requests include cookie
  ↓
Backend validates JWT from Authorization header
```

## مدل‌های دیتابیس

### Organization

```python
class Organization(Base):
    id: UUID              # PK
    name: str
    plan: str = "free"    # free, pro, enterprise
    created_at: datetime
```

### User

```python
class User(Base):
    id: UUID              # PK
    email: str            # unique
    created_at: datetime
```

### Membership

```python
class Membership(Base):
    id: UUID              # PK
    user_id: UUID         # FK → users.id
    org_id: UUID          # FK → organizations.id
    roles: list[str]      # ["ORG_ADMIN", "ORG_MEMBER"]
```

**نکات:**
- یک کاربر می‌تواند به چندین سازمان تعلق داشته باشد
- هر membership می‌تواند چندین نقش داشته باشد
- نقش‌ها در JWT token قرار می‌گیرند

## JWT Token

### ساختار Claims

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "org_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "roles": ["ORG_ADMIN"],
  "iat": 1234567890,
  "exp": 1234571490
}
```

### ایجاد Token

```python
from apps.core.security import create_access_token

claims = {
    "sub": str(user.id),
    "email": user.email,
    "org_id": str(org.id),
    "roles": membership.roles,
}

token = create_access_token(claims, ttl_min=60)
```

### اعتبارسنجی Token

```python
from apps.core.security import decode_token
from jose import JWTError

try:
    payload = decode_token(token)
    user_id = payload["sub"]
    org_id = payload["org_id"]
    roles = payload["roles"]
except JWTError:
    # Token invalid or expired
    raise HTTPException(401, "Invalid token")
```

## API Endpoints

### Dev Login (Development)

**مسیر:** `POST /auth/dev/login`

**شرایط:** `APP_ENV in ["local", "ci"]`

**ورودی:**
```json
{
  "email": "user@example.com",
  "org_name": "Acme Corp"
}
```

**خروجی:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "org_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

**رفتار:**
1. یافتن یا ساخت User با email
2. یافتن یا ساخت Organization با name
3. یافتن یا ساخت Membership با نقش `["ORG_ADMIN"]`
4. صدور JWT token

### OIDC Well-Known (Production)

**مسیر:** `GET /auth/oidc/.well-known`

**شرایط:** `APP_ENV == "prod"` و همه تنظیمات OIDC پر باشند

**خروجی:**
```json
{
  "issuer": "https://idp.example.com",
  "client_id": "your-client-id",
  "redirect_uri": "https://app.example.com/callback"
}
```

### OIDC Exchange (Production - Skeleton)

**مسیر:** `POST /auth/oidc/exchange`

**ورودی:**
```json
{
  "code": "authorization_code_from_idp",
  "state": "csrf_state_token"
}
```

**وضعیت:** اسکلت (فعلاً 503 برمی‌گرداند)

**TODO برای V1:**
1. مبادله code با IdP
2. اعتبارسنجی ID token
3. استخراج اطلاعات کاربر
4. ساخت/به‌روزرسانی User و Membership
5. صدور JWT token

### Get Current User

**مسیر:** `GET /me`

**نیازمندی:** JWT token در header

**خروجی:**
```json
{
  "email": "user@example.com",
  "org_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "roles": ["ORG_ADMIN"]
}
```

### Org-Scoped Whoami

**مسیر:** `GET /orgs/{org_id}/whoami`

**نیازمندی:** JWT token + `current_user.org_id == org_id`

**خروجی:** مشابه `/me`

**رفتار:**
- اگر `org_id` در مسیر با `org_id` در token مطابقت نداشته باشد → 403

## Dependencies و Guards

### get_current_user

استخراج و اعتبارسنجی کاربر جاری از JWT:

```python
from apps.core.deps import get_current_user, CurrentUser

@router.get("/protected")
async def protected_route(
    current_user: CurrentUser = Depends(get_current_user)
):
    # current_user.user_id
    # current_user.email
    # current_user.org_id
    # current_user.roles
    pass
```

### require_roles

بررسی نقش کاربر:

```python
from apps.core.deps import require_roles

@router.delete("/admin-only")
async def admin_only(
    _: CurrentUser = Depends(require_roles("ORG_ADMIN"))
):
    # فقط کاربران با نقش ORG_ADMIN
    pass
```

### org_guard

اطمینان از تعلق کاربر به سازمان:

```python
from apps.core.deps import org_guard

@router.get("/orgs/{org_id}/data")
async def get_org_data(
    org_id: UUID,
    current_user: CurrentUser = Depends(org_guard())
):
    # فقط اگر current_user.org_id == org_id
    pass
```

## Frontend Integration

### Dev Login Flow

```typescript
// web/app/api/dev-login/route.ts
const response = await fetch(`${backendUrl}/auth/dev/login`, {
  method: 'POST',
  body: JSON.stringify({ email, org_name })
})

const { access_token, org_id } = await response.json()

// Set HTTP-only cookie
cookies().set('farda_token', access_token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  maxAge: 60 * 60 // 1 hour
})
```

### Authenticated Requests

```typescript
// web/lib/api.ts
export async function apiFetch(path: string, init?: RequestInit) {
  const headers = new Headers(init?.headers)
  
  // در SSR، کوکی را دستی اضافه کن
  if (typeof window === 'undefined') {
    const token = cookies().get('farda_token')?.value
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }
  
  return fetch(`${apiUrl}${path}`, { ...init, headers })
}
```

## تنظیمات محیطی

### Backend (.env)

```bash
APP_ENV=local                    # local | ci | prod
AUTH_SECRET=change-in-prod       # کلید JWT (حداقل 32 کاراکتر)
AUTH_ACCESS_TTL_MIN=60           # مدت اعتبار token (دقیقه)

# OIDC (فقط در production)
OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_REDIRECT_URI=
```

### Frontend (.env)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_BASE_URL=http://backend:8000  # در Docker
AUTH_ACCESS_TTL_MIN=60
```

## امنیت

### چک‌لیست امنیتی

- ✅ کلید JWT (`AUTH_SECRET`) پیچیده و منحصربه‌فرد باشد
- ✅ Token expiry معقول تنظیم شود (60 دقیقه)
- ✅ Dev login فقط در local/ci فعال باشد
- ✅ OIDC secrets در production از Vault خوانده شوند
- ✅ JWT signature همیشه بررسی شود
- ✅ Org isolation با `org_guard` اعمال شود
- ✅ HTTP-only cookies برای ذخیره token
- ✅ CORS به دامنه‌های مجاز محدود شود

### محدودیت‌های فعلی (MVP)

1. **Refresh Tokens:** فعلاً وجود ندارد
   - Token‌ها پس از انقضا نیاز به ورود مجدد دارند
   - در V1 باید refresh token اضافه شود

2. **Password Authentication:** فعلاً وجود ندارد
   - Dev login بدون رمز عبور است
   - OIDC برای production authentication

3. **Session Management:** ساده است
   - فعلاً tracking نمی‌شود
   - در V1 باید session management اضافه شود

4. **Rate Limiting:** فعلاً وجود ندارد
   - در production باید rate limiting اضافه شود

## تست‌ها

### نمونه تست‌های موجود

```python
# tests/test_auth_multitenant.py

def test_dev_login_creates_user_and_org():
    """Dev login ساخت user/org و برگرداندن token."""
    
def test_me_endpoint_with_valid_token():
    """دریافت اطلاعات کاربر با token معتبر."""
    
def test_org_guard_allows_same_org():
    """org_guard اجازه دسترسی به org خودی."""
    
def test_org_guard_denies_different_org():
    """org_guard جلوگیری از دسترسی به org دیگر."""
```

### اجرای تست‌ها

```bash
cd backend
export APP_ENV=ci AUTH_SECRET=test-secret
pytest tests/test_auth_multitenant.py -v
```

## مهاجرت‌های دیتابیس

```bash
# ایجاد migration جدید
cd backend
alembic revision -m "add auth models"

# اعمال migration‌ها
alembic upgrade head

# برگشت migration
alembic downgrade -1
```

## عیب‌یابی

### مشکل: Token نامعتبر

```python
# بررسی کلید AUTH_SECRET
print(settings.AUTH_SECRET)

# بررسی expiry
from jose import jwt
payload = jwt.decode(token, verify=False)  # بدون verify
print(payload['exp'])  # زمان انقضا
```

### مشکل: 403 در org_guard

```python
# بررسی org_id در token
from apps.core.security import decode_token
payload = decode_token(token)
print(f"Token org_id: {payload['org_id']}")
print(f"Path org_id: {org_id}")
```

### مشکل: Cookie ذخیره نمی‌شود

```typescript
// بررسی تنظیمات cookie
cookies().set('farda_token', token, {
  httpOnly: true,
  secure: false,  // در development
  sameSite: 'lax',
  path: '/',
})
```

## برنامه آینده (V1+)

1. **Refresh Tokens**
   - افزودن `refresh_token` به جدول
   - Endpoint برای refresh: `POST /auth/refresh`
   - Automatic token refresh در frontend

2. **OIDC کامل**
   - تکمیل `/auth/oidc/exchange`
   - پشتیبانی از چندین IdP
   - Auto-provisioning کاربران

3. **Session Management**
   - Tracking session‌های فعال
   - Logout همه session‌ها
   - Session timeout

4. **MFA (Multi-Factor Authentication)**
   - TOTP support
   - SMS/Email codes
   - Backup codes

5. **Audit Logging**
   - Log همه رویدادهای احراز هویت
   - Failed login attempts
   - IP tracking

---

**نگارش:** پرامپت ۲  
**تاریخ:** 2025-10-18  
**وضعیت:** پیاده‌سازی شده و تست شده
