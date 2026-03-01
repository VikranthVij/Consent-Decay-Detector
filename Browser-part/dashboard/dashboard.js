const allowInput = document.getElementById("allowInput");
const blockInput = document.getElementById("blockInput");
const allowBtn = document.getElementById("allowBtn");
const blockBtn = document.getElementById("blockBtn");

const allowedList = document.getElementById("allowedList");
const blockedList = document.getElementById("blockedList");

function render() {
  chrome.storage.local.get(["allowedDomains", "manuallyBlocked"], (res) => {
    const allowed = res.allowedDomains || [];
    const blocked = res.manuallyBlocked || [];

    allowedList.innerHTML = allowed.map((d) => `<div>${d}</div>`).join("");
    blockedList.innerHTML = blocked.map((d) => `<div>${d}</div>`).join("");
    const logsDiv = document.getElementById("logs");

    chrome.storage.local.get(["logs"], (res) => {
      const logs = res.logs || [];
      logsDiv.innerHTML = logs
        .slice(0, 50)
        .map((l) => `<div>${l}</div>`)
        .join("");
    });
  });
}

allowBtn.addEventListener("click", () => {
  const domain = allowInput.value.trim();
  if (!domain) return;

  chrome.storage.local.get(["allowedDomains"], (res) => {
    const list = res.allowedDomains || [];
    if (!list.includes(domain)) {
      list.push(domain);
      chrome.storage.local.set({ allowedDomains: list }, render);
    }
  });
});

blockBtn.addEventListener("click", () => {
  const domain = blockInput.value.trim();
  if (!domain) return;

  chrome.storage.local.get(["manuallyBlocked"], (res) => {
    const list = res.manuallyBlocked || [];
    if (!list.includes(domain)) {
      list.push(domain);
      chrome.storage.local.set({ manuallyBlocked: list }, render);
    }
  });
});

render();
