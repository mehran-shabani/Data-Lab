'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ToolAPI, ToolOut, ToolUpdate, DataSourceAPI, DataSourceOut } from '@/lib/api';

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

function stringifyJson(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return '{}';
  }
}

export default function EditToolPage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [tool, setTool] = useState<ToolOut | null>(null);
  const [, setDatasources] = useState<DataSourceOut[]>([]);
  const [formData, setFormData] = useState<ToolUpdate>({});

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  const loadData = useCallback(async () => {
    try {
      const [toolData, dsData] = await Promise.all([
        ToolAPI.get(orgId, toolId),
        DataSourceAPI.list(orgId),
      ]);

      setTool(toolData);
      setDatasources(dsData);
      setFormData({
        name: toolData.name,
        version: toolData.version,
        type: toolData.type,
        datasource_id: toolData.datasource_id,
        input_schema: toolData.input_schema,
        output_schema: toolData.output_schema,
        exec_config: toolData.exec_config,
        rate_limit_per_min: toolData.rate_limit_per_min,
        enabled: toolData.enabled,
      });
    } catch (err: unknown) {
      alert(`�� �� ���?���?: ${getErrorMessage(err)}`);
      router.back();
    }
  }, [orgId, router, toolId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      await ToolAPI.update(orgId, toolId, formData);
      router.push('/dashboard/tools');
    } catch (err: unknown) {
      alert(`��: ${getErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  }

  if (!tool) return <div className="p-8">�� ��� ���?���?...</div>;

  return (
    <div className="p-8 max-w-4xl" dir="rtl">
      <h1 className="text-2xl font-bold mb-6">�?��?� �����: {tool.name}</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">�� ����� *</label>
          <input
            type="text"
            required
            value={formData.name || ''}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Execution Config (JSON)</label>
          <textarea
            value={stringifyJson(formData.exec_config)}
            onChange={(e) => {
              try {
                setFormData({ ...formData, exec_config: JSON.parse(e.target.value) });
              } catch {
                // ignore invalid JSON edits until they are valid
              }
            }}
            className="w-full px-3 py-2 border rounded font-mono text-sm"
            rows={6}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Rate Limit (per minute)</label>
          <input
            type="number"
            value={formData.rate_limit_per_min ?? ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                rate_limit_per_min: e.target.value ? parseInt(e.target.value, 10) : null,
              })
            }
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            checked={formData.enabled ?? false}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
            className="ml-2"
          />
          <label className="text-sm font-medium">���</label>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            {loading ? '�� ��� ��?��...' : '��?�� ��??���'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="bg-gray-300 hover:bg-gray-400 px-6 py-2 rounded"
          >
            �뭩��
          </button>
        </div>
      </form>
    </div>
  );
}
