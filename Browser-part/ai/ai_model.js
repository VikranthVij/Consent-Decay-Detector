import { scale } from "./scaler.js";

let weights = null;

// ------------------------------
// Load Weights
// ------------------------------
async function loadWeights() {
  if (!weights) {
    const response = await fetch(
      chrome.runtime.getURL("ai/model_weights.json"),
    );
    weights = await response.json();
  }
}

// ------------------------------
// Math Utilities
// ------------------------------
function matMul(vec, matrix) {
  const output = new Array(matrix[0].length).fill(0);

  for (let j = 0; j < matrix[0].length; j++) {
    for (let i = 0; i < vec.length; i++) {
      output[j] += vec[i] * matrix[i][j];
    }
  }

  return output;
}

function addBias(vec, bias) {
  return vec.map((v, i) => v + bias[i]);
}

function relu(vec) {
  return vec.map((v) => Math.max(0, v));
}

function sigmoid(x) {
  return 1 / (1 + Math.exp(-x));
}

// ------------------------------
// AI Prediction
// ------------------------------
export async function predict(rawFeatures) {
  await loadWeights();

  const x = scale(rawFeatures);

  // ---- Layer 0 (6 → 16) ----
  let z0 = matMul(x, weights.layer_0_weights);
  z0 = addBias(z0, weights.layer_0_bias);
  let a0 = relu(z0);

  // ---- Layer 1 (16 → 8) ----
  let z1 = matMul(a0, weights.layer_1_weights);
  z1 = addBias(z1, weights.layer_1_bias);
  let a1 = relu(z1);

  // ---- Layer 2 (8 → 1) ----
  let z2 = matMul(a1, weights.layer_2_weights);
  z2 = addBias(z2, weights.layer_2_bias);

  return sigmoid(z2[0]);
}
