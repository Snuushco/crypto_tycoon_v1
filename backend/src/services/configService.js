import merge from "lodash.merge";
import { staticConfig } from "../data/staticConfig.js";
import { listExperiments, getAssignments } from "./experimentService.js";
import { readJSON, writeJSON } from "../utils/fileStore.js";

const DYNAMIC_FILE = "dynamicConfig.json";
const PLAYER_OVERRIDES_FILE = "playerOverrides.json";

export async function getStaticConfig() {
  return staticConfig;
}

export async function getDynamicConfig() {
  const current = await readJSON(DYNAMIC_FILE, {});
  return merge({}, current);
}

export async function updateDynamicConfig(overrides) {
  const merged = merge({}, await getDynamicConfig(), overrides ?? {});
  await writeJSON(DYNAMIC_FILE, merged);
  return merged;
}

export async function setPlayerOverride(playerId, payload) {
  if (!playerId) throw new Error("playerId is required");
  const current = await readJSON(PLAYER_OVERRIDES_FILE, {});
  const next = merge({}, current, { [playerId]: payload });
  await writeJSON(PLAYER_OVERRIDES_FILE, next);
  return next[playerId];
}

export async function resolveConfig(playerId) {
  const base = merge({}, staticConfig);
  const dynamic = await getDynamicConfig();
  const assignments = playerId ? await getAssignments(playerId) : null;
  const experimentOverrides = await deriveExperimentConfig(assignments);
  const playerOverrides = playerId ? await getPlayerOverride(playerId) : {};
  const resolved = merge({}, base, dynamic, experimentOverrides, playerOverrides);
  return {
    playerId,
    assignments: assignments ?? {},
    config: resolved
  };
}

async function getPlayerOverride(playerId) {
  if (!playerId) return {};
  const overrides = await readJSON(PLAYER_OVERRIDES_FILE, {});
  return overrides[playerId] ?? {};
}

async function deriveExperimentConfig(assignments) {
  if (!assignments) return {};
  const experiments = await listExperiments();
  const overrides = {};
  for (const experiment of experiments) {
    const variant = assignments[experiment.id];
    if (!variant) continue;
    const mapped = experimentVariantToConfig(experiment.id, variant);
    merge(overrides, mapped);
  }
  return overrides;
}

function experimentVariantToConfig(experimentId, variant) {
  switch (experimentId) {
    case "starter_price_test":
      return { pricing: { starter_pack: variant.price } };
    case "dailyRewardIntensity":
      return { dailyRewardScaling: { multiplier: variant.multiplier } };
    case "booster_strength":
      return {
        boostValues: {
          defaultMultiplier: variant.boost,
          defaultDurationSeconds: variant.duration
        }
      };
    default:
      return {};
  }
}
