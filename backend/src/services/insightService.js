import dayjs from "dayjs";
import { getAllEvents, getAnalyticsSummary } from "./analyticsService.js";
import { readJSON, writeJSON } from "../utils/fileStore.js";

const INSIGHTS_FILE = "insights.json";

export async function generateInsights() {
  const summary = await getAnalyticsSummary();
  const events = await getAllEvents();
  const suggestions = [];

  const starterTest = summary.experiments?.starter_price_test ?? [];
  if (starterTest.length >= 2) {
    const sorted = [...starterTest].sort((a, b) => b.conversionRate - a.conversionRate);
    const best = sorted[0];
    const next = sorted[1];
    if (best && next && best.conversionRate > next.conversionRate + 0.05) {
      suggestions.push({
        type: "experiment",
        message: `Variant ${best.variantId} outperforms ${next.variantId} on conversions. Consider increasing traffic share.`,
      });
    }
  }

  if (detectRewardConversionSpike(events)) {
    suggestions.push({
      type: "rewards",
      message: "Purchases spike after reward streak claims. Review reward pacing to avoid over-generosity.",
    });
  }

  if (summary.boosterUsage < Math.max(summary.dau * 0.1, 5)) {
    suggestions.push({
      type: "boosters",
      message: "Boosters under-used. Check pricing or duration to improve attractiveness.",
    });
  }

  const payload = {
    generatedAt: new Date().toISOString(),
    suggestions,
  };
  await writeJSON(INSIGHTS_FILE, payload);
  return payload;
}

export async function getInsights() {
  return readJSON(INSIGHTS_FILE, { generatedAt: null, suggestions: [] });
}

function detectRewardConversionSpike(events) {
  const rewardClaims = events.filter((e) => e.eventName === "retention_reward_claimed");
  const purchases = events.filter((e) => e.eventName === "purchase_success");
  for (const reward of rewardClaims) {
    const horizon = dayjs(reward.timestamp).add(2, "hour").valueOf();
    const followUp = purchases.find(
      (purchase) => purchase.playerId === reward.playerId && purchase.timestamp >= reward.timestamp && purchase.timestamp <= horizon
    );
    if (followUp) {
      return true;
    }
  }
  return false;
}
