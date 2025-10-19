'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ToolAPI, ToolOut, InvokeOut } from '@/lib/api';

export default function TestToolPage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.id as string;

  const [tool, setTool] = useState<ToolOut | null>(null);
  const [params Input, setParamsInput] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvokeOut | null>(null);
  const [error, setError] = useState('');

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  useEffect(() => {
    loadTool();
  }, [toolId]);

  async function loadTool() {
    try {
      const data = await ToolAPI.get(orgId, toolId);
      setTool(data);
      // Initialize params from input_schema
      if (data.input_schema && Object.keys(data.input_schema).length > 0) {
        const sampleParams: any = {};
        const properties = data.input_schema.properties || {};
        for (const [key, value] of Object.entries(properties)) {
          const prop = value as any;
          if (prop.type === 'string') sampleParams[key] = '';
          else if (prop.type === 'number' || prop.type === 'integer') sampleParams[key] = 0;
          else sampleParams[key] = null;
        }
        setParamsInput(JSON.stringify(sampleParams, null, 2));
      }
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleInvoke() {
    setLoading(true);
    setResult(null);
    setError('');

    try {
      const params = JSON.parse(paramsInput);
      const data = await ToolAPI.invoke(orgId, toolId, { params });
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!tool) return <div className="p-8">در حال بارگذاری...</div>;

  return (
    <div className="p-8 max-w-4xl" dir="rtl">
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-800"
        >
          ← بازگشت
        </button>
        <h1 className="text-2xl font-bold mt-2">تست ابزار: {tool.name}</h1>
        <p className="text-gray-600 mt-1">نوع: {tool.type} | نسخه: {tool.version}</p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold mb-3">پارامترهای ورودی (JSON)</h2>
          <textarea
            value={paramsInput}
            onChange={(e) => setParamsInput(e.target.value)}
            className="w-full px-3 py-2 border rounded font-mono text-sm"
            rows={8}
            placeholder='{"param1": "value1"}'
            dir="ltr"
          />
        </div>

        <button
          onClick={handleInvoke}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded font-semibold disabled:opacity-50"
        >
          {loading ? 'در حال اجرا...' : 'اجرای ابزار'}
        </button>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-4">
            <p className="text-red-800 font-semibold">خطا</p>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className={`border rounded p-4 ${result.ok ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <div className="flex justify-between items-center mb-2">
                <p className={`font-semibold ${result.ok ? 'text-green-800' : 'text-red-800'}`}>
                  {result.ok ? '✓ موفق' : '✗ ناموفق'}
                </p>
                <span className="text-xs text-gray-600">Trace ID: {result.trace_id}</span>
              </div>
              {result.masked && (
                <p className="text-yellow-700 text-sm">⚠️ برخی فیلدها توسط Policy پنهان شده‌اند</p>
              )}
            </div>

            {result.ok && result.data && (
              <div>
                <h3 className="font-semibold mb-2">نتیجه:</h3>
                <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm font-mono" dir="ltr">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </div>
            )}

            {result.error && (
              <div className="bg-red-50 border border-red-200 rounded p-4">
                <p className="text-red-800 font-semibold">پیام خطا:</p>
                <p className="text-red-600 text-sm mt-1">{result.error}</p>
              </div>
            )}
          </div>
        )}

        {/* Tool Info */}
        <div className="border-t pt-4 mt-6">
          <h3 className="font-semibold mb-3">اطلاعات ابزار</h3>
          <div className="space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <span className="text-gray-600">Execution Config:</span>
              <pre className="text-xs font-mono overflow-auto" dir="ltr">
                {JSON.stringify(tool.exec_config, null, 2)}
              </pre>
            </div>
            {tool.datasource_id && (
              <div className="grid grid-cols-2 gap-2">
                <span className="text-gray-600">DataSource ID:</span>
                <span className="font-mono text-xs">{tool.datasource_id}</span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <span className="text-gray-600">Rate Limit:</span>
              <span>{tool.rate_limit_per_min || 'پیش‌فرض'} فراخوانی در دقیقه</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
