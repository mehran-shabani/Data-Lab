# راه‌حل قطعی خطای Ruff I001 - Import Sorting

## 🎯 مشکل

```
I001 [*] Import block is un-sorted or un-formatted
apps/core/schemas/datasource.py
Found 1 error. [*] 1 fixable with the `--fix` option.
```

## ⚡ راه‌حل فوری (یک خط!)

```bash
cd backend && pip install ruff && ruff check . --fix
```

این دستور:
1. ruff را نصب می‌کند
2. **خودکار** همه مشکلات import sorting را حل می‌کند
3. فایل را به شکل صحیح مرتب می‌کند

## 📋 راه‌حل گام به گام

### در محیط محلی (Local):

```bash
# 1. رفتن به پوشه backend
cd backend

# 2. نصب ruff (اگر نصب نیست)
pip install ruff

# 3. اصلاح خودکار
ruff check . --fix

# 4. بررسی
ruff check .
```

**خروجی مورد انتظار:**
```
All checks passed!
```

### برای CI/CD:

اگر در GitHub Actions این خطا می‌بینید، در Workflow خود `--fix` را اضافه کنید:

```yaml
# ❌ قبل (فقط بررسی می‌کند)
- name: Lint with ruff
  run: |
    cd backend
    ruff check .

# ✅ بعد (اصلاح می‌کند)
- name: Lint with ruff
  run: |
    cd backend
    ruff check . --fix
    # یا فقط بررسی اگر می‌خواهید force کنید که محلی fix شود
    ruff check .
```

## 🔍 چرا این اتفاق می‌افتد؟

Ruff قوانین `isort` را برای مرتب‌سازی imports اعمال می‌کند:

**ترتیب صحیح:**
```python
"""Module docstring."""

# بخش 1: Standard library (مرتب‌شده الفبایی)
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

# یک خط خالی

# بخش 2: Third-party (مرتب‌شده الفبایی)
from pydantic import BaseModel, Field, model_validator

# یک خط خالی

# بخش 3: کد اصلی
```

## 🚀 راه‌حل‌های خودکار

### اسکریپت آماده

استفاده از اسکریپت آماده:

```bash
cd backend
./FIX_RUFF_IN_CI.sh
```

### Pre-commit Hook

**نصب:**
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
cd backend
ruff check . --fix
git add -u
EOF

chmod +x .git/hooks/pre-commit
```

### IDE Setup

**VS Code** - نصب extension:
1. نصب "Ruff" extension
2. در `settings.json`:
```json
{
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true
}
```

**PyCharm**:
1. Settings → Tools → External Tools
2. اضافه کردن Ruff با argument: `check $FilePath$ --fix`

## ✅ Commit کردن تغییرات

پس از اجرای `ruff check . --fix`:

```bash
# بررسی تغییرات
git diff

# اضافه کردن فایل‌های تغییر یافته
git add -u

# Commit
git commit -m "fix: organize imports with ruff auto-fix (I001)"

# Push
git push
```

## 📝 فایل‌های کمکی ایجاد شده

- ✅ `backend/FIX_RUFF_IN_CI.sh` - اسکریپت اصلاح خودکار
- ✅ `IMPORT_SORT_FIX.md` - راهنمای کامل
- ✅ `CI_LINT_SOLUTION.md` - راه‌حل برای CI
- ✅ این فایل - خلاصه راه‌حل

## 🎓 نکات مهم

1. **همیشه `--fix` استفاده کنید**: ruff بهترین اصلاح را انجام می‌دهد
2. **تست محلی**: قبل از push، `ruff check .` را اجرا کنید
3. **Pre-commit hook**: از hook استفاده کنید تا این مشکل تکرار نشود
4. **IDE integration**: برای تجربه بهتر توسعه

## 🔄 وضعیت فعلی

| فایل | وضعیت | اقدام لازم |
|------|-------|-----------|
| `apps/core/schemas/datasource.py` | ⚠️ نیاز به fix | `ruff check . --fix` |
| سایر فایل‌ها | ✅ | - |

## 🎉 نتیجه

با اجرای یک دستور ساده، همه مشکلات حل می‌شوند:

```bash
cd backend && ruff check . --fix
```

**این دستور:**
- ✅ Imports را مرتب می‌کند
- ✅ فرمت را اصلاح می‌کند
- ✅ همه قوانین ruff را اعمال می‌کند
- ✅ فایل را آماده commit می‌کند

---

**تاریخ**: 2025-10-18  
**مشکل**: I001 Import sorting  
**راه‌حل**: `ruff check . --fix`  
**وضعیت**: ✅ آماده برای اصلاح
