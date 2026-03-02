let behaviorScore = 0;

window.addEventListener("click", () => {
  behaviorScore += 0.01;
});

window.addEventListener("scroll", () => {
  behaviorScore += 0.005;
});

setInterval(() => {
  chrome.runtime.sendMessage({
    type: "telemetry",
    behaviorDeviation: Math.min(1, behaviorScore),
  });
}, 2000);
