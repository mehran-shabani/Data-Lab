'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { MCPServerAPI, MCPServerOut } from '@/lib/api';

const UNKNOWN_ERROR_MESSAGE = 'خطای ناشناخته رخ داد.';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  if (typeof error === 'string' && error.trim().length > 0) {
    return error;
  }

  try {
    const serialized = JSON.stringify(error);
    if (serialized !== undefined) {
      return serialized;
    }
  } catch {
    // ignore serialization issues
  }

  return UNKNOWN_ERROR_MESSAGE;
}

export default function MCPServerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = params.id as string;

  const [server, setServer] = useState<MCPServerOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  const loadServer = useCallback(async () => {
    setLoading(true);
    try {
      const data = await MCPServerAPI.get(orgId, serverId);
      setServer(data);
    } catch (err: unknown) {
      alert(`خطا: ${getErrorMessage(err)}`);
      router.back();
    } finally {
      setLoading(false);
    }
  }, [orgId, router, serverId]);

  useEffect(() => {
    void loadServer();
  }, [loadServer]);

  async function handleRotateKey() {
    if (!confirm('آیا از گردش کلید API مطمئن هستید؟ کلید فعلی غیرفعال خواهد شد.')) return;

    try {
      const result = await MCPServerAPI.rotateKey(orgId, serverId);
      setNewApiKey(result.plain_api_key || null);
      await loadServer();
    } catch (err: unknown) {
      alert(`خطا: ${getErrorMessage(err)}`);
    }
  }

  function handleCopyKey() {
    if (newApiKey) {
      navigator.clipboard.writeText(newApiKey);
      alert('کلید جدید کپی شد!');
    }
  }

  if (loading) return <div className="p-8">در حال بارگذاری...</div>;
  if (!server) return null;

  return (
    <div className="p-8 max-w-3xl" dir="rtl">
      <button
        onClick={() => router.back()}
        className="text-blue-600 hover:text-blue-800 mb-4"
      >
        ← بازگشت
      </button>

      <h1 className="text-2xl font-bold mb-6">جزئیات MCP Server</h1>

      {newApiKey && (
        <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4 mb-6">
          <p className="text-red-600 font-semibold mb-2">این کلید جدید است - آن را در جای امن ذخیره کنید!</p>
          <div className="bg-white p-3 rounded font-mono text-sm break-all" dir="ltr">
            {newApiKey}
          </div>
          <button
            onClick={handleCopyKey}
            className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
          >
            کپی کلید
          </button>
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">نام سرویس</p>
            <p className="font-semibold">{server.name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">وضعیت</p>
            {server.status === 'ENABLED' ? (
              <span className="inline-block px-3 py-1 text-sm rounded bg-green-100 text-green-800">فعال</span>
            ) : (
              <span className="inline-block px-3 py-1 text-sm rounded bg-red-100 text-red-800">غیرفعال</span>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-600">تاریخ ایجاد</p>
            <p>{new Date(server.created_at).toLocaleString('fa-IR')}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">آخرین بروزرسانی</p>
            <p>{new Date(server.updated_at).toLocaleString('fa-IR')}</p>
          </div>
        </div>

        <div className="border-t pt-4 mt-6 space-y-3">
          <h2 className="font-semibold text-lg">عملیات</h2>
          
          <button
            onClick={handleRotateKey}
            className="block w-full bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded"
          >
            گردش کلید API (Rotate Key)
          </button>

          <p className="text-sm text-gray-600">
            با گردش کلید، کلید قبلی بلافاصله غیرفعال می‌شود و تنها این کلید جدید معتبر خواهد بود.
          </p>
        </div>
      </div>
    </div>
  );
}
