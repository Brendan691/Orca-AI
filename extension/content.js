/**
 * 小鲸OrcaAI v0.2.0 — Content Script (Chrome + Edge)
 * 与页面内容交互：提取正文、页面标记
 */

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageContent') {
    const content = extractPageContent();
    sendResponse({ content, title: document.title });
  }
  return true;
});

function extractPageContent() {
  const article = document.querySelector('article');
  const main = document.querySelector('main');

  if (article) return cleanText(article.innerText);
  if (main) return cleanText(main.innerText);

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

  if (bestContainer && maxTextLength > 200) return cleanText(bestContainer.innerText);

  const allText = Array.from(paragraphs).map(p => p.innerText.trim()).filter(t => t.length > 10).join('\n');
  if (allText.length > 100) return cleanText(allText);

  return cleanText(document.body.innerText);
}

function cleanText(text) {
  return text.replace(/\s+/g, ' ').replace(/\n{3,}/g, '\n\n').trim().substring(0, 15000);
}
