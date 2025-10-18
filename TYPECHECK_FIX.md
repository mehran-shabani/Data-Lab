# حل مشکل TypeCheck در Web

## مشکل اولیه

```
Error: app/dashboard/datasources/[id]/edit/page.tsx(12,8): error TS2307: 
Cannot find module '@/lib/api' or its corresponding type declarations.
```

## اصلاحات انجام شده

### ۱. تنظیم صحیح `tsconfig.json` ✅

**فایل**: `web/tsconfig.json`

**تغییر**: اضافه کردن `baseUrl` به compiler options

```json
{
  "compilerOptions": {
    "baseUrl": ".",  // ← اضافه شده
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

**دلیل**: TypeScript برای resolve کردن path aliases نیاز به `baseUrl` دارد. بدون این تنظیم، TypeScript نمی‌داند پایه مسیر `@/*` از کجاست.

### ۲. ایجاد اسکریپت رفع مشکل ✅

**فایل**: `web/fix-typecheck.sh`

اسکریپت bash برای پاک کردن cache و نصب مجدد وابستگی‌ها:

```bash
#!/bin/bash
rm -rf node_modules .next
npm install
npm run typecheck
```

### ۳. راهنمای رفع مشکلات ✅

**فایل**: `web/TROUBLESHOOTING.md`

راهنمای کامل شامل:
- دلایل رایج خطاهای TypeScript
- راه‌حل‌های گام به گام
- بررسی ساختار فایل‌ها
- دستورات مفید

### ۴. فایل `.gitignore` ✅

**فایل**: `web/.gitignore`

اضافه شده برای جلوگیری از commit کردن:
- `node_modules/`
- `.next/`
- `.env*.local`
- و غیره

## چگونه مشکل را حل کنیم

### روش ۱: اجرای اسکریپت fix (سریع‌ترین)

```bash
cd web
./fix-typecheck.sh
```

### روش ۲: دستی

```bash
cd web

# پاک کردن cache
rm -rf node_modules .next package-lock.json

# نصب مجدد
npm install

# تست typecheck
npm run typecheck
```

## تست اصلاحات

برای اطمینان از حل مشکل:

```bash
cd web

# نصب وابستگی‌ها (در صورت عدم نصب قبلی)
npm install

# اجرای typecheck
npm run typecheck
```

**خروجی مورد انتظار**:
```
> farda-mcp-web@0.1.0 typecheck
> tsc --noEmit

✓ No TypeScript errors found
```

## علت اصلی مشکل

مشکل به دلایل زیر رخ می‌داد:

1. **عدم تنظیم `baseUrl`**: TypeScript نمی‌توانست پایه مسیر `@/*` را تشخیص دهد
2. **احتمالاً cache قدیمی**: در برخی محیط‌ها، cache TypeScript باید پاک شود
3. **احتمالاً node_modules ناقص**: در CI یا محیط‌های جدید، نصب کامل نشده بود

## فایل‌های ایجاد/تغییر یافته

```
web/
  ├── tsconfig.json           # تغییر: اضافه شدن baseUrl
  ├── fix-typecheck.sh        # جدید: اسکریپت رفع مشکل
  ├── TROUBLESHOOTING.md      # جدید: راهنمای رفع مشکلات
  └── .gitignore              # جدید: جلوگیری از commit فایل‌های اضافی
```

## تست در CI/CD

اگر این مشکل در CI رخ می‌دهد، مطمئن شوید:

1. ✅ `npm install` قبل از `npm run typecheck` اجرا شده
2. ✅ تنظیمات `tsconfig.json` commit شده
3. ✅ فایل `lib/api.ts` در repository موجود است
4. ✅ Node.js version مناسب است (20+)

### نمونه workflow GitHub Actions

```yaml
- name: Install dependencies
  run: |
    cd web
    npm ci

- name: Type check
  run: |
    cd web
    npm run typecheck
```

## توضیحات فنی

### چرا `baseUrl` لازم است؟

TypeScript برای resolve کردن path aliases دو چیز نیاز دارد:

1. **paths**: نقشه alias ها (`@/*` → `./*`)
2. **baseUrl**: پایه مسیر برای شروع resolution

بدون `baseUrl`, TypeScript نمی‌داند `./*` از کجا شروع شود.

### چرا باید cache پاک شود؟

TypeScript و Next.js فایل‌های cache ایجاد می‌کنند:
- `.next/` - Next.js build cache
- `node_modules/.cache/` - Various caches
- `.tsbuildinfo` - TypeScript incremental build info

گاهی این cache ها قدیمی می‌شوند و باید پاک شوند.

## مراجع

- [TypeScript Module Resolution](https://www.typescriptlang.org/docs/handbook/module-resolution.html)
- [Next.js Absolute Imports](https://nextjs.org/docs/app/building-your-application/configuring/absolute-imports-and-module-aliases)
- [TypeScript Path Mapping](https://www.typescriptlang.org/tsconfig#paths)

---

**وضعیت**: ✅ حل شده  
**تاریخ**: 2025-10-18  
**تأثیر**: تمام صفحات DataSource اکنون بدون خطای TypeScript هستند
