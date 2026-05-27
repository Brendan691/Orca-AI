/**
 * 小鲸OrcaAI Chrome Extension - Content Script
 * 用于与页面内容交互
 */

// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageContent') {
    // 提取页面正文内容
    const content = extractPageContent();
    sendResponse({ content });
  }
  return true;
});

/**
 * 提取页面正文内容
 * 使用多种策略，优先提取主要内容区域
 */
function extractPageContent() {
  // 策略1：找article或main标签
  const article = document.querySelector('article');
  const main = document.querySelector('main');

  if (article) {
    return cleanText(article.innerText);
  }
  if (main) {
    return cleanText(main.innerText);
  }

  // 策略2：找最长文本的段落容器
  const paragraphs = document.querySelectorAll('p');
  let bestContainer = null;
  let maxTextLength = 0;

  paragraphs.forEach(p => {
    const parent = p.parentElement;
    if (parent) {
      const textLength = parent.innerText.length;
      if (textLength > maxTextLength && textLength < 50000) {
        maxTextLength = textLength;
        bestContainer = parent;
      }
    }
  });

  if (bestContainer && maxTextLength > 200) {
    return cleanText(bestContainer.innerText);
  }

  // 策略3：退而求其次，提取所有段落
  const allText = Array.from(paragraphs)
    .map(p => p.innerText.trim())
    .filter(t => t.length > 10)
    .join('\n');

  if (allText.length > 100) {
    return cleanText(allText);
  }

  // 最终策略：返回body文本
  return cleanText(document.body.innerText);
}

/**
 * 清理文本
 */
function cleanText(text) {
  return text
    .replace(/\s+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
    .substring(0, 15000); // 最多15000字符
}
