# Farda MCP Web

فرانت‌اند Farda MCP بر پایهٔ Next.js 15 با App Router، TypeScript و پشتیبانی کامل RTL.

## ویژگی‌ها

* ⚡ Next.js 15 با App Router
* 🎨 Tailwind CSS برای استایل‌دهی
* 🌐 پشتیبانی کامل از راست‌به‌چپ (RTL)
* 📅 تقویم جلالی
* 🔐 آماده برای احراز هویت (پرامپت ۲)
* 📱 طراحی واکنش‌گرا (Responsive)

## نیازمندی‌ها

* Node.js 20+
* npm یا pnpm یا yarn

## نصب و راه‌اندازی

### ۱. نصب وابستگی‌ها

```bash
cd web
npm install
# یا
pnpm install
```

### ۲. تنظیم متغیرهای محیطی

```bash
cp .env.example .env.local
# فایل .env.local را ویرایش کنید
```

### ۳. اجرای سرور توسعه

```bash
npm run dev
```

برنامه در آدرس `http://localhost:3000` در دسترس خواهد بود.

## اسکریپت‌ها

* `npm run dev` - اجرای سرور توسعه
* `npm run build` - ساخت برای production
* `npm run start` - اجرای سرور production
* `npm run lint` - بررسی کد با ESLint
* `npm run typecheck` - بررسی نوع‌ها با TypeScript

## ساختار پروژه

```
web/
  app/              # Next.js App Router
    (auth)/         # گروه مسیریابی برای احراز هویت
    dashboard/      # داشبورد
    api/            # API Routes
    layout.tsx      # Layout اصلی با RTL
    page.tsx        # صفحه خانه
  components/       # کامپوننت‌های قابل استفاده مجدد
  lib/              # توابع کمکی و utilities
    api.ts          # کلاینت API
    i18n.ts         # ترجمه و بین‌المللی‌سازی
    jalali.ts       # تقویم جلالی
  public/           # فایل‌های استاتیک
```

## صفحات

* `/` - صفحه خوش‌آمدگویی
* `/dashboard` - داشبورد (در حال توسعه)
* `/signin` - ورود به سیستم (UI نمایشی)
* `/api/health` - API Route برای بررسی سلامت

## استایل‌دهی

این پروژه از Tailwind CSS استفاده می‌کند. تمام استایل‌ها به‌صورت RTL و با فونت Vazirmatn پیکربندی شده‌اند.

## i18n و RTL

* فونت پیش‌فرض: Vazirmatn (از Google Fonts)
* جهت متن: راست‌به‌چپ (RTL)
* زبان: فارسی (fa)
* تقویم: جلالی/شمسی

## توسعه

این پروژه از استانداردهای زیر پیروی می‌کند:

* **TypeScript** برای type safety
* **ESLint** برای کیفیت کد
* **Tailwind CSS** برای استایل‌دهی
* **React 19** با Server Components
* **Next.js 15** با App Router

برای اطلاعات بیشتر، به مستندات در پوشهٔ `docs/` مراجعه کنید.
