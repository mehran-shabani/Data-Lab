#!/bin/bash
# اسکریپت بررسی و اصلاح lint با ruff

set -e

echo "🔍 بررسی lint با ruff..."
echo ""

# رنگ‌ها برای خروجی
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# بررسی نصب ruff
if ! command -v ruff &> /dev/null; then
    echo -e "${RED}❌ ruff نصب نیست${NC}"
    echo "نصب ruff:"
    echo "  pip install ruff"
    exit 1
fi

echo -e "${YELLOW}📋 اجرای ruff check...${NC}"
if ruff check .; then
    echo -e "${GREEN}✅ هیچ خطای lint پیدا نشد!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  خطاهای lint پیدا شد${NC}"
    echo ""
    echo "برای اصلاح خودکار:"
    echo "  ruff check . --fix"
    echo ""
    exit 1
fi

echo ""
echo -e "${YELLOW}📐 بررسی formatting...${NC}"
if ruff format --check .; then
    echo -e "${GREEN}✅ فرمت کد صحیح است!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  کد نیاز به formatting دارد${NC}"
    echo ""
    echo "برای اصلاح خودکار:"
    echo "  ruff format ."
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 همه چیز عالی است!${NC}"
