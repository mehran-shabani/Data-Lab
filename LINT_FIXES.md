# اصلاحات Lint (Ruff) - Backend

## خلاصه اصلاحات

همه خطاهای lint که توسط ruff شناسایی شدند، برطرف شدند.

### تعداد خطاها: 8
### تعداد فایل‌های اصلاح شده: 5
### وضعیت: ✅ همه اصلاح شده

---

## جزئیات اصلاحات

### ۱. `apps/connectors/repo.py` ✅

**خطاها:**
- F401: `typing.Any` imported but unused
- F401: `sqlalchemy.orm.selectinload` imported but unused

**اصلاح:**
```python
# قبل
from typing import Any
from sqlalchemy.orm import selectinload

# بعد
# حذف شدند (استفاده نمی‌شدند)
```

---

### ۲. `apps/connectors/router.py` ✅

**خطا:**
- F401: `typing.Annotated` imported but unused

**اصلاح:**
```python
# قبل
from typing import Annotated

# بعد
# حذف شد (استفاده نمی‌شد)
```

---

### ۳. `apps/core/schemas/datasource.py` ✅

**خطاها:**
- I001: Import block is un-sorted or un-formatted
- F401: `typing.Any` imported but unused
- F401: `pydantic.field_validator` imported but unused

**اصلاح:**
```python
# قبل
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# بعد
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
```

**توضیح:**
- `Any` حذف شد (استفاده نمی‌شد)
- `field_validator` حذف شد (فقط `model_validator` استفاده می‌شد)
- ترتیب imports مرتب شد

---

### ۴. `tests/test_datasource_connectivity.py` ✅

**خطا:**
- I001: Import block is un-sorted or un-formatted

**اصلاح:**
```python
# قبل
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from apps.core import app as fastapi_app
from apps.core.models import Membership, Organization, User
from apps.core.security import create_access_token

# بعد
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from apps.core import app as fastapi_app
from apps.core.models import Membership, Organization, User
from apps.core.security import create_access_token
```

**توضیح:**
- Imports مرتب شدند طبق استاندارد:
  1. Standard library (unittest.mock)
  2. Third-party (pytest, httpx)
  3. Local (apps.core.*)
- Items درون هر import نیز الفبایی شدند

---

### ۵. `tests/test_datasource_crud.py` ✅

**خطا:**
- F401: `apps.core.models.DataSource` imported but unused

**اصلاح:**
```python
# قبل
from apps.core.models import DataSource, Membership, Organization, User

# بعد
from apps.core.models import Membership, Organization, User
```

**توضیح:**
- `DataSource` در تست‌ها استفاده نمی‌شد (فقط از طریق API تست می‌شد)

---

## قوانین Ruff مرتبط

### F401: Unused Import
Import هایی که در کد استفاده نمی‌شوند باید حذف شوند.

**چرا مهم است:**
- کد تمیزتر و قابل خواندن‌تر
- کاهش حجم bundle
- عدم confusion برای توسعه‌دهندگان

### I001: Import Sorting
Import ها باید به ترتیب زیر مرتب شوند:

1. **Standard library**: ماژول‌های داخلی Python
2. **Third-party**: کتابخانه‌های خارجی
3. **Local**: ماژول‌های پروژه

**مثال صحیح:**
```python
# Standard library
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

# Third-party
import pytest
from fastapi import APIRouter
from pydantic import BaseModel

# Local
from apps.core.models import User
from apps.core.security import create_token
```

---

## تست اصلاحات

### اجرای Ruff

```bash
cd backend

# بررسی lint
ruff check .

# اصلاح خودکار (در صورت نیاز)
ruff check . --fix

# فرمت کردن کد
ruff format .
```

**خروجی مورد انتظار:**
```
All checks passed!
```

### اجرای تست‌ها

```bash
cd backend

# اطمینان از عدم شکستن تست‌ها
pytest -v
```

---

## تنظیمات Ruff

تنظیمات ruff در `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults (FastAPI Depends)
]

[tool.ruff.lint.isort]
known-first-party = ["apps"]
```

---

## پیشگیری از خطاهای آینده

### ۱. Pre-commit Hook

ایجاد `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
ruff check . --fix
ruff format .
```

### ۲. IDE Integration

**VS Code** (`settings.json`):
```json
{
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true
}
```

**PyCharm**:
- Settings → Tools → External Tools → Add Ruff

### ۳. CI/CD Check

در GitHub Actions workflow:

```yaml
- name: Lint with ruff
  run: |
    cd backend
    pip install ruff
    ruff check .
    ruff format --check .
```

---

## خلاصه تغییرات

| فایل | خطاها | اصلاحات |
|------|-------|---------|
| `apps/connectors/repo.py` | 2 | حذف 2 import استفاده نشده |
| `apps/connectors/router.py` | 1 | حذف 1 import استفاده نشده |
| `apps/core/schemas/datasource.py` | 3 | حذف 2 import + مرتب‌سازی |
| `tests/test_datasource_connectivity.py` | 1 | مرتب‌سازی imports |
| `tests/test_datasource_crud.py` | 1 | حذف 1 import استفاده نشده |
| **جمع** | **8** | **8 اصلاح** |

---

## نتیجه

✅ **همه خطاهای lint برطرف شدند**

- کد تمیزتر و استانداردتر
- قابل نگهداری بهتر
- آماده برای CI/CD
- مطابق با best practices Python

---

**تاریخ**: 2025-10-18  
**ابزار**: Ruff v0.1.0+  
**Python**: 3.11+
