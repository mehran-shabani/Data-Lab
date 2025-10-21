'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  listDataSources, 
  deleteDataSource, 
  getDataSourcesHealth,
  type DataSourceOut,
  type HealthSummaryItem,
} from '@/lib/api';

export default function DataSourcesPage() {
  const router = useRouter();
  const [datasources, setDatasources] = useState<DataSourceOut[]>([]);
  const [healthData, setHealthData] = useState<Map<string, HealthSummaryItem>>(new Map());
  const [loading, setLoading] = useState(true);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    // Get org_id from token (simplified - in real app, decode JWT)
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/signin');
      return;
    }

    // For MVP, decode the token to get org_id
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setOrgId(payload.org_id);
    } catch (e) {
      console.error('Failed to decode token', e);
      router.push('/signin');
      return;
    }
  }, [router]);

  useEffect(() => {
    if (!orgId) return;

    const fetchDataSources = async () => {
      try {
        setLoading(true);
        const [dsData, healthDataArray] = await Promise.all([
          listDataSources(orgId),
          getDataSourcesHealth(orgId).catch(() => []),
        ]);
        setDatasources(dsData);
        
        // Convert health array to map for easy lookup
        const healthMap = new Map<string, HealthSummaryItem>();
        healthDataArray.forEach(item => {
          healthMap.set(item.ds_id, item);
        });
        setHealthData(healthMap);
        
        setError(null);
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری منابع داده');
      } finally {
        setLoading(false);
      }
    };

    fetchDataSources();
  }, [orgId]);

  const handlePingAll = async () => {
    if (!orgId) return;

    setLoadingHealth(true);
    setError(null);

    try {
      const healthDataArray = await getDataSourcesHealth(orgId);
      const healthMap = new Map<string, HealthSummaryItem>();
      healthDataArray.forEach(item => {
        healthMap.set(item.ds_id, item);
      });
      setHealthData(healthMap);
    } catch (err: any) {
      setError(err.message || 'خطا در دریافت وضعیت سلامت');
    } finally {
      setLoadingHealth(false);
    }
  };

  const handleDelete = async (dsId: string) => {
    if (!orgId) return;
    if (!confirm('آیا مطمئن هستید که می‌خواهید این منبع داده را حذف کنید؟')) return;

    try {
      await deleteDataSource(orgId, dsId);
      setDatasources(datasources.filter((ds) => ds.id !== dsId));
    } catch (err: any) {
      alert(err.message || 'خطا در حذف منبع داده');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">در حال بارگذاری...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">منابع داده</h1>
            <p className="text-gray-600 mt-2">مدیریت اتصالات پایگاه داده و API</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handlePingAll}
              disabled={loadingHealth}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-100 transition-colors"
            >
              {loadingHealth ? 'در حال بررسی...' : '🔄 بررسی سلامت همه'}
            </button>
            <Link
              href="/dashboard/datasources/new"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + منبع داده جدید
            </Link>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* DataSources List */}
        {datasources.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg
                className="mx-auto h-12 w-12"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              هیچ منبع داده‌ای وجود ندارد
            </h3>
            <p className="text-gray-600 mb-6">
              برای شروع، یک منبع داده جدید ایجاد کنید
            </p>
            <Link
              href="/dashboard/datasources/new"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              ایجاد اولین منبع داده
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    نام
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    نوع
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    وضعیت
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    آخرین OK
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    تاریخ ایجاد
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    عملیات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {datasources.map((ds) => {
                  const health = healthData.get(ds.id);
                  const getTypeColor = (type: string) => {
                    switch (type) {
                      case 'POSTGRES': return 'bg-blue-100 text-blue-800';
                      case 'REST': return 'bg-green-100 text-green-800';
                      case 'MONGODB': return 'bg-green-100 text-green-800';
                      case 'GRAPHQL': return 'bg-purple-100 text-purple-800';
                      case 'S3': return 'bg-orange-100 text-orange-800';
                      default: return 'bg-gray-100 text-gray-800';
                    }
                  };
                  
                  return (
                    <tr key={ds.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link 
                          href={`/dashboard/datasources/${ds.id}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-900"
                        >
                          {ds.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTypeColor(ds.type)}`}>
                          {ds.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {health ? (
                          <div className="flex items-center gap-2">
                            {health.ok === true && (
                              <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                ✓ سالم
                              </span>
                            )}
                            {health.ok === false && (
                              <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                ✗ خطا
                              </span>
                            )}
                            {health.ok === null && (
                              <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                ؟ نامشخص
                              </span>
                            )}
                            {health.state === 'OPEN' && (
                              <span className="text-xs text-red-600">(تعلیق)</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {health?.last_ok_ts 
                          ? new Date(health.last_ok_ts * 1000).toLocaleString('fa-IR', { 
                              month: 'short', 
                              day: 'numeric', 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })
                          : '—'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(ds.created_at).toLocaleDateString('fa-IR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/dashboard/datasources/${ds.id}`}
                          className="text-blue-600 hover:text-blue-900 ml-4"
                        >
                          جزییات
                        </Link>
                        <Link
                          href={`/dashboard/datasources/${ds.id}/edit`}
                          className="text-blue-600 hover:text-blue-900 ml-4"
                        >
                          ویرایش
                        </Link>
                        <button
                          onClick={() => handleDelete(ds.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          حذف
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
