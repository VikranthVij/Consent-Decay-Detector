const thresholds = {
  passive: 0.75,
  balanced: 0.55,
  aggressive: 0.35,
};

let currentMode = "balanced";

chrome.storage.local.get(["securityMode"], (res) => {
  if (res.securityMode) currentMode = res.securityMode;
});

function updateRisk(domain, probability) {
  return new Promise((resolve) => {
    chrome.storage.local.get(["domainRisk"], (res) => {
      const domainRisk = res.domainRisk || {};
      const previous = domainRisk[domain] || 0;

      // Risk accumulation
      const updated = Math.min(1, previous * 0.9 + probability * 0.5);

      domainRisk[domain] = updated;

      chrome.storage.local.set({ domainRisk }, () => {
        resolve(updated);
      });
    });
  });
}

export async function evaluateZeroTrust(domain, probability) {
  const threshold = thresholds[currentMode];

  const risk = await updateRisk(domain, probability);

  return {
    domain,
    probability,
    risk,
    threshold,
    malicious: risk > threshold,
    mode: currentMode,
  };
}
