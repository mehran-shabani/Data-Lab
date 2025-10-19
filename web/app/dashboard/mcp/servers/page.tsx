'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MCPServerAPI, MCPServerOut } from '@/lib/api';

export default function MCPServersPage() {
  const router = useRouter();
  const [servers, setServers] = useState<MCPServerOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  useEffect(() => {
    loadServers();
  }, []);

  async function loadServers() {
    try {
      setLoading(true);
      const data = await MCPServerAPI.list(orgId);
      setServers(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleStatus(serverId: string, currentStatus: string) {
    const newStatus = currentStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED';
    const action = newStatus === 'ENABLED' ? MCPServerAPI.enable : MCPServerAPI.disable;

    try {
      await action(orgId, serverId);
      await loadServers();
    } catch (err: any) {
      alert(`خطا: ${err.message}`);
    }
  }

  if (loading) return <div className="p-8">در حال بارگذاری...</div>;
  if (error) return <div className="p-8 text-red-600">خطا: {error}</div>;

  return (
    <div className="p-8" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">مدیریت MCP Servers</h1>
        <button
          onClick={() => router.push('/dashboard/mcp/servers/new')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          سرور جدید
        </button>
      </div>

      {servers.length === 0 ? (
        <p className="text-gray-600">هیچ سروری یافت نشد</p>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">نام</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">وضعیت</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">تاریخ ایجاد</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">عملیات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {servers.map((server) => (
                <tr key={server.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{server.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {server.status === 'ENABLED' ? (
                      <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">فعال</span>
                    ) : (
                      <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-800">غیرفعال</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {new Date(server.created_at).toLocaleDateString('fa-IR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2 space-x-reverse">
                    <button
                      onClick={() => router.push(`/dashboard/mcp/servers/${server.id}`)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      جزئیات
                    </button>
                    <button
                      onClick={() => handleToggleStatus(server.id, server.status)}
                      className={server.status === 'ENABLED' ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                    >
                      {server.status === 'ENABLED' ? 'غیرفعال' : 'فعال'}
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
