const toggle = document.getElementById("engineToggle");
const riskScore = document.getElementById("riskScore");
const modeSelect = document.getElementById("modeSelect");
const dashboardBtn = document.getElementById("dashboardBtn");

chrome.storage.local.get(
  ["engineEnabled", "globalRiskScore", "mode"],
  (res) => {
    toggle.checked = res.engineEnabled !== false;
    riskScore.textContent = res.globalRiskScore || 0;
    modeSelect.value = res.mode || "balanced";
  },
);

toggle.addEventListener("change", () => {
  chrome.storage.local.set({ engineEnabled: toggle.checked });
});

modeSelect.addEventListener("change", () => {
  chrome.storage.local.set({ mode: modeSelect.value });
});

dashboardBtn.addEventListener("click", () => {
  chrome.tabs.create({
    url: chrome.runtime.getURL("dashboard/dashboard.html"),
  });
});
chrome.storage.onChanged.addListener((changes) => {
  if (changes.globalRiskScore) {
    riskScore.textContent = changes.globalRiskScore.newValue;
  }
});
