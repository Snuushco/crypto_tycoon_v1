import crypto from "crypto";
import merge from "lodash.merge";
import { experimentCatalog } from "../data/experiments.js";
import { readJSON, writeJSON } from "../utils/fileStore.js";

const ASSIGNMENTS_FILE = "assignments.json";

export async function listExperiments() {
  return experimentCatalog;
}

export async function assignPlayer(playerId) {
  if (!playerId) {
    throw new Error("playerId is required for assignment");
  }
  const existing = await readJSON(ASSIGNMENTS_FILE, {});
  if (existing[playerId]) {
    return existing[playerId];
  }
  const assignments = {};
  for (const experiment of experimentCatalog) {
    if (!experiment.active) continue;
    const variant = pickVariant(experiment, playerId);
    assignments[experiment.id] = variant;
  }
  const updated = merge({}, existing, { [playerId]: assignments });
  await writeJSON(ASSIGNMENTS_FILE, updated);
  return assignments;
}

export async function getAssignments(playerId) {
  const existing = await readJSON(ASSIGNMENTS_FILE, {});
  return existing[playerId] ?? null;
}

function pickVariant(experiment, playerId) {
  const variants = experiment.variants ?? [];
  if (!variants.length) return null;
  if (experiment.assignment === "weighted" && experiment.weights) {
    const roll = deterministicFloat(playerId + experiment.id);
    let cumulative = 0;
    for (const variant of variants) {
      const weight = experiment.weights[variant.id] ?? 0;
      cumulative += weight;
      if (roll <= cumulative) {
        return variant;
      }
    }
    return variants[variants.length - 1];
  }
  const index = deterministicIndex(playerId, experiment.id, variants.length);
  return variants[index];
}

function deterministicIndex(playerId, experimentId, length) {
  if (!length) return 0;
  const hash = crypto.createHash("sha256").update(`${playerId}:${experimentId}`).digest("hex");
  const numeric = parseInt(hash.slice(0, 8), 16);
  return numeric % length;
}

function deterministicFloat(seed) {
  const hash = crypto.createHash("sha256").update(seed).digest("hex");
  const numeric = parseInt(hash.slice(0, 8), 16);
  // normalize to 0-1
  return (numeric % 10_000) / 10_000;
}
