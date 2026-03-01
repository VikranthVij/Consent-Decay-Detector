export function evaluateRules(features) {
  const [burst, xhr, post, thirdParty, beacon, deviation] = features;

  if (beacon > 0.9 && thirdParty > 0.9) {
    return { immediateBlock: true, reason: "Beacon exfiltration pattern" };
  }

  if (post > 0.95 && deviation > 0.8) {
    return { immediateBlock: true, reason: "High POST anomaly" };
  }

  return { immediateBlock: false };
}
