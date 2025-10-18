# راه‌حل سریع برای خطای Ruff در CI

## مشکل

```
I001 [*] Import block is un-sorted or un-formatted
Found 1 error.
[*] 1 fixable with the `--fix` option.
```

## راه‌حل سریع ⚡

### گزینه 1: اجرای اسکریپت خودکار (سریع‌ترین)

```bash
cd backend
./FIX_RUFF_IN_CI.sh
```

این اسکریپت:
- ✅ ruff را نصب می‌کند (اگر نباشد)
- ✅ همه مشکلات fixable را اصلاح می‌کند
- ✅ کد را format می‌کند
- ✅ بررسی نهایی انجام می‌دهد

### گزینه 2: دستی

```bash
cd backend

# نصب ruff
pip install ruff

# اصلاح خودکار
ruff check . --fix

# فرمت کردن
ruff format .

# بررسی
ruff check .
```

### گزینه 3: فقط فایل مشکل‌دار

```bash
cd backend
ruff check apps/core/schemas/datasource.py --fix
```

## Commit کردن تغییرات

```bash
git add -u
git commit -m "fix: organize imports with ruff auto-fix"
git push
```

## چرا این اتفاق می‌افتد؟

Ruff در CI با تنظیمات دقیق اجرا می‌شود و imports باید دقیقاً طبق استاندارد `isort` مرتب شوند:

```python
# ✅ صحیح
"""Module docstring."""

from datetime import datetime  # Standard library
from typing import Literal
from uuid import UUID

from pydantic import BaseModel  # Third-party


# کد شروع می‌شود
```

## پیشگیری در آینده

### Pre-commit Hook

ایجاد `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend && ruff check . --fix && ruff format .
```

### IDE Integration

**VS Code** - `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff"
}
```

**PyCharm**:
Settings → Tools → External Tools → Ruff

## تست محلی قبل از Push

```bash
cd backend

# بررسی lint
ruff check .

# در صورت خطا
ruff check . --fix

# بررسی فرمت
ruff format --check .

# اعمال فرمت
ruff format .
```

## نتیجه

با اجرای `ruff check . --fix`, همه مشکلات import sorting و formatting حل می‌شوند.

---

**Quick Fix:**
```bash
cd backend && pip install ruff && ruff check . --fix && git add -u
```
