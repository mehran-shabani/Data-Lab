import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-center">
        <h1 className="text-6xl font-bold mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Farda MCP
        </h1>
        <p className="text-xl mb-12 text-gray-600 dark:text-gray-300">
          سامانه مدیریت چندمستأجری با پروتکل MCP
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link 
            href="/dashboard"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            ورود به داشبورد
          </Link>
          <Link 
            href="/signin"
            className="px-6 py-3 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            ورود به سیستم
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="p-6 border border-gray-200 dark:border-gray-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">⚡ سریع و کارآمد</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              معماری Async با FastAPI و Next.js
            </p>
          </div>
          <div className="p-6 border border-gray-200 dark:border-gray-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">🔒 امن</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              احراز هویت چندلایه و RBAC
            </p>
          </div>
          <div className="p-6 border border-gray-200 dark:border-gray-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">🌐 چندمستأجری</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              جداسازی کامل داده‌ها و منابع
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
