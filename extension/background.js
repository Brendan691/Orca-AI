/**
 * 小鲸OrcaAI v0.2.0 — Service Worker
 * 支持 Chrome + Edge (Chromium 内核)
 * 功能：右键菜单收藏、快捷键收藏、通知、页面标记
 */

const API_BASE_KEY = 'apiUrl';
const DEFAULT_API = 'http://localhost:8000';

chrome.runtime.onInstalled.addListener(async () => {
  chrome.contextMenus.create({
    id: 'save-to-orcaai',
    title: '🐳 收藏到小鲸知识库',
    contexts: ['page', 'selection', 'link', 'image'],
  });
  chrome.contextMenus.create({
    id: 'ask-orcaai',
    title: '💬 向小鲸提问',
    contexts: ['selection'],
  });

  const stored = await chrome.storage.local.get(API_BASE_KEY);
  if (!stored[API_BASE_KEY]) {
    await chrome.storage.local.set({ [API_BASE_KEY]: DEFAULT_API });
  }
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { apiUrl } = await chrome.storage.local.get(API_BASE_KEY);
  const baseUrl = apiUrl || DEFAULT_API;

  if (info.menuItemId === 'save-to-orcaai') {
    const url = info.linkUrl || info.pageUrl || info.srcUrl;
    const title = info.selectionText ? info.selectionText.slice(0, 100) : (tab?.title || '');

    try {
      const resp = await fetch(`${baseUrl}/api/documents/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title }),
      });
      const result = await resp.json();
      const msg = result.success
        ? `✅ 已收藏：${title.slice(0, 50)}`
        : `❌ 收藏失败：${result.message}`;
      chrome.notifications?.create({ type: 'basic', iconUrl: 'icons/icon128.png', title: '小鲸 OrcaAI', message: msg });
    } catch (e) {
      chrome.notifications?.create({ type: 'basic', iconUrl: 'icons/icon128.png', title: '小鲸 OrcaAI', message: `❌ 网络错误：${e.message}` });
    }
  }

  if (info.menuItemId === 'ask-orcaai' && info.selectionText) {
    try {
      const resp = await fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: info.selectionText }),
      });
      const result = await resp.json();
      chrome.notifications?.create({
        type: 'basic', iconUrl: 'icons/icon128.png', title: '小鲸 AI 回答',
        message: result.answer?.slice(0, 200) || '无法获取回答',
      });
    } catch (e) { /* 静默失败 */ }
  }
});

chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'save-to-knowledge-base') {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs[0];
    if (!tab || !tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('edge://')) return;

    const { apiUrl } = await chrome.storage.local.get(API_BASE_KEY);
    const baseUrl = apiUrl || DEFAULT_API;
    try {
      await fetch(`${baseUrl}/api/documents/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: tab.url, title: tab.title }),
      });
    } catch (e) { /* 静默失败 */ }
  }
});
