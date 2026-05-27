/** API 客户端 — 统一封装后端请求 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

let authToken: string | null = null;

export function setToken(token: string | null) {
  authToken = token;
  if (token) {
    if (typeof window !== 'undefined') localStorage.setItem('orcaai_token', token);
  } else {
    if (typeof window !== 'undefined') localStorage.removeItem('orcaai_token');
  }
}

export function getToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== 'undefined') {
    return localStorage.getItem('orcaai_token');
  }
  return null;
}

async function request(method: string, path: string, body?: any): Promise<any> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  // 认证
  login: (email: string, password: string) =>
    request('POST', '/api/auth/login', { email, password }),
  register: (email: string, username: string, password: string) =>
    request('POST', '/api/auth/register', { email, username, password }),
  getMe: () => request('GET', '/api/auth/me'),

  // 文档
  getDocuments: () => request('GET', '/api/documents'),
  uploadUrl: (url: string, title?: string) =>
    request('POST', '/api/documents/upload', { url, title }),
  uploadContent: (content: string, title?: string) =>
    request('POST', '/api/documents/upload', { content, title }),
  deleteDocument: (docId: string) =>
    request('DELETE', `/api/documents/${docId}`),

  // 文件上传
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/files/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  // 问答
  chat: (message: string, searchInternet?: boolean) =>
    request('POST', '/api/chat', { message, search_internet: searchInternet }),

  // 搜索
  search: (query: string, topK?: number) =>
    request('POST', '/api/search', { query, top_k: topK || 5 }),

  // 联网搜索
  searchInternet: (q: string) =>
    request('GET', `/api/search/internet?q=${encodeURIComponent(q)}`),

  // 标签
  getTags: () => request('GET', '/api/tags'),

  // 报告生成
  generateReport: (reportType: string, timeRange?: string) =>
    request('POST', '/api/generate/report', { report_type: reportType, time_range: timeRange }),
  getReportTypes: () => request('GET', '/api/generate/report-types'),

  // 团队
  getTeams: () => request('GET', '/api/teams'),
  createTeam: (name: string, description?: string) =>
    request('POST', '/api/teams', { name, description }),
  addMember: (teamId: string, email: string, role?: string) =>
    request('POST', `/api/teams/${teamId}/members`, { email, role: role || 'editor' }),

  // 系统
  getStatus: () => request('GET', '/api/status'),
  healthCheck: () => fetch(`${API_BASE}/health`).then(r => r.json()),
};
