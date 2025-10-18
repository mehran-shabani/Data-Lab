'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface UserInfo {
  email: string
  org_id: string
  roles: string[]
}

export default function Dashboard() {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const router = useRouter()

  useEffect(() => {
    async function checkAuth() {
      try {
        // Check if authenticated by calling /me
        const response = await fetch('http://localhost:8000/me', {
          credentials: 'include',
        })

        if (!response.ok) {
          // Not authenticated, redirect to signin
          router.push('/signin')
          return
        }

        const userData = await response.json()
        setUser(userData)

        // Also check health
        const healthResponse = await fetch('http://localhost:8000/healthz')
        if (healthResponse.ok) {
          setHealthStatus('✓ Connected')
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        router.push('/signin')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">در حال بارگذاری...</p>
        </div>
      </div>
    )
  }
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

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <h3 className="text-xl font-semibold mb-4">خوش آمدید{user ? ` ${user.email}` : ''}</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              این داشبورد در حال توسعه است. قابلیت‌های بیشتر در پرامپت‌های بعدی اضافه خواهد شد.
            </p>
            {user && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded p-4 mb-4">
                <h4 className="font-semibold mb-2">اطلاعات کاربری:</h4>
                <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <li><strong>ایمیل:</strong> {user.email}</li>
                  <li><strong>سازمان:</strong> {user.org_id}</li>
                  <li><strong>نقش‌ها:</strong> {user.roles.join(', ')}</li>
                </ul>
              </div>
            )}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-800 rounded p-3 mb-4">
              <p className="text-sm text-green-800 dark:text-green-300">
                <strong>وضعیت Backend:</strong> {healthStatus}
              </p>
            </div>
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
