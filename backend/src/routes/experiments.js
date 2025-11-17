import { Router } from "express";
import { assignPlayer, listExperiments, getAssignments } from "../services/experimentService.js";

const router = Router();

router.get("/", async (_req, res, next) => {
  try {
    const experiments = await listExperiments();
    res.json(experiments);
  } catch (error) {
    next(error);
  }
});

router.post("/assign", async (req, res, next) => {
  try {
    const { playerId } = req.body ?? {};
    const assignments = await assignPlayer(playerId);
    res.json({ playerId, assignments });
  } catch (error) {
    next(error);
  }
});

router.get("/:playerId", async (req, res, next) => {
  try {
    const { playerId } = req.params;
    const assignments = await getAssignments(playerId);
    res.json({ playerId, assignments });
  } catch (error) {
    next(error);
  }
});

export default router;
