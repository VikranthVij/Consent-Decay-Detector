// ===============================
// Zero Trust AI Firewall
// ===============================

import { extractFeatures } from "./ai/feature_extractor.js";
import { predict } from "./ai/ai_model.js";
import { evaluateZeroTrust } from "./core/zero_trust.js";
import { blockDomain, blockRequest } from "./core/dnr_manager.js";
import { logEvent } from "./core/logger.js";
import { unblockDomain } from "./core/dnr_manager.js";

let engineEnabled = true;
let mode = "balanced"; // strict | balanced | monitor
let telemetry = { behaviorDeviation: 0 };
let globalRiskScore = 0;

// -------------------------------
// Load state
// -------------------------------
chrome.storage.local.get(["engineEnabled", "mode"], (res) => {
  if (res.engineEnabled === false) engineEnabled = false;
  if (res.mode) mode = res.mode;
});

// -------------------------------
// Storage changes
// -------------------------------
chrome.storage.onChanged.addListener((changes) => {
  if (changes.engineEnabled) engineEnabled = changes.engineEnabled.newValue;

  if (changes.mode) mode = changes.mode.newValue;
});

// -------------------------------
// Threshold logic
// -------------------------------
function getThreshold() {
  if (mode === "strict") return 0.7;
  if (mode === "balanced") return 0.88;
  if (mode === "monitor") return 1.1; // impossible to trigger
  return 0.88;
}

// -------------------------------
// Navigation
// -------------------------------
chrome.webNavigation.onCommitted.addListener(async (details) => {
  if (!engineEnabled) return;
  if (!details.url.startsWith("http")) return;

  const url = new URL(details.url);
  const domain = url.hostname;

  try {
    // Manual overrides
    const { allowedDomains = [], manuallyBlocked = [] } =
      await chrome.storage.local.get(["allowedDomains", "manuallyBlocked"]);

    if (allowedDomains.includes(domain)) {
      await unblockDomain(domain);
      return;
    }

    if (manuallyBlocked.includes(domain)) {
      await blockDomain(domain);
      return;
    }

    const features = extractFeatures(details, telemetry);
    const probability = await predict(features);

    const threshold = getThreshold();

    if (probability > threshold && mode !== "monitor") {
      await blockRequest(details.url);
      logEvent("BLOCK_REQUEST_AI", { domain, probability });
    }

    const state = await evaluateZeroTrust(domain, probability);

    globalRiskScore = state.risk;
    chrome.storage.local.set({ globalRiskScore });

    if (mode === "strict" && state.risk > 80) {
      await blockDomain(domain);
      logEvent("BLOCK_DOMAIN_ZERO_TRUST", { domain });
    }
  } catch (err) {
    console.error("Background error:", err);
  }
});
console.log("FEATURES:", features);
