import { Router } from "express";
import { resolveConfig, getDynamicConfig, updateDynamicConfig, setPlayerOverride } from "../services/configService.js";

const router = Router();

router.get("/dynamicConfig", async (req, res, next) => {
  try {
    const { playerId } = req.query;
    const result = await resolveConfig(playerId);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

router.get("/dynamicConfig/raw", async (_req, res, next) => {
  try {
    const current = await getDynamicConfig();
    res.json(current);
  } catch (error) {
    next(error);
  }
});

router.patch("/dynamicConfig", async (req, res, next) => {
  try {
    const overrides = await updateDynamicConfig(req.body ?? {});
    res.json(overrides);
  } catch (error) {
    next(error);
  }
});

router.post("/playerOverride", async (req, res, next) => {
  try {
    const { playerId, overrides } = req.body ?? {};
    const payload = await setPlayerOverride(playerId, overrides ?? {});
    res.json({ playerId, overrides: payload });
  } catch (error) {
    next(error);
  }
});

export default router;
