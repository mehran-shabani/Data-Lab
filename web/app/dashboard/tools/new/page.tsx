'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ToolAPI, ToolCreate, ToolType, DataSourceAPI, DataSourceOut } from '@/lib/api';

export default function NewToolPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [datasources, setDatasources] = useState<DataSourceOut[]>([]);
  
  const [formData, setFormData] = useState<ToolCreate>({
    name: '',
    version: 'v1',
    type: 'CUSTOM' as ToolType,
    datasource_id: null,
    input_schema: {},
    output_schema: {},
    exec_config: {},
    rate_limit_per_min: 60,
    enabled: true,
  });

  // Mock org_id for MVP
  const orgId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

  useEffect(() => {
    loadDataSources();
  }, []);

  async function loadDataSources() {
    try {
      const data = await DataSourceAPI.list(orgId);
      setDatasources(data);
    } catch (err) {
      console.error('Failed to load datasources:', err);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      await ToolAPI.create(orgId, formData);
      router.push('/dashboard/tools');
    } catch (err: any) {
      alert(`خطا: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl" dir="rtl">
      <h1 className="text-2xl font-bold mb-6">ایجاد ابزار جدید</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">نام ابزار *</label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">نسخه</label>
          <input
            type="text"
            value={formData.version}
            onChange={(e) => setFormData({ ...formData, version: e.target.value })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">نوع ابزار *</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as ToolType })}
            className="w-full px-3 py-2 border rounded"
          >
            <option value="CUSTOM">سفارشی (CUSTOM)</option>
            <option value="POSTGRES_QUERY">پرس و جوی PostgreSQL</option>
            <option value="REST_CALL">فراخوانی REST</option>
          </select>
        </div>

        {(formData.type === 'POSTGRES_QUERY' || formData.type === 'REST_CALL') && (
          <div>
            <label className="block text-sm font-medium mb-1">DataSource</label>
            <select
              value={formData.datasource_id || ''}
              onChange={(e) => setFormData({ ...formData, datasource_id: e.target.value || null })}
              className="w-full px-3 py-2 border rounded"
            >
              <option value="">انتخاب کنید</option>
              {datasources.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.type})
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Input Schema (JSON)</label>
          <textarea
            value={JSON.stringify(formData.input_schema, null, 2)}
            onChange={(e) => {
              try {
                setFormData({ ...formData, input_schema: JSON.parse(e.target.value) });
              } catch {}
            }}
            className="w-full px-3 py-2 border rounded font-mono text-sm"
            rows={4}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Output Schema (JSON)</label>
          <textarea
            value={JSON.stringify(formData.output_schema, null, 2)}
            onChange={(e) => {
              try {
                setFormData({ ...formData, output_schema: JSON.parse(e.target.value) });
              } catch {}
            }}
            className="w-full px-3 py-2 border rounded font-mono text-sm"
            rows={4}
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
            placeholder={
              formData.type === 'POSTGRES_QUERY'
                ? '{"query_template": "SELECT * FROM table WHERE id = %(id)s"}'
                : formData.type === 'REST_CALL'
                ? '{"method": "GET", "path": "/api/endpoint/{id}", "timeout_ms": 3000}'
                : '{}'
            }
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
            checked={formData.enabled}
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
            {loading ? 'در حال ذخیره...' : 'ذخیره'}
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
