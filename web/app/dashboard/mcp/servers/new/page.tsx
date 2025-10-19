'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MCPServerAPI, MCPServerCreate } from '@/lib/api';

export default function NewMCPServerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [apiKey, setApiKey] = useState<string | null>(null);

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const payload: MCPServerCreate = { name };
      const result = await MCPServerAPI.create(orgId, payload);
      
      // Show API key (one-time display)
      if (result.plain_api_key) {
        setApiKey(result.plain_api_key);
      }
    } catch (err: any) {
      alert(`خطا: ${err.message}`);
      setLoading(false);
    }
  }

  function handleCopyKey() {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      alert('کلید کپی شد!');
    }
  }

  if (apiKey) {
    return (
      <div className="p-8 max-w-2xl" dir="rtl">
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
          <h2 className="text-xl font-bold text-green-800 mb-4">✓ سرور با موفقیت ایجاد شد</h2>
          
          <div className="bg-white p-4 rounded border border-yellow-400">
            <p className="text-red-600 font-semibold mb-2">⚠️ توجه: این کلید فقط یک بار نمایش داده می‌شود!</p>
            <p className="text-sm text-gray-700 mb-3">لطفاً کلید زیر را در مکانی امن ذخیره کنید:</p>
            
            <div className="bg-gray-100 p-3 rounded font-mono text-sm break-all" dir="ltr">
              {apiKey}
            </div>
            
            <button
              onClick={handleCopyKey}
              className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
            >
              کپی کلید
            </button>
          </div>
          
          <button
            onClick={() => router.push('/dashboard/mcp/servers')}
            className="mt-6 bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
          >
            بازگشت به لیست
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl" dir="rtl">
      <h1 className="text-2xl font-bold mb-6">ایجاد MCP Server جدید</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">نام سرور *</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            placeholder="مثلاً: Production MCP Server"
          />
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-sm">
          <p className="font-semibold text-yellow-800 mb-1">نکته مهم:</p>
          <p className="text-yellow-700">
            پس از ایجاد سرور، یک API Key یکبار-مصرف نمایش داده می‌شود. این کلید را در جای امنی ذخیره کنید زیرا دیگر قابل بازیابی نیست.
          </p>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            {loading ? 'در حال ایجاد...' : 'ایجاد سرور'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="bg-gray-300 hover:bg-gray-400 px-6 py-2 rounded"
          >
            انصراف
          </button>
        </div>
      </form>
    </div>
  );
}
