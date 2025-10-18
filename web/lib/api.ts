/**
 * API client for DataSource management
 */

import { redirect } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface DataSourceOut {
  id: string;
  name: string;
  type: 'POSTGRES' | 'REST';
  schema_version: string;
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreatePostgres {
  name: string;
  type: 'POSTGRES';
  schema_version?: string;
  dsn?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
}

export interface DataSourceCreateRest {
  name: string;
  type: 'REST';
  schema_version?: string;
  base_url: string;
  auth_type: 'NONE' | 'API_KEY' | 'BEARER';
  headers?: Record<string, string>;
  api_key?: string;
  bearer_token?: string;
}

export type DataSourceCreate = DataSourceCreatePostgres | DataSourceCreateRest;

export interface DataSourceUpdatePostgres {
  type: 'POSTGRES';
  name?: string;
  dsn?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
}

export interface DataSourceUpdateRest {
  type: 'REST';
  name?: string;
  base_url?: string;
  auth_type?: 'NONE' | 'API_KEY' | 'BEARER';
  headers?: Record<string, string>;
  api_key?: string;
  bearer_token?: string;
}

export type DataSourceUpdate = DataSourceUpdatePostgres | DataSourceUpdateRest;

export interface ConnectivityCheckOut {
  ok: boolean;
  details: string;
}

export interface DataSourceTestCheckPostgres {
  type: 'POSTGRES';
  dsn?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
}

export interface DataSourceTestCheckRest {
  type: 'REST';
  base_url: string;
  auth_type: 'NONE' | 'API_KEY' | 'BEARER';
  headers?: Record<string, string>;
  api_key?: string;
  bearer_token?: string;
}

export type DataSourceTestCheck = DataSourceTestCheckPostgres | DataSourceTestCheckRest;

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

/**
 * Handle API errors
 */
function handleApiError(response: Response, data: any): never {
  if (response.status === 401 || response.status === 403) {
    // Redirect to signin
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      redirect('/signin');
    }
  }

  const errorMessage = data?.detail || `خطا در عملیات (کد ${response.status})`;
  throw new Error(errorMessage);
}

/**
 * List all DataSources for an organization
 */
export async function listDataSources(orgId: string): Promise<DataSourceOut[]> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

/**
 * Get a single DataSource by ID
 */
export async function getDataSource(orgId: string, dsId: string): Promise<DataSourceOut> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/${dsId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

/**
 * Create a new DataSource
 */
export async function createDataSource(
  orgId: string,
  payload: DataSourceCreate
): Promise<DataSourceOut> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

/**
 * Update an existing DataSource
 */
export async function updateDataSource(
  orgId: string,
  dsId: string,
  payload: DataSourceUpdate
): Promise<DataSourceOut> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/${dsId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

/**
 * Delete a DataSource
 */
export async function deleteDataSource(orgId: string, dsId: string): Promise<void> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/${dsId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    handleApiError(response, data);
  }
}

/**
 * Check connectivity for a saved DataSource
 */
export async function checkDataSourceConnectivity(
  orgId: string,
  dsId: string
): Promise<ConnectivityCheckOut> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/${dsId}/check`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

/**
 * Check connectivity for a draft DataSource (without saving)
 */
export async function checkDraftConnectivity(
  orgId: string,
  payload: DataSourceTestCheck
): Promise<ConnectivityCheckOut> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}/orgs/${orgId}/datasources/check`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}
