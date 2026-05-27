/**
 * 小鲸OrcaAI Chrome Extension - Background Service Worker
 */

// 安装时初始化
chrome.runtime.onInstalled.addListener(() => {
  console.log('小鲸OrcaAI 已安装');
});

// 监听来自content script的消息（如需跨标签通信）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 可以在这里处理后台任务
  return true;
});
