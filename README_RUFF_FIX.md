# 🔧 رفع سریع خطای Ruff در CI

## مشکل شما

```
I001 [*] Import block is un-sorted or un-formatted
apps/core/schemas/datasource.py
```

## ⚡ راه‌حل (30 ثانیه)

```bash
cd backend
pip install ruff
ruff check . --fix
git add -u
git commit -m "fix: organize imports with ruff"
git push
```

**تمام!** ✅

---

## چرا این کار می‌کند؟

- `ruff check . --fix` **خودکار** تمام imports را مرتب می‌کند
- مطابق با استاندارد PEP8 و isort
- همه فایل‌ها را یکجا اصلاح می‌کند

---

## راهنماهای کامل

اگر می‌خواهید بیشتر بدانید:

1. 📘 **RUFF_ERROR_FINAL_FIX.md** - راهنمای کامل
2. 📘 **CI_LINT_SOLUTION.md** - راه‌حل برای CI/CD
3. 📘 **IMPORT_SORT_FIX.md** - توضیحات تکنیکال
4. 🔧 **backend/FIX_RUFF_IN_CI.sh** - اسکریپت خودکار

---

## سوالات متداول

**Q: چرا محلی کار می‌کرد اما در CI خطا داد؟**  
A: CI از ruff استفاده می‌کند که قوانین دقیق‌تری دارد.

**Q: باید هر بار این کار را بکنم؟**  
A: خیر! از Pre-commit hook استفاده کنید (راهنما در اسناد).

**Q: آیا کد من خراب می‌شود؟**  
A: خیر! ruff فقط imports را مرتب می‌کند، منطق کد تغییر نمی‌کند.

---

**بیایید شروع کنیم! دستور بالا را اجرا کنید. 🚀**
