export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export class ApiException extends Error {
  code: string;
  details?: any;
  status: number;

  constructor(status: number, error: ApiError) {
    super(error.message || 'An unexpected error occurred');
    this.name = 'ApiException';
    this.status = status;
    this.code = error.code || 'UNKNOWN_ERROR';
    this.details = error.details;
  }
}

const API_BASE = '/api/v1';

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('brightloop_token');
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'omit',
  });

  if (response.status === 204) {
    return {} as T;
  }

  if (response.headers.get('content-type')?.includes('application/pdf')) {
    const blob = await response.blob();
    return blob as unknown as T;
  }

  let data: any;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const errorInfo: ApiError = data?.error || {
      code: `HTTP_${response.status}`,
      message: response.statusText || 'Request failed',
    };
    throw new ApiException(response.status, errorInfo);
  }

  return data as T;
}
