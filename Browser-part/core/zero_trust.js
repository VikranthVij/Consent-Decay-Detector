import { blockDomain } from "./dnr_manager.js";

const thresholds = {
  passive: 0.75,
  balanced: 0.55,
  aggressive: 0.35,
};

let currentMode = "balanced";

chrome.storage.local.get(["securityMode"], (res) => {
  if (res.securityMode) currentMode = res.securityMode;
});

export async function evaluateZeroTrust(domain, probability) {
  const { domainState = {} } = await chrome.storage.local.get(["domainState"]);

  const existing = domainState[domain] || {
    risk: 0,
    domainRuleId: null,
  };

  // Risk accumulation
  const updatedRisk = Math.min(1, existing.risk * 0.9 + probability * 0.5);

  const threshold = thresholds[currentMode];

  let domainRuleId = existing.domainRuleId;

  // Escalate to full domain block
  if (updatedRisk > threshold && !domainRuleId) {
    domainRuleId = await blockDomain(domain);
  }

  // De-escalate when risk decays
  if (updatedRisk < threshold * 0.4 && domainRuleId) {
    await removeRule(domainRuleId);
    domainRuleId = null;
  }

  domainState[domain] = {
    risk: updatedRisk,
    domainRuleId,
  };

  await chrome.storage.local.set({ domainState });

  return domainState[domain];
}
