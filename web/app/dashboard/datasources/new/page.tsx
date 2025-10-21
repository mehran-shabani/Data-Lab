'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createDataSource, checkDraftConnectivity, type DataSourceCreate } from '@/lib/api';

type DataSourceType = 'POSTGRES' | 'REST' | 'MONGODB' | 'GRAPHQL' | 'S3';
type AuthType = 'NONE' | 'API_KEY' | 'BEARER';
type WizardStep = 1 | 2 | 3;

const TYPE_INFO: Record<DataSourceType, { label: string; description: string; icon: string }> = {
  POSTGRES: {
    label: 'PostgreSQL',
    description: 'پایگاه داده رابطه‌ای قدرتمند و منبع‌باز',
    icon: '🐘',
  },
  REST: {
    label: 'REST API',
    description: 'اتصال به API های RESTful',
    icon: '🌐',
  },
  MONGODB: {
    label: 'MongoDB',
    description: 'پایگاه داده NoSQL مبتنی بر اسناد',
    icon: '🍃',
  },
  GRAPHQL: {
    label: 'GraphQL',
    description: 'API با زبان کوئری انعطاف‌پذیر',
    icon: '⬢',
  },
  S3: {
    label: 'S3 / MinIO',
    description: 'ذخیره‌سازی ابری شیء (فقط خواندن)',
    icon: '🪣',
  },
};

export default function NewDataSourceWizard() {
  const router = useRouter();
  const [orgId, setOrgId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
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

  // MongoDB fields
  const [mongoUri, setMongoUri] = useState('');
  const [mongoDb, setMongoDb] = useState('');
  const [mongoCollection, setMongoCollection] = useState('');

  // GraphQL fields
  const [graphqlUrl, setGraphqlUrl] = useState('');
  const [graphqlAuthType, setGraphqlAuthType] = useState<AuthType>('NONE');
  const [graphqlApiKey, setGraphqlApiKey] = useState('');
  const [graphqlBearerToken, setGraphqlBearerToken] = useState('');
  const [graphqlHeaders, setGraphqlHeaders] = useState('{}');

  // S3 fields
  const [s3Endpoint, setS3Endpoint] = useState('');
  const [s3Region, setS3Region] = useState('');
  const [s3Bucket, setS3Bucket] = useState('');
  const [s3AccessKey, setS3AccessKey] = useState('');
  const [s3SecretKey, setS3SecretKey] = useState('');
  const [s3PathStyle, setS3PathStyle] = useState(false);

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

  const buildTestPayload = (): any => {
    switch (dsType) {
      case 'POSTGRES':
        if (useExplicit) {
          return { type: 'POSTGRES', host, port, database, username, password };
        } else {
          return { type: 'POSTGRES', dsn };
        }
      case 'REST':
        return {
          type: 'REST',
          base_url: baseUrl,
          auth_type: authType,
          api_key: authType === 'API_KEY' ? apiKey : undefined,
          bearer_token: authType === 'BEARER' ? bearerToken : undefined,
          headers: headers ? JSON.parse(headers) : undefined,
        };
      case 'MONGODB':
        return {
          type: 'MONGODB',
          uri: mongoUri,
          db: mongoDb,
          collection: mongoCollection || undefined,
        };
      case 'GRAPHQL':
        return {
          type: 'GRAPHQL',
          base_url: graphqlUrl,
          auth_type: graphqlAuthType,
          api_key: graphqlAuthType === 'API_KEY' ? graphqlApiKey : undefined,
          bearer_token: graphqlAuthType === 'BEARER' ? graphqlBearerToken : undefined,
          headers: graphqlHeaders ? JSON.parse(graphqlHeaders) : undefined,
        };
      case 'S3':
        return {
          type: 'S3',
          endpoint: s3Endpoint,
          region: s3Region || undefined,
          bucket: s3Bucket,
          access_key: s3AccessKey,
          secret_key: s3SecretKey,
          use_path_style: s3PathStyle,
        };
    }
  };

  const handleTestConnection = async () => {
    if (!orgId) return;

    setCheckingConnectivity(true);
    setConnectivityResult(null);
    setError(null);

    try {
      const payload = buildTestPayload();
      const result = await checkDraftConnectivity(orgId, payload);
      setConnectivityResult(result);
    } catch (err: any) {
      setError(err.message || 'خطا در تست اتصال');
    } finally {
      setCheckingConnectivity(false);
    }
  };

  const handleCreate = async () => {
    if (!orgId) return;

    setLoading(true);
    setError(null);

    try {
      const basePayload = buildTestPayload();
      const payload: DataSourceCreate = {
        name,
        ...basePayload,
      };

      await createDataSource(orgId, payload);
      router.push('/dashboard/datasources');
    } catch (err: any) {
      setError(err.message || 'خطا در ایجاد منبع داده');
    } finally {
      setLoading(false);
    }
  };

  const canProceedToStep2 = () => {
    return dsType !== null;
  };

  const canProceedToStep3 = () => {
    if (!name.trim()) return false;

    switch (dsType) {
      case 'POSTGRES':
        if (useExplicit) {
          return host && database && username && password;
        } else {
          return dsn.trim().length > 0;
        }
      case 'REST':
        return baseUrl.trim().length > 0;
      case 'MONGODB':
        return mongoUri.trim().length > 0 && mongoDb.trim().length > 0;
      case 'GRAPHQL':
        return graphqlUrl.trim().length > 0;
      case 'S3':
        return s3Endpoint && s3Bucket && s3AccessKey && s3SecretKey;
      default:
        return false;
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">مرحله ۱: انتخاب نوع منبع داده</h2>
        <p className="text-gray-600">نوع منبع داده‌ای که می‌خواهید متصل شوید را انتخاب کنید.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(TYPE_INFO).map(([type, info]) => (
          <button
            key={type}
            type="button"
            onClick={() => setDsType(type as DataSourceType)}
            className={`p-6 border-2 rounded-lg text-right transition-all ${
              dsType === type
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="text-3xl mb-2">{info.icon}</div>
            <h3 className="font-bold text-gray-900 mb-1">{info.label}</h3>
            <p className="text-sm text-gray-600">{info.description}</p>
          </button>
        ))}
      </div>

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={() => setCurrentStep(2)}
          disabled={!canProceedToStep2()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          مرحله بعد ←
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => {
    const renderConfigFields = () => {
      switch (dsType) {
        case 'POSTGRES':
          return (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">روش اتصال</label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input type="radio" checked={useExplicit} onChange={() => setUseExplicit(true)} className="ml-2" />
                    فیلدهای جداگانه
                  </label>
                  <label className="flex items-center">
                    <input type="radio" checked={!useExplicit} onChange={() => setUseExplicit(false)} className="ml-2" />
                    DSN
                  </label>
                </div>
              </div>

              {useExplicit ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">میزبان *</label>
                      <input
                        type="text"
                        value={host}
                        onChange={(e) => setHost(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">پورت *</label>
                      <input
                        type="number"
                        value={port}
                        onChange={(e) => setPort(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">نام پایگاه داده *</label>
                    <input
                      type="text"
                      value={database}
                      onChange={(e) => setDatabase(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">نام کاربری *</label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">رمز عبور *</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">DSN *</label>
                  <input
                    type="text"
                    value={dsn}
                    onChange={(e) => setDsn(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="postgresql://user:password@host:port/database"
                  />
                </div>
              )}
            </>
          );

        case 'REST':
          return (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">آدرس پایه (Base URL) *</label>
                <input
                  type="url"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">نوع احراز هویت</label>
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">API Key *</label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
              {authType === 'BEARER' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Bearer Token *</label>
                  <input
                    type="password"
                    value={bearerToken}
                    onChange={(e) => setBearerToken(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">هدرهای سفارشی (JSON)</label>
                <textarea
                  value={headers}
                  onChange={(e) => setHeaders(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"X-Custom-Header": "value"}'
                />
              </div>
            </>
          );

        case 'MONGODB':
          return (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">URI اتصال *</label>
                <input
                  type="text"
                  value={mongoUri}
                  onChange={(e) => setMongoUri(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="mongodb://user:pass@host:27017/db یا mongodb+srv://..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">نام پایگاه داده *</label>
                <input
                  type="text"
                  value={mongoDb}
                  onChange={(e) => setMongoDb(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Collection (اختیاری)</label>
                <input
                  type="text"
                  value={mongoCollection}
                  onChange={(e) => setMongoCollection(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          );

        case 'GRAPHQL':
          return (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">آدرس GraphQL Endpoint *</label>
                <input
                  type="url"
                  value={graphqlUrl}
                  onChange={(e) => setGraphqlUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.example.com/graphql"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">نوع احراز هویت</label>
                <select
                  value={graphqlAuthType}
                  onChange={(e) => setGraphqlAuthType(e.target.value as AuthType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="NONE">بدون احراز هویت</option>
                  <option value="API_KEY">API Key</option>
                  <option value="BEARER">Bearer Token</option>
                </select>
              </div>
              {graphqlAuthType === 'API_KEY' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">API Key *</label>
                  <input
                    type="password"
                    value={graphqlApiKey}
                    onChange={(e) => setGraphqlApiKey(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
              {graphqlAuthType === 'BEARER' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Bearer Token *</label>
                  <input
                    type="password"
                    value={graphqlBearerToken}
                    onChange={(e) => setGraphqlBearerToken(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">هدرهای سفارشی (JSON)</label>
                <textarea
                  value={graphqlHeaders}
                  onChange={(e) => setGraphqlHeaders(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"X-Custom-Header": "value"}'
                />
              </div>
            </>
          );

        case 'S3':
          return (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Endpoint *</label>
                <input
                  type="url"
                  value={s3Endpoint}
                  onChange={(e) => setS3Endpoint(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="https://s3.amazonaws.com یا http://minio:9000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Region (اختیاری برای MinIO)</label>
                <input
                  type="text"
                  value={s3Region}
                  onChange={(e) => setS3Region(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="us-east-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">نام Bucket *</label>
                <input
                  type="text"
                  value={s3Bucket}
                  onChange={(e) => setS3Bucket(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Access Key *</label>
                <input
                  type="text"
                  value={s3AccessKey}
                  onChange={(e) => setS3AccessKey(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Secret Key *</label>
                <input
                  type="password"
                  value={s3SecretKey}
                  onChange={(e) => setS3SecretKey(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={s3PathStyle}
                    onChange={(e) => setS3PathStyle(e.target.checked)}
                    className="ml-2"
                  />
                  استفاده از Path-Style (برای MinIO)
                </label>
              </div>
            </>
          );

        default:
          return null;
      }
    };

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            مرحله ۲: وارد کردن تنظیمات
          </h2>
          <p className="text-gray-600">مشخصات اتصال به {TYPE_INFO[dsType].label} را وارد کنید.</p>
        </div>

        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          ⚠️ اطلاعات حساس (رمز عبور، کلیدها) به صورت رمزشده ذخیره می‌شوند.
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">نام منبع داده *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="مثال: پایگاه داده اصلی"
          />
        </div>

        {renderConfigFields()}

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={() => setCurrentStep(1)}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            → مرحله قبل
          </button>
          <button
            type="button"
            onClick={() => setCurrentStep(3)}
            disabled={!canProceedToStep3()}
            className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            مرحله بعد (تست اتصال) ←
          </button>
        </div>
      </div>
    );
  };

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">مرحله ۳: تست اتصال</h2>
        <p className="text-gray-600">اتصال را تست کنید و سپس منبع داده را ایجاد نمایید.</p>
      </div>

      {/* Connection Test */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
      )}

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

      {/* Summary */}
      <div className="p-6 bg-gray-50 rounded-lg">
        <h3 className="font-bold text-gray-900 mb-4">خلاصه تنظیمات</h3>
        <dl className="space-y-2">
          <div className="flex">
            <dt className="font-medium text-gray-700 w-32">نام:</dt>
            <dd className="text-gray-900">{name}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-32">نوع:</dt>
            <dd className="text-gray-900">{TYPE_INFO[dsType].label}</dd>
          </div>
          {dsType === 'POSTGRES' && (
            <div className="flex">
              <dt className="font-medium text-gray-700 w-32">میزبان:</dt>
              <dd className="text-gray-900">{useExplicit ? `${host}:${port}` : 'DSN'}</dd>
            </div>
          )}
          {dsType === 'REST' && (
            <div className="flex">
              <dt className="font-medium text-gray-700 w-32">URL:</dt>
              <dd className="text-gray-900">{baseUrl}</dd>
            </div>
          )}
          {dsType === 'MONGODB' && (
            <div className="flex">
              <dt className="font-medium text-gray-700 w-32">پایگاه داده:</dt>
              <dd className="text-gray-900">{mongoDb}</dd>
            </div>
          )}
          {dsType === 'GRAPHQL' && (
            <div className="flex">
              <dt className="font-medium text-gray-700 w-32">Endpoint:</dt>
              <dd className="text-gray-900">{graphqlUrl}</dd>
            </div>
          )}
          {dsType === 'S3' && (
            <div className="flex">
              <dt className="font-medium text-gray-700 w-32">Bucket:</dt>
              <dd className="text-gray-900">{s3Bucket}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={() => setCurrentStep(2)}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          → مرحله قبل
        </button>
        <button
          type="button"
          onClick={handleTestConnection}
          disabled={checkingConnectivity}
          className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 transition-colors"
        >
          {checkingConnectivity ? 'در حال تست...' : '🔍 تست اتصال'}
        </button>
        <button
          type="button"
          onClick={handleCreate}
          disabled={loading || (connectivityResult && !connectivityResult.ok)}
          className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'در حال ایجاد...' : '✓ ایجاد منبع داده'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/datasources" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← بازگشت به لیست
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">ویزارد ایجاد منبع داده جدید</h1>
          <p className="text-gray-600 mt-2">ایجاد اتصال به پایگاه داده یا API در ۳ مرحله ساده</p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex-1 flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                    currentStep === step
                      ? 'bg-blue-600 text-white'
                      : currentStep > step
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {currentStep > step ? '✓' : step}
                </div>
                {step < 3 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${currentStep > step ? 'bg-green-500' : 'bg-gray-200'}`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600">
            <span>انتخاب نوع</span>
            <span>تنظیمات</span>
            <span>تست و ایجاد</span>
          </div>
        </div>

        {/* Wizard Content */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </div>
      </div>
    </div>
  );
}
