/**
 * API client for Farda MCP Platform
 */

import { redirect } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ========== Common Types ==========

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
function handleApiError(response: Response, data: unknown): never {
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

/**
 * Test connectivity for draft config before saving
 */
export async function testDataSourceConfig(
  orgId: string,
  payload: DataSourceTestCheck
): Promise<ConnectivityCheckOut> {
  return checkDraftConnectivity(orgId, payload);
}

export const DataSourceAPI = {
  list: listDataSources,
  get: getDataSource,
  create: createDataSource,
  update: updateDataSource,
  delete: deleteDataSource,
  check: checkDataSourceConnectivity,
  testConfig: testDataSourceConfig,
};

// ========== Tool Types ==========

export type ToolType = 'POSTGRES_QUERY' | 'REST_CALL' | 'CUSTOM';

export interface ToolOut {
  id: string;
  org_id: string;
  name: string;
  version: string;
  type: ToolType;
  datasource_id: string | null;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  exec_config: Record<string, unknown>;
  rate_limit_per_min: number | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ToolCreate {
  name: string;
  version?: string;
  type: ToolType;
  datasource_id?: string | null;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  exec_config?: Record<string, unknown>;
  rate_limit_per_min?: number | null;
  enabled?: boolean;
}

export interface ToolUpdate {
  name?: string;
  version?: string;
  type?: ToolType;
  datasource_id?: string | null;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  exec_config?: Record<string, unknown>;
  rate_limit_per_min?: number | null;
  enabled?: boolean;
}

export interface InvokeIn {
  params: Record<string, unknown>;
}

export interface InvokeOut {
  ok: boolean;
  data: unknown;
  masked: boolean;
  trace_id: string;
  error: string | null;
}

// ========== Tool API Functions ==========

/**
 * Helper to make API requests with authentication
 */
async function apiRequest<T>(path: string, options: RequestInit): Promise<T> {
  const token = getAuthToken();
  if (!token) {
    redirect('/signin');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (options.method === 'DELETE' && response.status === 204) {
    return undefined as never;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    handleApiError(response, data);
  }

  return data;
}

export async function listTools(orgId: string): Promise<ToolOut[]> {
  return apiRequest<ToolOut[]>(`/orgs/${orgId}/tools/`, {
    method: 'GET',
  });
}

export async function getTool(orgId: string, toolId: string): Promise<ToolOut> {
  return apiRequest<ToolOut>(`/orgs/${orgId}/tools/${toolId}`, {
    method: 'GET',
  });
}

export async function createTool(orgId: string, payload: ToolCreate): Promise<ToolOut> {
  return apiRequest<ToolOut>(`/orgs/${orgId}/tools/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateTool(orgId: string, toolId: string, payload: ToolUpdate): Promise<ToolOut> {
  return apiRequest<ToolOut>(`/orgs/${orgId}/tools/${toolId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deleteTool(orgId: string, toolId: string): Promise<void> {
  return apiRequest<void>(`/orgs/${orgId}/tools/${toolId}`, {
    method: 'DELETE',
  });
}

export async function invokeTool(orgId: string, toolId: string, payload: InvokeIn): Promise<InvokeOut> {
  return apiRequest<InvokeOut>(`/orgs/${orgId}/tools/${toolId}/invoke`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export const ToolAPI = {
  list: listTools,
  get: getTool,
  create: createTool,
  update: updateTool,
  delete: deleteTool,
  invoke: invokeTool,
};

// ========== MCP Server Types ==========

export type MCPServerStatus = 'ENABLED' | 'DISABLED';

export interface MCPServerOut {
  id: string;
  org_id: string;
  name: string;
  status: MCPServerStatus;
  created_at: string;
  updated_at: string;
  plain_api_key?: string | null;
}

export interface MCPServerCreate {
  name: string;
}

// ========== MCP Server API ==========

export async function listMCPServers(orgId: string): Promise<MCPServerOut[]> {
  return apiRequest<MCPServerOut[]>(`/orgs/${orgId}/mcp/servers`, {
    method: 'GET',
  });
}

export async function getMCPServer(orgId: string, serverId: string): Promise<MCPServerOut> {
  return apiRequest<MCPServerOut>(`/orgs/${orgId}/mcp/servers/${serverId}`, {
    method: 'GET',
  });
}

export async function createMCPServer(orgId: string, payload: MCPServerCreate): Promise<MCPServerOut> {
  return apiRequest<MCPServerOut>(`/orgs/${orgId}/mcp/servers`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function rotateMCPServerKey(orgId: string, serverId: string): Promise<MCPServerOut> {
  return apiRequest<MCPServerOut>(`/orgs/${orgId}/mcp/servers/${serverId}/rotate-key`, {
    method: 'POST',
  });
}

export async function enableMCPServer(orgId: string, serverId: string): Promise<MCPServerOut> {
  return apiRequest<MCPServerOut>(`/orgs/${orgId}/mcp/servers/${serverId}/enable`, {
    method: 'POST',
  });
}

export async function disableMCPServer(orgId: string, serverId: string): Promise<MCPServerOut> {
  return apiRequest<MCPServerOut>(`/orgs/${orgId}/mcp/servers/${serverId}/disable`, {
    method: 'POST',
  });
}

export const MCPServerAPI = {
  list: listMCPServers,
  get: getMCPServer,
  create: createMCPServer,
  rotateKey: rotateMCPServerKey,
  enable: enableMCPServer,
  disable: disableMCPServer,
};

// ========== Policy Types ==========

export type PolicyEffect = 'ALLOW' | 'DENY';
export type PolicyResourceType = 'TOOL' | 'DATASOURCE';

export interface PolicyOut {
  id: string;
  org_id: string;
  name: string;
  effect: PolicyEffect;
  resource_type: PolicyResourceType;
  resource_id: string;
  conditions: Record<string, unknown>;
  field_masks: Record<string, unknown> | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyCreate {
  name: string;
  effect: PolicyEffect;
  resource_type: PolicyResourceType;
  resource_id: string;
  conditions?: Record<string, unknown>;
  field_masks?: Record<string, unknown> | null;
  enabled?: boolean;
}

export interface PolicyUpdate {
  name?: string;
  effect?: PolicyEffect;
  resource_type?: PolicyResourceType;
  resource_id?: string;
  conditions?: Record<string, unknown>;
  field_masks?: Record<string, unknown> | null;
  enabled?: boolean;
}

// ========== Policy API ==========

export async function listPolicies(orgId: string): Promise<PolicyOut[]> {
  return apiRequest<PolicyOut[]>(`/orgs/${orgId}/policies/`, {
    method: 'GET',
  });
}

export async function getPolicy(orgId: string, policyId: string): Promise<PolicyOut> {
  return apiRequest<PolicyOut>(`/orgs/${orgId}/policies/${policyId}`, {
    method: 'GET',
  });
}

export async function createPolicy(orgId: string, payload: PolicyCreate): Promise<PolicyOut> {
  return apiRequest<PolicyOut>(`/orgs/${orgId}/policies/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updatePolicy(orgId: string, policyId: string, payload: PolicyUpdate): Promise<PolicyOut> {
  return apiRequest<PolicyOut>(`/orgs/${orgId}/policies/${policyId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deletePolicy(orgId: string, policyId: string): Promise<void> {
  return apiRequest<void>(`/orgs/${orgId}/policies/${policyId}`, {
    method: 'DELETE',
  });
}

export const PolicyAPI = {
  list: listPolicies,
  get: getPolicy,
  create: createPolicy,
  update: updatePolicy,
  delete: deletePolicy,
};
