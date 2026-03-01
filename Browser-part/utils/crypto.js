export async function hashData(data) {
  const encoder = new TextEncoder();
  const encoded = encoder.encode(JSON.stringify(data));

  const hashBuffer = await crypto.subtle.digest("SHA-256", encoded);
  const hashArray = Array.from(new Uint8Array(hashBuffer));

  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}
