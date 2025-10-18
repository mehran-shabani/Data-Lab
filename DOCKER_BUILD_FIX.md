# حل مشکل Docker Build - Module not found '@/lib/api'

تاریخ: 2025-10-18

## مشکل

هنگام build کردن Docker image برای web، خطای زیر رخ داد:

```
Module not found: Can't resolve '@/lib/api'

./app/dashboard/datasources/[id]/edit/page.tsx
./app/dashboard/datasources/new/page.tsx
./app/dashboard/datasources/page.tsx
```

## علت ریشه‌ای

در فایل `.gitignore` ریشه پروژه، `lib/` به صورت کلی ignore شده بود:

```gitignore
# قبل (اشتباه)
lib/          # ← این web/lib/ را هم ignore می‌کند!
lib64/
```

این تنظیم برای ignore کردن Python library directories (`lib/`, `lib64/`) در نظر گرفته شده بود، اما به اشتباه `web/lib/` را هم ignore می‌کرد.

### چرا در محیط local کار می‌کرد؟

- فایل `web/lib/api.ts` روی دیسک وجود داشت
- Next.js در حالت dev (`npm run dev`) مستقیماً از filesystem می‌خواند
- TypeScript compiler هم فایل را می‌دید

### چرا در Docker build کار نمی‌کرد؟

- Docker از Git context استفاده می‌کند
- فایل‌های untracked/ignored در Git به Docker کپی نمی‌شوند
- فایل `web/lib/api.ts` در Git tracked نبود
- در نتیجه در Docker image وجود نداشت

## راه‌حل

### ۱. اصلاح `.gitignore` ✅

تغییر `lib/` به `backend/lib/` برای مشخص کردن scope:

```gitignore
# بعد (صحیح)
backend/lib/     # ← فقط backend/lib/ را ignore می‌کند
backend/lib64/
```

### ۲. اضافه کردن `web/lib/api.ts` به Git ✅

```bash
git add web/lib/api.ts
```

## تست اصلاح

### محلی (Local)

```bash
cd web

# تست typecheck
npm run typecheck

# تست build
npm run build
```

### Docker Build

```bash
# از ریشه پروژه
docker build -f ops/docker/web.Dockerfile -t farda-mcp-web:test .

# یا با docker compose
cd ops/compose
docker compose build web
```

**خروجی مورد انتظار:**
```
✓ Creating an optimized production build
✓ Compiled successfully
```

## درس‌های آموخته

### ۱. Scope Specific Ignores

**بد:**
```gitignore
lib/           # خیلی عمومی - همه lib/ ها را ignore می‌کند
node_modules/  # خیلی عمومی
```

**خوب:**
```gitignore
backend/lib/        # مشخص - فقط backend
backend/lib64/
web/node_modules/   # مشخص - فقط web
backend/.venv/      # مشخص - فقط backend
```

### ۲. تست Docker Build در Local

قبل از push به CI/CD، همیشه Docker build را local تست کنید:

```bash
# تست سریع
docker build -f ops/docker/web.Dockerfile -t test-image .

# با docker compose
docker compose build
```

### ۳. بررسی Git Tracked Files

برای اطمینان از tracked بودن فایل‌های مهم:

```bash
# لیست فایل‌های tracked در یک directory
git ls-files web/lib/

# چک کردن اینکه آیا یک فایل ignore شده
git check-ignore -v web/lib/api.ts
```

## بهبودهای پیشنهادی

### ۱. بهبود `.gitignore`

ساختار بهتر برای monorepo:

```gitignore
# Python (Backend)
backend/__pycache__/
backend/*.pyc
backend/.pytest_cache/
backend/.venv/
backend/lib/
backend/lib64/

# Node.js (Web)
web/node_modules/
web/.next/
web/out/
web/.env*.local

# Shared
*.log
.DS_Store
.env
```

### ۲. اضافه کردن Pre-commit Check

اطمینان از اینکه فایل‌های ضروری tracked هستند:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if critical files are tracked
CRITICAL_FILES=(
  "web/lib/api.ts"
  "backend/apps/core/crypto.py"
)

for file in "${CRITICAL_FILES[@]}"; do
  if ! git ls-files --error-unmatch "$file" &>/dev/null; then
    echo "Error: Critical file not tracked: $file"
    exit 1
  fi
done
```

### ۳. Docker Build در CI/CD

اضافه کردن build test به GitHub Actions:

```yaml
# .github/workflows/docker-build.yml
name: Docker Build Test

on: [push, pull_request]

jobs:
  test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Web Image
        run: |
          docker build -f ops/docker/web.Dockerfile -t test-web .
      
      - name: Build Backend Image
        run: |
          docker build -f ops/docker/backend.Dockerfile -t test-backend .
```

## چک‌لیست برای آینده

قبل از push کد جدید:

- [ ] تست `npm run build` در web
- [ ] بررسی `git ls-files` برای فایل‌های جدید
- [ ] تست Docker build محلی
- [ ] بررسی `.gitignore` برای عدم ignore اتفاقی
- [ ] اجرای تست‌های یکپارچه

## فایل‌های تغییر یافته

```
/
  ├── .gitignore              # اصلاح: lib/ → backend/lib/
  └── web/
      └── lib/
          └── api.ts          # اضافه به git
```

## کامیت نهایی

```bash
git add .gitignore web/lib/api.ts
git commit -m "fix: resolve Docker build issue by scoping lib/ ignore to backend only

- Change lib/ to backend/lib/ in .gitignore
- Add web/lib/api.ts to git tracking
- Fixes 'Module not found' error in Docker build
"
```

## نتیجه

✅ **Docker build اکنون موفق است**

- فایل `web/lib/api.ts` در Git tracked
- `.gitignore` scope شده به backend
- Build محلی و Docker هر دو کار می‌کنند

---

**وضعیت**: ✅ حل شده  
**تأثیر**: Docker build اکنون بدون خطا می‌سازد  
**تست شده**: ✅ محلی و Docker
