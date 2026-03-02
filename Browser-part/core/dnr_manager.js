let ruleCounter = 10000;

// Keep track of domain → rule IDs
async function storeRule(domain, id) {
  const { domainRules = {} } = await chrome.storage.local.get(["domainRules"]);

  if (!domainRules[domain]) domainRules[domain] = [];
  domainRules[domain].push(id);

  await chrome.storage.local.set({ domainRules });
}

async function getNextRuleId() {
  const rules = await chrome.declarativeNetRequest.getDynamicRules();

  const existingIds = rules.map((r) => r.id);

  while (existingIds.includes(ruleCounter)) {
    ruleCounter++;
  }

  return ruleCounter++;
}

// ----------------------------
// Block single request
// ----------------------------
export async function blockRequest(url) {
  const id = await getNextRuleId();

  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [
      {
        id,
        priority: 1,
        action: { type: "block" },
        condition: {
          urlFilter: url,
          resourceTypes: ["main_frame", "xmlhttprequest"],
        },
      },
    ],
    removeRuleIds: [],
  });
}

// ----------------------------
// Block entire domain
// ----------------------------
export async function blockDomain(domain) {
  const id = await getNextRuleId();

  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [
      {
        id,
        priority: 1,
        action: { type: "block" },
        condition: {
          urlFilter: `||${domain}^`,
          resourceTypes: ["main_frame", "xmlhttprequest"],
        },
      },
    ],
    removeRuleIds: [],
  });

  await storeRule(domain, id);

  const { blockedDomains = [] } = await chrome.storage.local.get([
    "blockedDomains",
  ]);

  if (!blockedDomains.includes(domain)) {
    blockedDomains.push(domain);
    await chrome.storage.local.set({ blockedDomains });
  }
}

// ----------------------------
// Unblock domain
// ----------------------------
export async function unblockDomain(domain) {
  const { domainRules = {} } = await chrome.storage.local.get(["domainRules"]);

  const ruleIds = domainRules[domain] || [];

  if (ruleIds.length > 0) {
    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: [],
      removeRuleIds: ruleIds,
    });
  }

  delete domainRules[domain];

  await chrome.storage.local.set({ domainRules });

  const { blockedDomains = [] } = await chrome.storage.local.get([
    "blockedDomains",
  ]);

  const updated = blockedDomains.filter((d) => d !== domain);

  await chrome.storage.local.set({ blockedDomains: updated });
}
