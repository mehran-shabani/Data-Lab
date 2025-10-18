# حل مشکل Import Sorting - Ruff I001

تاریخ: 2025-10-18

## مشکل

در CI، خطای زیر دیده می‌شود:

```
I001 [*] Import block is un-sorted or un-formatted
 --> apps/core/schemas/datasource.py:3:1
```

## علت

Ruff از قوانین `isort` برای مرتب‌سازی imports استفاده می‌کند. استاندارد صحیح:

```python
"""Module docstring."""

# 1. Standard library imports (مرتب‌شده الفبایی)
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

# 2. یک خط خالی

# 3. Third-party imports (مرتب‌شده الفبایی)
from pydantic import BaseModel, Field, model_validator

# 4. یک خط خالی

# 5. کد شروع می‌شود
```

## راه‌حل

### گزینه 1: اجازه دادن به Ruff برای اصلاح خودکار (توصیه می‌شود)

```bash
cd backend
ruff check . --fix
```

این دستور تمام مشکلات fixable را به صورت خودکار حل می‌کند.

### گزینه 2: اصلاح دستی

فایل `apps/core/schemas/datasource.py` باید به این شکل باشد:

```python
"""Pydantic schemas for DataSource management."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ===== Base Schemas =====
```

**نکات مهم:**
- دقیقاً یک خط خالی بین docstring و imports
- دقیقاً یک خط خالی بین standard library و third-party
- دقیقاً یک خط خالی بین imports و کد

## تست اصلاح

```bash
cd backend

# بررسی
ruff check apps/core/schemas/datasource.py

# یا همه فایل‌ها
ruff check .
```

**خروجی مورد انتظار:**
```
All checks passed!
```

## اضافه کردن به CI/CD

در GitHub Actions workflow، اگر می‌خواهید خودکار fix شود:

```yaml
- name: Lint with ruff
  run: |
    cd backend
    pip install ruff
    ruff check . --fix
    # بررسی اینکه آیا تغییری ایجاد شد
    if ! git diff --quiet; then
      echo "Ruff made fixes. Please run 'ruff check --fix' locally."
      git diff
      exit 1
    fi
```

یا فقط بررسی (بدون fix):

```yaml
- name: Lint with ruff
  run: |
    cd backend
    pip install ruff
    ruff check .
```

## Pre-commit Hook

برای جلوگیری از این مشکل در آینده:

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd backend
ruff check . --fix
git add -u  # اضافه کردن تغییرات fix شده
```

## تنظیمات Ruff

در `pyproject.toml`:

```toml
[tool.ruff.lint.isort]
known-first-party = ["apps"]
```

این به ruff می‌گوید که ماژول‌های `apps.*` را به عنوان first-party (local) در نظر بگیرد.

## نتیجه

با اجرای `ruff check . --fix`، همه مشکلات import sorting حل می‌شود.

---

**راه‌حل سریع:**
```bash
cd backend
ruff check . --fix
git add -u
git commit -m "fix: organize imports with ruff"
```
