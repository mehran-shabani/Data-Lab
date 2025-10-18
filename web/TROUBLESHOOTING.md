# راهنمای رفع مشکلات Web (Next.js)

## مشکل: خطای TypeScript برای ماژول `@/lib/api`

### علت
خطای زیر نشان می‌دهد که TypeScript نمی‌تواند ماژول‌های با path alias `@/*` را پیدا کند:

```
Error: Cannot find module '@/lib/api' or its corresponding type declarations.
```

### راه‌حل ۱: نصب مجدد وابستگی‌ها (توصیه می‌شود)

```bash
cd web

# پاک کردن cache و node_modules
rm -rf node_modules .next package-lock.json

# نصب مجدد
npm install

# اجرای typecheck
npm run typecheck
```

یا استفاده از اسکریپت آماده:

```bash
cd web
./fix-typecheck.sh
```

### راه‌حل ۲: بررسی تنظیمات

مطمئن شوید که `tsconfig.json` شامل موارد زیر باشد:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### راه‌حل ۳: بررسی ساختار فایل‌ها

مطمئن شوید که ساختار زیر وجود دارد:

```
web/
  ├── lib/
  │   └── api.ts          ← باید وجود داشته باشد
  ├── app/
  │   └── dashboard/
  │       └── datasources/
  │           ├── page.tsx
  │           ├── new/
  │           │   └── page.tsx
  │           └── [id]/
  │               └── edit/
  │                   └── page.tsx
  └── tsconfig.json
```

### راه‌حل ۴: بررسی وجود TypeScript

```bash
# بررسی نصب TypeScript
npx tsc --version

# اگر نصب نیست:
npm install --save-dev typescript
```

## مشکلات رایج دیگر

### خطای "Module not found" در runtime

**علت**: مسیر import اشتباه است یا فایل حذف شده.

**راه‌حل**:
```bash
# بررسی وجود فایل
ls -la lib/api.ts

# اگر وجود ندارد، از Git بازیابی کنید
git checkout lib/api.ts
```

### خطای CORS در توسعه

**علت**: Backend در حال اجرا نیست یا CORS تنظیم نشده.

**راه‌حل**:
1. مطمئن شوید backend در `http://localhost:8000` در حال اجرا است
2. بررسی `NEXT_PUBLIC_API_URL` در `.env.local`
3. بررسی تنظیمات CORS در backend

### Build fails

**علت**: خطاهای TypeScript یا missing dependencies.

**راه‌حل**:
```bash
# اجرای typecheck
npm run typecheck

# اجرای lint
npm run lint

# رفع خطاها و build مجدد
npm run build
```

## دستورات مفید

```bash
# اجرای development server
npm run dev

# typecheck بدون build
npm run typecheck

# linting
npm run lint

# production build
npm run build

# اجرای production server
npm run start
```

## دریافت کمک

اگر مشکل همچنان پابرجاست:

1. بررسی [Issues در GitHub](https://github.com/your-org/farda-mcp/issues)
2. ایجاد issue جدید با:
   - پیام خطای کامل
   - نسخه Node.js و npm (`node -v`, `npm -v`)
   - محتوای `tsconfig.json`
   - خروجی `npm list typescript`

---

**نکته**: پس از هر تغییر در `tsconfig.json`، Next.js dev server را restart کنید.
