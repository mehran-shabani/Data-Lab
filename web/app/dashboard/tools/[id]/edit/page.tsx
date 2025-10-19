'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ToolAPI, ToolOut, ToolUpdate, DataSourceAPI, DataSourceOut } from '@/lib/api';

export default function EditToolPage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [tool, setTool] = useState<ToolOut | null>(null);
  const [datasources, setDatasources] = useState<DataSourceOut[]>([]);
  const [formData, setFormData] = useState<ToolUpdate>({});

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  useEffect(() => {
    loadData();
  }, [toolId]);

  async function loadData() {
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
    } catch (err: any) {
      alert(`خطا در بارگذاری: ${err.message}`);
      router.back();
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      await ToolAPI.update(orgId, toolId, formData);
      router.push('/dashboard/tools');
    } catch (err: any) {
      alert(`خطا: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!tool) return <div className="p-8">در حال بارگذاری...</div>;

  return (
    <div className="p-8 max-w-4xl" dir="rtl">
      <h1 className="text-2xl font-bold mb-6">ویرایش ابزار: {tool.name}</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">نام ابزار *</label>
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
            value={JSON.stringify(formData.exec_config, null, 2)}
            onChange={(e) => {
              try {
                setFormData({ ...formData, exec_config: JSON.parse(e.target.value) });
              } catch {}
            }}
            className="w-full px-3 py-2 border rounded font-mono text-sm"
            rows={6}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Rate Limit (per minute)</label>
          <input
            type="number"
            value={formData.rate_limit_per_min || ''}
            onChange={(e) => setFormData({ ...formData, rate_limit_per_min: e.target.value ? parseInt(e.target.value) : null })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            checked={formData.enabled || false}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
            className="ml-2"
          />
          <label className="text-sm font-medium">فعال</label>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            {loading ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
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
