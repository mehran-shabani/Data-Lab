'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ToolAPI, ToolOut, InvokeOut } from '@/lib/api';

const UNKNOWN_ERROR_MESSAGE = 'یک خطای ناشناخته رخ داد.';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function getSampleValueFromSchema(property: Record<string, unknown>): unknown {
  const rawType = property.type;
  const type =
    typeof rawType === 'string'
      ? rawType
      : Array.isArray(rawType)
        ? rawType.find((item): item is string => typeof item === 'string')
        : undefined;

  switch (type) {
    case 'string':
      return '';
    case 'number':
    case 'integer':
      return 0;
    case 'boolean':
      return false;
    case 'array':
      return [];
    case 'object':
      return {};
    default:
      return null;
  }
}

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
    // ignore serialization errors
  }

  return UNKNOWN_ERROR_MESSAGE;
}

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return UNKNOWN_ERROR_MESSAGE;
  }
}

export default function TestToolPage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.id as string;

  const [tool, setTool] = useState<ToolOut | null>(null);
  const [paramsInput, setParamsInput] = useState<string>('{}');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvokeOut | null>(null);
  const [error, setError] = useState('');

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  const loadTool = useCallback(async () => {
    try {
      const data = await ToolAPI.get(orgId, toolId);
      setTool(data);
      // Initialize params from input_schema
      const schemaProperties = (data.input_schema as { properties?: unknown }).properties;
      if (isRecord(schemaProperties)) {
        const properties = schemaProperties as Record<string, unknown>;
        const sampleParams: Record<string, unknown> = {};
        let hasSample = false;

        for (const [key, value] of Object.entries(properties)) {
          if (!isRecord(value)) continue;
          sampleParams[key] = getSampleValueFromSchema(value);
          hasSample = true;
        }

        if (hasSample) {
          setParamsInput(JSON.stringify(sampleParams, null, 2));
        }
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  }, [orgId, toolId]);

  useEffect(() => {
    void loadTool();
  }, [loadTool]);

  async function handleInvoke() {
    setLoading(true);
    setResult(null);
    setError('');

    try {
      const parsedParams = JSON.parse(paramsInput) as Record<string, unknown>;
      const data = await ToolAPI.invoke(orgId, toolId, { params: parsedParams });
      setResult(data);
    } catch (err: unknown) {
      setError(getErrorMessage(err));
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
                  {formatJson(result.data)}
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
                {formatJson(tool.exec_config)}
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
