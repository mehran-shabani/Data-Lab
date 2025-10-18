#!/bin/bash
# اسکریپت حل مشکل TypeCheck

echo "🔧 حل مشکل TypeScript..."

# پاک کردن cache
echo "1️⃣ پاک کردن cache..."
rm -rf node_modules .next

# نصب مجدد وابستگی‌ها
echo "2️⃣ نصب مجدد وابستگی‌ها..."
npm install

# اجرای typecheck
echo "3️⃣ اجرای typecheck..."
npm run typecheck

echo "✅ تمام!"
