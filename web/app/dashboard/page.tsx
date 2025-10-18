import Link from 'next/link'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Farda MCP</h1>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                خانه
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-3xl font-bold mb-8">داشبورد</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">تنانت‌ها</div>
              <div className="text-3xl font-bold">0</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">کاربران</div>
              <div className="text-3xl font-bold">0</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">اتصالات MCP</div>
              <div className="text-3xl font-bold">0</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">درخواست‌ها</div>
              <div className="text-3xl font-bold">0</div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">خوش آمدید</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              این داشبورد در حال توسعه است. قابلیت‌های بیشتر در پرامپت‌های بعدی اضافه خواهد شد.
            </p>
            <div className="flex gap-3">
              <button type="button" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                شروع کنید
              </button>
              <button type="button" className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                مستندات
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
