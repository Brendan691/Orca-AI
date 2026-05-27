'use client';

import { useState, useEffect, useRef } from 'react';
import { api, setToken, getToken } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Tab = 'dashboard' | 'documents' | 'chat' | 'upload' | 'reports' | 'teams' | 'settings';

export default function Home() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [user, setUser] = useState<any>(null);
  const [dark, setDark] = useState(false);

  // Auth
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authError, setAuthError] = useState('');

  // Dashboard
  const [status, setStatus] = useState<any>(null);

  // Documents
  const [docs, setDocs] = useState<any[]>([]);

  // Chat
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [searchInternet, setSearchInternet] = useState(false);

  // Upload
  const [uploadUrl, setUploadUrl] = useState('');
  const [uploadText, setUploadText] = useState('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadMode, setUploadMode] = useState<'url' | 'text' | 'file'>('url');
  const [uploadMsg, setUploadMsg] = useState('');

  // Reports
  const [reportType, setReportType] = useState('weekly_shipping');
  const [reportContent, setReportContent] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [reportLoading, setReportLoading] = useState(false);

  // Teams
  const [teams, setTeams] = useState<any[]>([]);
  const [teamName, setTeamName] = useState('');
  const [teamMemberEmail, setTeamMemberEmail] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = getToken();
    if (token) {
      api.getMe().then(u => { setUser(u); loadData(); }).catch(() => setToken(null));
    }
  }, []);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory]);

  async function loadData() {
    const [s, d, t] = await Promise.all([
      api.getStatus().catch(() => null),
      api.getDocuments().catch(() => ({ documents: [], total: 0 })),
      api.getTeams().catch(() => []),
    ]);
    setStatus(s);
    setDocs(d.documents || []);
    setTeams(Array.isArray(t) ? t : []);
  }

  async function handleAuth() {
    setAuthError('');
    try {
      if (authMode === 'login') {
        const r = await api.login(email, password);
        setToken(r.access_token);
        setUser(r.user);
        loadData();
      } else {
        const r = await api.register(email, username, password);
        setToken(r.access_token);
        setUser(r.user);
        loadData();
      }
    } catch (e: any) {
      setAuthError(e.message);
    }
  }

  function logout() { setToken(null); setUser(null); setTab('dashboard'); }

  async function handleUpload() {
    setUploadMsg('');
    try {
      let result;
      if (uploadMode === 'url' && uploadUrl) {
        result = await api.uploadUrl(uploadUrl, uploadTitle);
      } else if (uploadMode === 'text' && uploadText) {
        result = await api.uploadContent(uploadText, uploadTitle);
      }
      setUploadMsg(result?.success ? `✅ ${result.message}` : `❌ ${result?.message}`);
      if (result?.success) { loadData(); setTab('documents'); }
    } catch (e: any) {
      setUploadMsg(`❌ ${e.message}`);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadMsg('上传解析中...');
    try {
      const result = await api.uploadFile(file);
      setUploadMsg(result.success ? `✅ ${result.message}` : `❌ ${result.message}`);
      loadData();
    } catch (e: any) {
      setUploadMsg(`❌ ${e.message}`);
    }
  }

  async function handleChat() {
    if (!chatMsg.trim() || chatLoading) return;
    const msg = chatMsg;
    setChatMsg('');
    setChatHistory(prev => [...prev, { role: 'user', content: msg }]);
    setChatLoading(true);

    try {
      const r = await api.chat(msg, searchInternet);
      setChatHistory(prev => [...prev, { role: 'assistant', content: r.answer }]);
    } catch (e: any) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: `❌ ${e.message}` }]);
    }
    setChatLoading(false);
  }

  async function handleGenerate() {
    setReportLoading(true);
    setReportContent('');
    try {
      const r = await api.generateReport(reportType, 'week');
      if (r.success) {
        setReportTitle(r.title);
        setReportContent(r.content);
      } else {
        setReportContent(r.content || '生成失败');
      }
    } catch (e: any) {
      setReportContent(`❌ ${e.message}`);
    }
    setReportLoading(false);
  }

  async function handleCreateTeam() {
    if (!teamName) return;
    try {
      await api.createTeam(teamName);
      setTeamName('');
      loadData();
    } catch (e: any) { alert(e.message); }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-ocean-50 to-blue-100 dark:from-gray-900 dark:to-gray-800">
        <div className="card w-full max-w-md">
          <div className="text-center mb-6">
            <div className="text-5xl mb-3">🐳</div>
            <h1 className="text-2xl font-bold text-ocean-600 dark:text-ocean-400">小鲸 OrcaAI</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">AI 驱动的海事知识管理工具</p>
          </div>

          <div className="flex mb-4 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${authMode === 'login' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}`}
              onClick={() => setAuthMode('login')}
            >登录</button>
            <button
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${authMode === 'register' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}`}
              onClick={() => setAuthMode('register')}
            >注册</button>
          </div>

          <div className="space-y-3">
            <input className="input" type="email" placeholder="邮箱" value={email} onChange={e => setEmail(e.target.value)} />
            {authMode === 'register' && (
              <input className="input" type="text" placeholder="用户名" value={username} onChange={e => setUsername(e.target.value)} />
            )}
            <input className="input" type="password" placeholder="密码" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAuth()} />
            {authError && <p className="text-red-500 text-sm">{authError}</p>}
            <button className="btn-primary w-full" onClick={handleAuth}>
              {authMode === 'login' ? '登录' : '注册'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'dashboard', label: '概览', icon: '📊' },
    { key: 'documents', label: '文档', icon: '📄' },
    { key: 'upload', label: '上传', icon: '📤' },
    { key: 'chat', label: '问答', icon: '💬' },
    { key: 'reports', label: '报告', icon: '📋' },
    { key: 'teams', label: '团队', icon: '👥' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🐳</span>
            <span className="font-bold text-lg text-ocean-600 dark:text-ocean-400">小鲸 OrcaAI</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setDark(!dark)} className="btn-secondary text-sm px-2 py-1">
              {dark ? '☀️' : '🌙'}
            </button>
            <span className="text-sm text-gray-500">{user.display_name || user.username}</span>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-red-500">退出</button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                tab === t.key
                  ? 'border-ocean-500 text-ocean-600 dark:text-ocean-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Dashboard */}
        {tab === 'dashboard' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">📊 系统概览</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card text-center">
                <div className="text-3xl font-bold text-ocean-600">{status?.document_count || 0}</div>
                <div className="text-sm text-gray-500 mt-1">文档切片</div>
              </div>
              <div className="card text-center">
                <div className="text-3xl font-bold text-ocean-600">{docs.length}</div>
                <div className="text-sm text-gray-500 mt-1">收藏文档</div>
              </div>
              <div className="card text-center">
                <div className="text-3xl font-bold text-ocean-600">4</div>
                <div className="text-sm text-gray-500 mt-1">标签维度</div>
              </div>
              <div className="card text-center">
                <div className="text-3xl font-bold text-ocean-600">{teams.length}</div>
                <div className="text-sm text-gray-500 mt-1">团队数</div>
              </div>
            </div>

            <div className="card">
              <h3 className="font-semibold mb-3">🚀 快速操作</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button onClick={() => setTab('upload')} className="btn-primary">📤 上传文档</button>
                <button onClick={() => setTab('chat')} className="btn-primary">💬 开始问答</button>
                <button onClick={() => setTab('reports')} className="btn-primary">📋 生成报告</button>
                <button onClick={() => setTab('documents')} className="btn-secondary">📄 查看文档</button>
              </div>
            </div>

            {docs.length > 0 && (
              <div className="card">
                <h3 className="font-semibold mb-3">📋 最近文档</h3>
                {docs.slice(0, 5).map((doc: any) => (
                  <div key={doc.doc_id} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                    <div>
                      <p className="font-medium text-sm">{doc.title || '未命名'}</p>
                      <p className="text-xs text-gray-400">{doc.created_at?.slice(0, 10)}</p>
                    </div>
                    <button onClick={async () => { await api.deleteDocument(doc.doc_id); loadData(); }} className="text-red-400 hover:text-red-600 text-sm">删除</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Documents */}
        {tab === 'documents' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">📄 文档列表 ({docs.length})</h2>
              <button onClick={loadData} className="btn-secondary text-sm">刷新</button>
            </div>
            {docs.length === 0 ? (
              <div className="card text-center py-12 text-gray-400">还没有文档。去上传你的第一篇文档吧！</div>
            ) : (
              docs.map((doc: any) => (
                <div key={doc.doc_id} className="card flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{doc.title || '未命名'}</h3>
                    <p className="text-xs text-gray-400 mt-1">{doc.doc_id?.slice(0, 16)}...</p>
                    {doc.url && <a href={doc.url} target="_blank" className="text-ocean-500 text-xs hover:underline mt-1 block">🔗 原文</a>}
                    {doc.tags && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {Object.values(doc.tags).flat().filter(Boolean).slice(0, 5).map((tag: string) => (
                          <span key={tag} className="tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button onClick={async () => { await api.deleteDocument(doc.doc_id); loadData(); }}
                    className="text-red-400 hover:text-red-600 text-sm ml-4 shrink-0">🗑️</button>
                </div>
              ))
            )}
          </div>
        )}

        {/* Upload */}
        {tab === 'upload' && (
          <div className="space-y-6 max-w-2xl">
            <h2 className="text-xl font-bold">📤 上传文档</h2>

            <div className="flex gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              {(['url', 'text', 'file'] as const).map(m => (
                <button key={m}
                  className={`flex-1 py-2 text-sm rounded-md ${uploadMode === m ? 'bg-white dark:bg-gray-600 shadow-sm font-medium' : ''}`}
                  onClick={() => setUploadMode(m)}
                >{m === 'url' ? '🔗 网页' : m === 'text' ? '📝 文本' : '📎 文件'}</button>
              ))}
            </div>

            {uploadMode === 'url' && (
              <div className="space-y-3">
                <input className="input" placeholder="网页链接 https://..." value={uploadUrl} onChange={e => setUploadUrl(e.target.value)} />
                <input className="input" placeholder="标题（可选）" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)} />
                <button className="btn-primary" onClick={handleUpload}>📥 解析并保存</button>
              </div>
            )}

            {uploadMode === 'text' && (
              <div className="space-y-3">
                <input className="input" placeholder="标题（可选）" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)} />
                <textarea className="input h-40" placeholder="粘贴文本内容..." value={uploadText} onChange={e => setUploadText(e.target.value)} />
                <button className="btn-primary" onClick={handleUpload}>📝 保存到知识库</button>
              </div>
            )}

            {uploadMode === 'file' && (
              <div className="card space-y-3">
                <p className="text-sm text-gray-500">支持 PDF、Word、PPT、Excel、MP3、图片、TXT 等格式</p>
                <input type="file" className="input" onChange={handleFileUpload}
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.csv,.json,.mp3,.wav,.m4a,.jpg,.png,.gif,.webp" />
              </div>
            )}

            {uploadMsg && <div className={`text-sm p-3 rounded-lg ${uploadMsg.startsWith('✅') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>{uploadMsg}</div>}
          </div>
        )}

        {/* Chat */}
        {tab === 'chat' && (
          <div className="max-w-3xl mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">💬 知识库问答</h2>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={searchInternet} onChange={e => setSearchInternet(e.target.checked)} />
                🌐 联网搜索
              </label>
            </div>

            <div className="card h-96 overflow-y-auto space-y-3">
              {chatHistory.length === 0 && (
                <div className="text-center text-gray-400 py-12">
                  <p className="text-4xl mb-3">🐳</p>
                  <p>向我提问海事相关问题吧！</p>
                  <p className="text-xs mt-2">例如：最新集装箱运价走势如何？</p>
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] px-4 py-2 rounded-xl text-sm ${
                    msg.role === 'user'
                      ? 'bg-ocean-500 text-white rounded-br-sm'
                      : 'bg-gray-100 dark:bg-gray-700 rounded-bl-sm'
                  }`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              {chatLoading && <div className="text-gray-400 text-sm">小鲸思考中...</div>}
              <div ref={chatEndRef} />
            </div>

            <div className="flex gap-2">
              <input className="input flex-1" placeholder="输入问题..." value={chatMsg}
                onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleChat()} />
              <button className="btn-primary" onClick={handleChat} disabled={chatLoading}>发送</button>
            </div>
            {chatHistory.length > 0 && (
              <button onClick={() => setChatHistory([])} className="btn-secondary text-sm">🗑️ 清空对话</button>
            )}
          </div>
        )}

        {/* Reports */}
        {tab === 'reports' && (
          <div className="max-w-3xl mx-auto space-y-4">
            <h2 className="text-xl font-bold">📋 AI 报告生成</h2>
            <div className="flex items-center gap-3">
              <select className="input w-auto" value={reportType} onChange={e => setReportType(e.target.value)}>
                <option value="weekly_shipping">🚢 周度航运市场简报</option>
                <option value="risk_alert">⚠️ 航线风险预警报告</option>
                <option value="convention_update">📜 国际海事公约更新解读</option>
              </select>
              <button className="btn-primary" onClick={handleGenerate} disabled={reportLoading}>
                {reportLoading ? '生成中...' : '🚀 生成报告'}
              </button>
            </div>
            {reportContent && (
              <div className="card">
                {reportTitle && <h3 className="text-lg font-bold mb-4">{reportTitle}</h3>}
                <div className="prose">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{reportContent}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Teams */}
        {tab === 'teams' && (
          <div className="max-w-2xl space-y-6">
            <h2 className="text-xl font-bold">👥 团队管理</h2>

            <div className="card space-y-3">
              <h3 className="font-semibold">创建团队</h3>
              <div className="flex gap-2">
                <input className="input" placeholder="团队名称" value={teamName} onChange={e => setTeamName(e.target.value)} />
                <button className="btn-primary" onClick={handleCreateTeam}>创建</button>
              </div>
            </div>

            {teams.map((team: any) => (
              <div key={team.id} className="card">
                <h3 className="font-semibold">{team.name}</h3>
                <p className="text-sm text-gray-500">{team.member_count} 位成员 · 角色：{team.role}</p>
              </div>
            ))}

            {teams.length === 0 && (
              <div className="card text-center py-8 text-gray-400">还没有团队。创建一个吧！</div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
