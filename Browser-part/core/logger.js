export function logEvent(type, data) {
  chrome.storage.local.get(["logs"], (res) => {
    const logs = res.logs || [];
    logs.unshift(`${type}: ${JSON.stringify(data)}`);
    chrome.storage.local.set({ logs: logs.slice(0, 100) });
  });
}
