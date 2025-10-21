'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getDataSource,
  getDataSourceMetrics,
  pingDataSource,
  sampleDataSource,
  deleteDataSource,
  type DataSourceOut,
  type DataSourceMetrics,
} from '@/lib/api';

type Tab = 'overview' | 'metrics' | 'playground';

export default function DataSourceDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const dsId = params?.id as string;

  const [orgId, setOrgId] = useState<string | null>(null);
  const [datasource, setDatasource] = useState<DataSourceOut | null>(null);
  const [metrics, setMetrics] = useState<DataSourceMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Ping state
  const [pinging, setPinging] = useState(false);
  const [pingResult, setPingResult] = useState<{ ok: boolean; details: string } | null>(null);

  // Sample state
  const [sampling, setSampling] = useState(false);
  const [sampleParams, setSampleParams] = useState('{}');
  const [sampleResult, setSampleResult] = useState<any>(null);

  // Delete state
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/signin');
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setOrgId(payload.org_id);
    } catch (e) {
      console.error('Failed to decode token', e);
      router.push('/signin');
    }
  }, [router]);

  useEffect(() => {
    if (orgId && dsId) {
      loadData();
    }
  }, [orgId, dsId]);

  const loadData = async () => {
    if (!orgId) return;

    setLoading(true);
    setError(null);

    try {
      const [ds, met] = await Promise.all([
        getDataSource(orgId, dsId),
        getDataSourceMetrics(orgId, dsId),
      ]);
      setDatasource(ds);
      setMetrics(met);
    } catch (err: any) {
      setError(err.message || 'خطا در بارگذاری داده‌ها');
    } finally {
      setLoading(false);
    }
  };

  const handlePing = async () => {
    if (!orgId) return;

    setPinging(true);
    setPingResult(null);
    setError(null);

    try {
      const result = await pingDataSource(orgId, dsId);
      setPingResult(result);
      
      // Reload metrics after ping
      const met = await getDataSourceMetrics(orgId, dsId);
      setMetrics(met);
    } catch (err: any) {
      setError(err.message || 'خطا در ping');
    } finally {
      setPinging(false);
    }
  };

  const handleSample = async () => {
    if (!orgId) return;

    setSampling(true);
    setSampleResult(null);
    setError(null);

    try {
      const params = JSON.parse(sampleParams);
      const result = await sampleDataSource(orgId, dsId, params);
      setSampleResult(result);
      
      // Reload metrics
      const met = await getDataSourceMetrics(orgId, dsId);
      setMetrics(met);
    } catch (err: any) {
      setError(err.message || 'خطا در اجرای sample');
      setSampleResult({ error: err.message });
    } finally {
      setSampling(false);
    }
  };

  const handleDelete = async () => {
    if (!orgId) return;

    if (!confirm('آیا از حذف این منبع داده اطمینان دارید؟')) {
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      await deleteDataSource(orgId, dsId);
      router.push('/dashboard/datasources');
    } catch (err: any) {
      setError(err.message || 'خطا در حذف منبع داده');
      setDeleting(false);
    }
  };

  const formatTimestamp = (ts: number | null) => {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleString('fa-IR');
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'CLOSED':
        return 'bg-green-100 text-green-800';
      case 'OPEN':
        return 'bg-red-100 text-red-800';
      case 'HALF_OPEN':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center" dir="rtl">
        <div className="text-gray-600">در حال بارگذاری...</div>
      </div>
    );
  }

  if (!datasource) {
    return (
      <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
        <div className="max-w-6xl mx-auto">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            منبع داده یافت نشد
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/datasources" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← بازگشت به لیست
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{datasource.name}</h1>
              <p className="text-gray-600 mt-2">نوع: {datasource.type}</p>
            </div>
            <div className="flex gap-2">
              <Link
                href={`/dashboard/datasources/${dsId}/edit`}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                ویرایش
              </Link>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-red-400 transition-colors"
              >
                {deleting ? 'در حال حذف...' : 'حذف'}
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex gap-4">
            {[
              { id: 'overview', label: 'نمای کلی' },
              { id: 'metrics', label: 'متریک‌ها' },
              { id: 'playground', label: 'Playground' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Tab)}
                className={`px-4 py-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">اطلاعات پایه</h2>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="font-medium text-gray-700">شناسه</dt>
                  <dd className="text-gray-900 font-mono text-sm">{datasource.id}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-700">نسخه Schema</dt>
                  <dd className="text-gray-900">{datasource.schema_version}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-700">تاریخ ایجاد</dt>
                  <dd className="text-gray-900">{new Date(datasource.created_at).toLocaleString('fa-IR')}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-700">آخرین بروزرسانی</dt>
                  <dd className="text-gray-900">{new Date(datasource.updated_at).toLocaleString('fa-IR')}</dd>
                </div>
              </dl>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">وضعیت اتصال</h2>
              
              {pingResult && (
                <div
                  className={`mb-4 p-4 border rounded-lg ${
                    pingResult.ok
                      ? 'bg-green-50 border-green-200 text-green-700'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  <div className="font-medium">
                    {pingResult.ok ? '✓ اتصال موفق' : '✗ اتصال ناموفق'}
                  </div>
                  <div className="text-sm mt-1">{pingResult.details}</div>
                </div>
              )}

              {metrics && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-700">وضعیت Circuit Breaker:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStateColor(metrics.state)}`}>
                      {metrics.state}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">آخرین اتصال موفق:</span>
                      <span className="mr-2 text-gray-900">{formatTimestamp(metrics.last_ok_ts)}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">آخرین خطا:</span>
                      <span className="mr-2 text-gray-900">{formatTimestamp(metrics.last_err_ts)}</span>
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={handlePing}
                disabled={pinging}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
              >
                {pinging ? 'در حال تست...' : '🔍 تست اتصال'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'metrics' && metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">تعداد کل فراخوانی‌ها</h3>
              <p className="text-3xl font-bold text-gray-900">{metrics.calls_total}</p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">تعداد خطاها</h3>
              <p className="text-3xl font-bold text-red-600">{metrics.errors_total}</p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">میانگین تأخیر</h3>
              <p className="text-3xl font-bold text-gray-900">{metrics.avg_latency_ms.toFixed(2)} ms</p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">P95 تأخیر</h3>
              <p className="text-3xl font-bold text-gray-900">{metrics.p95_ms.toFixed(2)} ms</p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">وضعیت Circuit Breaker</h3>
              <p className={`inline-block px-4 py-2 rounded-full text-lg font-bold ${getStateColor(metrics.state)}`}>
                {metrics.state}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">آخرین اتصال موفق</h3>
              <p className="text-sm text-gray-900">{formatTimestamp(metrics.last_ok_ts)}</p>
              <h3 className="text-sm font-medium text-gray-700 mt-3 mb-2">آخرین خطا</h3>
              <p className="text-sm text-gray-900">{formatTimestamp(metrics.last_err_ts)}</p>
            </div>
          </div>
        )}

        {activeTab === 'playground' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Playground</h2>
              <p className="text-sm text-gray-600 mb-4">
                پارامترهای Sample را به صورت JSON وارد کرده و اجرا کنید.
              </p>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  پارامترهای Sample (JSON)
                </label>
                <textarea
                  value={sampleParams}
                  onChange={(e) => setSampleParams(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder={getSamplePlaceholder(datasource.type)}
                />
              </div>

              <button
                onClick={handleSample}
                disabled={sampling}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
              >
                {sampling ? 'در حال اجرا...' : '▶ اجرای Sample'}
              </button>
            </div>

            {sampleResult && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">نتیجه</h3>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                  {JSON.stringify(sampleResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function getSamplePlaceholder(type: string): string {
  switch (type) {
    case 'POSTGRES':
      return '{}  // محدودیت در MVP';
    case 'REST':
      return '{\n  "method": "GET",\n  "path": "/status"\n}';
    case 'MONGODB':
      return '{\n  "collection": "users",\n  "filter": {},\n  "limit": 1\n}';
    case 'GRAPHQL':
      return '{\n  "query": "{ __typename }",\n  "variables": {}\n}';
    case 'S3':
      return '{\n  "prefix": "",\n  "max_keys": 5\n}';
    default:
      return '{}';
  }
}
