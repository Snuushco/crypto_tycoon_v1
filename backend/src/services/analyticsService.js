import { nanoid } from "nanoid";
import dayjs from "dayjs";
import merge from "lodash.merge";
import { readJSON, writeJSON } from "../utils/fileStore.js";

const EVENTS_FILE = "analyticsEvents.json";

export async function logEventBatch({ playerId, events = [], experiments = {}, analyticsOptOut = false }) {
  if (!playerId || analyticsOptOut) {
    return { stored: 0 };
  }
  if (!Array.isArray(events) || !events.length) {
    return { stored: 0 };
  }
  const existing = await readJSON(EVENTS_FILE, []);
  const timestamp = Date.now();
  const normalized = events.map((event) => ({
    id: nanoid(),
    playerId,
    eventName: event.eventName,
    metadata: event.metadata ?? {},
    timestamp: event.timestamp ?? timestamp,
    experiments,
    clientTime: event.timestamp,
  }));
  const next = existing.concat(normalized);
  await writeJSON(EVENTS_FILE, next);
  return { stored: normalized.length };
}

export async function getAllEvents() {
  return readJSON(EVENTS_FILE, []);
}

export async function clearEvents() {
  await writeJSON(EVENTS_FILE, []);
}

export async function getAnalyticsSummary() {
  const events = await getAllEvents();
  const sessions = events.filter((e) => e.eventName === "session_start");
  const dau = uniquePlayersWithin(events, 1);
  const wau = uniquePlayersWithin(events, 7);
  const mau = uniquePlayersWithin(events, 30);
  const sessionLengthAvg = averageValue(
    events.filter((e) => e.eventName === "session_end"),
    (e) => e.metadata?.duration ?? 0
  );
  const retention = {
    d1: retentionRate(sessions, 1),
    d3: retentionRate(sessions, 3),
    d7: retentionRate(sessions, 7),
  };
  const purchaseEvents = events.filter((e) => e.eventName === "purchase_success");
  const conversionRate = computeConversionRate(sessions, purchaseEvents);
  const purchaseBreakdown = tallyBy(purchaseEvents, (e) => e.metadata?.productId ?? "unknown");
  const boosterUsage = events.filter((e) => e.eventName === "booster_used").length;
  const prestigeFrequency = events.filter((e) => e.eventName === "prestige").length;
  const abComparisons = buildABComparisons(events);

  return {
    dau,
    wau,
    mau,
    sessionLengthAvg,
    retention,
    purchaseConversionRate: conversionRate,
    purchaseBreakdown,
    boosterUsage,
    prestigeFrequency,
    experiments: abComparisons,
  };
}

function uniquePlayersWithin(events, days) {
  const cutoff = dayjs().subtract(days, "day").valueOf();
  const set = new Set();
  for (const event of events) {
    if (event.timestamp >= cutoff && event.eventName === "session_start") {
      set.add(event.playerId);
    }
  }
  return set.size;
}

function retentionRate(sessionEvents, dayOffset) {
  if (!sessionEvents.length) return 0;
  const sessionsByPlayer = groupBy(sessionEvents, (e) => e.playerId);
  let returning = 0;
  let cohort = 0;
  for (const [playerId, playerSessions] of sessionsByPlayer) {
    const sorted = playerSessions.map((s) => s.timestamp).sort();
    const first = sorted[0];
    if (!first) continue;
    cohort += 1;
    const horizon = dayjs(first).add(dayOffset, "day").valueOf();
    const cameBack = sorted.some((ts) => ts >= horizon);
    if (cameBack) returning += 1;
  }
  return cohort ? Number((returning / cohort).toFixed(2)) : 0;
}

function computeConversionRate(sessionStarts, purchases) {
  const uniquePlayers = new Set(sessionStarts.map((s) => s.playerId));
  const purchasingPlayers = new Set(purchases.map((p) => p.playerId));
  if (!uniquePlayers.size) return 0;
  return Number((purchasingPlayers.size / uniquePlayers.size).toFixed(2));
}

function tallyBy(items, selector) {
  const tally = {};
  for (const item of items) {
    const key = selector(item);
    tally[key] = (tally[key] ?? 0) + 1;
  }
  return tally;
}

function averageValue(items, selector) {
  if (!items.length) return 0;
  const total = items.reduce((sum, item) => sum + Number(selector(item) ?? 0), 0);
  return Number((total / items.length).toFixed(2));
}

function groupBy(items, selector) {
  const map = new Map();
  for (const item of items) {
    const key = selector(item);
    if (!map.has(key)) {
      map.set(key, []);
    }
    map.get(key).push(item);
  }
  return map;
}

function buildABComparisons(events) {
  const experiments = {};
  for (const event of events) {
    if (!event.experiments) continue;
    for (const [experimentId, variant] of Object.entries(event.experiments)) {
      if (!experiments[experimentId]) {
        experiments[experimentId] = {};
      }
      const bucket = experiments[experimentId];
      if (!bucket[variant.id || variant.variant || variant]) {
        bucket[variant.id || variant.variant || variant] = {
          players: new Set(),
          purchases: 0,
          sessions: [],
          income: 0,
        };
      }
      const entry = bucket[variant.id || variant.variant || variant];
      entry.players.add(event.playerId);
      if (event.eventName === "purchase_success") {
        entry.purchases += 1;
        entry.income += Number(event.metadata?.price ?? 0);
      }
      if (event.eventName === "session_end") {
        entry.sessions.push(Number(event.metadata?.duration ?? 0));
      }
    }
  }
  const result = {};
  for (const [experimentId, variants] of Object.entries(experiments)) {
    result[experimentId] = Object.entries(variants).map(([variantId, stats]) => {
      const sessionAvg = stats.sessions.length
        ? stats.sessions.reduce((sum, value) => sum + value, 0) / stats.sessions.length
        : 0;
      return {
        variantId,
        players: stats.players.size,
        conversionRate: stats.players.size ? stats.purchases / stats.players.size : 0,
        sessionLength: Number(sessionAvg.toFixed(2)),
        incomeVelocity: stats.players.size ? stats.income / stats.players.size : 0,
      };
    });
    if (result[experimentId].length >= 2) {
      const [control, challenger] = result[experimentId];
      result[experimentId] = result[experimentId].map((variant) => ({
        ...variant,
        zScore: computeZScore(control, variant),
      }));
    }
  }
  return result;
}

function computeZScore(control, variant) {
  if (!control || variant.players <= 0 || control.players <= 0) {
    return 0;
  }
  const p1 = control.conversionRate;
  const p2 = variant.conversionRate;
  const n1 = control.players;
  const n2 = variant.players;
  const pooled = (p1 * n1 + p2 * n2) / (n1 + n2);
  const numerator = p2 - p1;
  const denominator = Math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2)) || 1;
  return Number((numerator / denominator).toFixed(2));
}
