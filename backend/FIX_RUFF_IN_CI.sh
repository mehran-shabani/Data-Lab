#!/bin/bash
# اسکریپت سریع برای رفع مشکلات ruff قبل از commit

set -e

echo "🔧 اصلاح خودکار مشکلات ruff..."

# نصب ruff اگر نصب نیست
if ! command -v ruff &> /dev/null; then
    echo "📦 نصب ruff..."
    pip install ruff
fi

# اصلاح خودکار مشکلات
echo "✨ اجرای ruff check --fix..."
ruff check . --fix

# فرمت کردن کد
echo "📐 فرمت کردن کد..."
ruff format .

# بررسی نهایی
echo "✅ بررسی نهایی..."
if ruff check .; then
    echo ""
    echo "🎉 همه چیز تمیز است!"
    echo ""
    echo "تغییرات اعمال شده:"
    git diff --stat
    echo ""
    echo "برای commit کردن:"
    echo "  git add -u"
    echo "  git commit -m 'fix: organize imports and format code with ruff'"
else
    echo ""
    echo "⚠️  برخی مشکلات نیاز به اصلاح دستی دارند"
    exit 1
fi
