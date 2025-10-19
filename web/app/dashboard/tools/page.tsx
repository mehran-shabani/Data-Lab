'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ToolAPI, ToolOut } from '@/lib/api';

export default function ToolsPage() {
  const router = useRouter();
  const [tools, setTools] = useState<ToolOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  useEffect(() => {
    loadTools();
  }, []);

  async function loadTools() {
    try {
      setLoading(true);
      const data = await ToolAPI.list(orgId);
      setTools(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(toolId: string) {
    if (!confirm('آیا از حذف این ابزار مطمئن هستید؟')) return;

    try {
      await ToolAPI.delete(orgId, toolId);
      await loadTools();
    } catch (err: any) {
      alert(`خطا: ${err.message}`);
    }
  }

  if (loading) return <div className="p-8">در حال بارگذاری...</div>;
  if (error) return <div className="p-8 text-red-600">خطا: {error}</div>;

  return (
    <div className="p-8" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">مدیریت ابزارها</h1>
        <button
          onClick={() => router.push('/dashboard/tools/new')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          ابزار جدید
        </button>
      </div>

      {tools.length === 0 ? (
        <p className="text-gray-600">هیچ ابزاری یافت نشد</p>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">نام</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">نوع</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">نسخه</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">وضعیت</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Rate Limit</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">عملیات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tools.map((tool) => (
                <tr key={tool.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{tool.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                      {tool.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{tool.version}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {tool.enabled ? (
                      <span className="text-green-600">فعال</span>
                    ) : (
                      <span className="text-red-600">غیرفعال</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {tool.rate_limit_per_min || 'پیش‌فرض'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2 space-x-reverse">
                    <button
                      onClick={() => router.push(`/dashboard/tools/${tool.id}/test`)}
                      className="text-green-600 hover:text-green-900"
                    >
                      تست
                    </button>
                    <button
                      onClick={() => router.push(`/dashboard/tools/${tool.id}/edit`)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      ویرایش
                    </button>
                    <button
                      onClick={() => handleDelete(tool.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      حذف
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
