'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [orgName, setOrgName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/dev-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          org_name: orgName,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Login failed')
      }

      // Redirect to dashboard on success
      router.push('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold">
            ورود به سیستم
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            با حساب کاربری خود وارد شوید
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                ایمیل
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                className="appearance-none rounded-t-md relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white dark:bg-gray-800 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm disabled:opacity-50"
                placeholder="ایمیل"
              />
            </div>
            <div>
              <label htmlFor="org_name" className="sr-only">
                نام سازمان
              </label>
              <input
                id="org_name"
                name="org_name"
                type="text"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                disabled={isLoading}
                className="appearance-none rounded-b-md relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white dark:bg-gray-800 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm disabled:opacity-50"
                placeholder="نام سازمان"
              />
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-800 rounded p-3">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <strong>توجه:</strong> این فرم ورود توسعه‌دهنده است. فقط در محیط‌های local و CI فعال است.
            </p>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'در حال ورود...' : 'ورود'}
            </button>
          </div>

          <div className="text-center">
            <Link href="/" className="text-sm text-blue-600 hover:text-blue-500">
              بازگشت به صفحه اصلی
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
