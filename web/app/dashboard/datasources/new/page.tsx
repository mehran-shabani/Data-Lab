'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createDataSource, checkDraftConnectivity, type DataSourceCreate } from '@/lib/api';

type DataSourceType = 'POSTGRES' | 'REST';
type AuthType = 'NONE' | 'API_KEY' | 'BEARER';

export default function NewDataSourcePage() {
  const router = useRouter();
  const [orgId, setOrgId] = useState<string | null>(null);
  const [dsType, setDsType] = useState<DataSourceType>('POSTGRES');

  // Common fields
  const [name, setName] = useState('');

  // PostgreSQL fields
  const [useExplicit, setUseExplicit] = useState(true);
  const [dsn, setDsn] = useState('');
  const [host, setHost] = useState('localhost');
  const [port, setPort] = useState(5432);
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // REST fields
  const [baseUrl, setBaseUrl] = useState('');
  const [authType, setAuthType] = useState<AuthType>('NONE');
  const [apiKey, setApiKey] = useState('');
  const [bearerToken, setBearerToken] = useState('');
  const [headers, setHeaders] = useState('{}');

  // UI state
  const [loading, setLoading] = useState(false);
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

  const handleTestConnection = async () => {
    if (!orgId) return;

    setCheckingConnectivity(true);
    setConnectivityResult(null);
    setError(null);

    try {
      let payload: any;

      if (dsType === 'POSTGRES') {
        if (useExplicit) {
          payload = {
            type: 'POSTGRES',
            host,
            port,
            database,
            username,
            password,
          };
        } else {
          payload = {
            type: 'POSTGRES',
            dsn,
          };
        }
      } else {
        payload = {
          type: 'REST',
          base_url: baseUrl,
          auth_type: authType,
          api_key: authType === 'API_KEY' ? apiKey : undefined,
          bearer_token: authType === 'BEARER' ? bearerToken : undefined,
          headers: headers ? JSON.parse(headers) : undefined,
        };
      }

      const result = await checkDraftConnectivity(orgId, payload);
      setConnectivityResult(result);
    } catch (err: any) {
      setError(err.message || 'خطا در تست اتصال');
    } finally {
      setCheckingConnectivity(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgId) return;

    setLoading(true);
    setError(null);

    try {
      let payload: DataSourceCreate;

      if (dsType === 'POSTGRES') {
        if (useExplicit) {
          payload = {
            name,
            type: 'POSTGRES',
            host,
            port,
            database,
            username,
            password,
          };
        } else {
          payload = {
            name,
            type: 'POSTGRES',
            dsn,
          };
        }
      } else {
        payload = {
          name,
          type: 'REST',
          base_url: baseUrl,
          auth_type: authType,
          api_key: authType === 'API_KEY' ? apiKey : undefined,
          bearer_token: authType === 'BEARER' ? bearerToken : undefined,
          headers: headers ? JSON.parse(headers) : undefined,
        };
      }

      await createDataSource(orgId, payload);
      router.push('/dashboard/datasources');
    } catch (err: any) {
      setError(err.message || 'خطا در ایجاد منبع داده');
    } finally {
      setLoading(false);
    }
  };

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
          <h1 className="text-3xl font-bold text-gray-900">منبع داده جدید</h1>
          <p className="text-gray-600 mt-2">ایجاد اتصال به پایگاه داده یا API</p>
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

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              نام منبع داده *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="مثال: پایگاه داده اصلی"
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">نوع *</label>
            <select
              value={dsType}
              onChange={(e) => setDsType(e.target.value as DataSourceType)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="POSTGRES">PostgreSQL</option>
              <option value="REST">REST API</option>
            </select>
          </div>

          {/* PostgreSQL Fields */}
          {dsType === 'POSTGRES' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  روش اتصال
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={useExplicit}
                      onChange={() => setUseExplicit(true)}
                      className="ml-2"
                    />
                    فیلدهای جداگانه
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={!useExplicit}
                      onChange={() => setUseExplicit(false)}
                      className="ml-2"
                    />
                    DSN
                  </label>
                </div>
              </div>

              {useExplicit ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        میزبان *
                      </label>
                      <input
                        type="text"
                        value={host}
                        onChange={(e) => setHost(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        پورت *
                      </label>
                      <input
                        type="number"
                        value={port}
                        onChange={(e) => setPort(Number(e.target.value))}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      نام پایگاه داده *
                    </label>
                    <input
                      type="text"
                      value={database}
                      onChange={(e) => setDatabase(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      نام کاربری *
                    </label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      رمز عبور *
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    DSN (Connection String) *
                  </label>
                  <input
                    type="text"
                    value={dsn}
                    onChange={(e) => setDsn(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="postgresql://user:password@host:port/database"
                  />
                </div>
              )}
            </>
          )}

          {/* REST Fields */}
          {dsType === 'REST' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  آدرس پایه (Base URL) *
                </label>
                <input
                  type="url"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.example.com"
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
                    API Key *
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {authType === 'BEARER' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bearer Token *
                  </label>
                  <input
                    type="password"
                    value={bearerToken}
                    onChange={(e) => setBearerToken(e.target.value)}
                    required
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"X-Custom-Header": "value"}'
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={checkingConnectivity}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 transition-colors"
            >
              {checkingConnectivity ? 'در حال تست...' : 'تست اتصال'}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
            >
              {loading ? 'در حال ایجاد...' : 'ایجاد منبع داده'}
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
