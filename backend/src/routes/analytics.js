import { Router } from "express";
import { logEventBatch, getAnalyticsSummary } from "../services/analyticsService.js";
import { generateInsights, getInsights } from "../services/insightService.js";

const router = Router();

router.post("/eventBatch", async (req, res, next) => {
  try {
    const result = await logEventBatch(req.body ?? {});
    res.json(result);
  } catch (error) {
    next(error);
  }
});

router.get("/summary", async (_req, res, next) => {
  try {
    const summary = await getAnalyticsSummary();
    res.json(summary);
  } catch (error) {
    next(error);
  }
});

router.get("/insights", async (_req, res, next) => {
  try {
    const latest = await getInsights();
    res.json(latest);
  } catch (error) {
    next(error);
  }
});

router.post("/insights/refresh", async (_req, res, next) => {
  try {
    const refreshed = await generateInsights();
    res.json(refreshed);
  } catch (error) {
    next(error);
  }
});

export default router;
