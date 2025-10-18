'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getDataSource,
  updateDataSource,
  checkDataSourceConnectivity,
  type DataSourceOut,
  type DataSourceUpdate,
} from '@/lib/api';

type AuthType = 'NONE' | 'API_KEY' | 'BEARER';

export default function EditDataSourcePage() {
  const router = useRouter();
  const params = useParams();
  const dsId = params.id as string;

  const [orgId, setOrgId] = useState<string | null>(null);
  const [datasource, setDatasource] = useState<DataSourceOut | null>(null);

  // Form fields
  const [name, setName] = useState('');

  // PostgreSQL fields (masked)
  const [host, setHost] = useState('');
  const [port, setPort] = useState(5432);
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState(''); // Empty = no change

  // REST fields (masked)
  const [baseUrl, setBaseUrl] = useState('');
  const [authType, setAuthType] = useState<AuthType>('NONE');
  const [apiKey, setApiKey] = useState(''); // Empty = no change
  const [bearerToken, setBearerToken] = useState(''); // Empty = no change
  const [headers, setHeaders] = useState('{}');

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkingConnectivity, setCheckingConnectivity] = useState(false);
  const [connectivityResult, setConnectivityResult] = useState<{
    ok: boolean;
    details: string;
  } | null>(null);

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
    if (!orgId) return;

    const fetchDataSource = async () => {
      try {
        setLoading(true);
        const data = await getDataSource(orgId, dsId);
        setDatasource(data);
        setName(data.name);
        // Note: Sensitive fields are NOT returned by API, so they remain empty (masked)
        setError(null);
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری منبع داده');
      } finally {
        setLoading(false);
      }
    };

    fetchDataSource();
  }, [orgId, dsId]);

  const handleTestConnection = async () => {
    if (!orgId) return;

    setCheckingConnectivity(true);
    setConnectivityResult(null);
    setError(null);

    try {
      const result = await checkDataSourceConnectivity(orgId, dsId);
      setConnectivityResult(result);
    } catch (err: any) {
      setError(err.message || 'خطا در تست اتصال');
    } finally {
      setCheckingConnectivity(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgId || !datasource) return;

    setSaving(true);
    setError(null);

    try {
      let payload: DataSourceUpdate;

      if (datasource.type === 'POSTGRES') {
        payload = {
          type: 'POSTGRES',
          name: name !== datasource.name ? name : undefined,
          host: host || undefined,
          port: port !== 5432 ? port : undefined,
          database: database || undefined,
          username: username || undefined,
          password: password || undefined, // Only update if provided
        };
      } else {
        payload = {
          type: 'REST',
          name: name !== datasource.name ? name : undefined,
          base_url: baseUrl || undefined,
          auth_type: authType !== 'NONE' ? authType : undefined,
          api_key: apiKey || undefined,
          bearer_token: bearerToken || undefined,
          headers: headers && headers !== '{}' ? JSON.parse(headers) : undefined,
        };
      }

      await updateDataSource(orgId, dsId, payload);
      router.push('/dashboard/datasources');
    } catch (err: any) {
      setError(err.message || 'خطا در بروزرسانی منبع داده');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">در حال بارگذاری...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!datasource) {
    return (
      <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
        <div className="max-w-3xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            منبع داده یافت نشد
          </div>
          <Link
            href="/dashboard/datasources"
            className="inline-block mt-4 text-blue-600 hover:text-blue-800"
          >
            ← بازگشت به لیست
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/dashboard/datasources"
            className="text-blue-600 hover:text-blue-800 mb-4 inline-block"
          >
            ← بازگشت به لیست
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">ویرایش منبع داده</h1>
          <p className="text-gray-600 mt-2">
            نوع: {datasource.type} | ایجاد شده:{' '}
            {new Date(datasource.created_at).toLocaleDateString('fa-IR')}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Connectivity Result */}
          {connectivityResult && (
            <div
              className={`p-4 border rounded-lg ${
                connectivityResult.ok
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-red-50 border-red-200 text-red-700'
              }`}
            >
              <div className="font-medium mb-1">
                {connectivityResult.ok ? '✓ اتصال موفق' : '✗ اتصال ناموفق'}
              </div>
              <div className="text-sm">{connectivityResult.details}</div>
            </div>
          )}

          {/* Test Connection Button */}
          <div>
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={checkingConnectivity}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 transition-colors"
            >
              {checkingConnectivity ? 'در حال تست...' : 'تست اتصال با تنظیمات ذخیره‌شده'}
            </button>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">نام منبع داده</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Type (readonly) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">نوع</label>
            <input
              type="text"
              value={datasource.type}
              disabled
              className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
            />
            <p className="text-xs text-gray-500 mt-1">نوع منبع داده قابل تغییر نیست</p>
          </div>

          {/* PostgreSQL Fields */}
          {datasource.type === 'POSTGRES' && (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
                <strong>توجه:</strong> فیلدهای حساس (مانند رمز عبور) به صورت ماسک شده نمایش داده
                می‌شوند. اگر مقداری وارد نکنید، مقدار قبلی حفظ خواهد شد.
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">میزبان</label>
                  <input
                    type="text"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="•••••"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">پورت</label>
                  <input
                    type="number"
                    value={port}
                    onChange={(e) => setPort(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  نام پایگاه داده
                </label>
                <input
                  type="text"
                  value={database}
                  onChange={(e) => setDatabase(e.target.value)}
                  placeholder="•••••"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">نام کاربری</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="•••••"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  رمز عبور (برای تغییر وارد کنید)
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="•••••"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}

          {/* REST Fields */}
          {datasource.type === 'REST' && (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
                <strong>توجه:</strong> فیلدهای حساس به صورت ماسک شده نمایش داده می‌شوند. اگر
                مقداری وارد نکنید، مقدار قبلی حفظ خواهد شد.
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  آدرس پایه (Base URL)
                </label>
                <input
                  type="url"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="•••••"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  نوع احراز هویت
                </label>
                <select
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value as AuthType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="NONE">بدون احراز هویت</option>
                  <option value="API_KEY">API Key</option>
                  <option value="BEARER">Bearer Token</option>
                </select>
              </div>

              {authType === 'API_KEY' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key (برای تغییر وارد کنید)
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="•••••"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {authType === 'BEARER' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bearer Token (برای تغییر وارد کنید)
                  </label>
                  <input
                    type="password"
                    value={bearerToken}
                    onChange={(e) => setBearerToken(e.target.value)}
                    placeholder="•••••"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  هدرهای سفارشی (JSON)
                </label>
                <textarea
                  value={headers}
                  onChange={(e) => setHeaders(e.target.value)}
                  rows={3}
                  placeholder="•••••"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
            >
              {saving ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
            </button>
            <Link
              href="/dashboard/datasources"
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              انصراف
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
