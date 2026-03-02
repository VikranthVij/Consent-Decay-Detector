let requestHistory = {};
const WINDOW_MS = 10000;

export function extractFeatures(details) {
  const now = Date.now();
  const domain = new URL(details.url).hostname;

  if (!requestHistory[domain]) {
    requestHistory[domain] = [];
  }

  requestHistory[domain] = requestHistory[domain].filter(
    (t) => now - t < WINDOW_MS,
  );

  requestHistory[domain].push(now);

  const frequency = requestHistory[domain].length;

  const packetSize = details.requestBody
    ? JSON.stringify(details.requestBody).length
    : 0;

  const entropy = calculateEntropy(details.url);
  const domainRisk = scoreDomain(details.url);
  const jsBehavior = 0.2;

  return [packetSize, frequency, entropy, domainRisk, jsBehavior];
}

function calculateEntropy(str) {
  const len = str.length;
  const map = {};

  for (let char of str) {
    map[char] = (map[char] || 0) + 1;
  }

  return Object.values(map).reduce((sum, freq) => {
    const p = freq / len;
    return sum - p * Math.log2(p);
  }, 0);
}

function scoreDomain(url) {
  if (url.startsWith("http://")) return 3;
  if (url.includes("bit.ly")) return 4;
  return 1;
}
