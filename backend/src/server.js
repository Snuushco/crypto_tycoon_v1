import express from "express";
import cors from "cors";
import compression from "compression";
import morgan from "morgan";
import zlib from "zlib";

import analyticsRouter from "./routes/analytics.js";
import configRouter from "./routes/config.js";
import experimentsRouter from "./routes/experiments.js";

const app = express();
const PORT = process.env.PORT || 4000;
const jsonParser = express.json({ limit: "1mb" });

app.use(cors());
app.use(compression());
app.use(morgan("dev"));

app.use((req, res, next) => {
  if (req.headers["content-encoding"] === "gzip") {
    const chunks = [];
    req
      .on("data", (chunk) => chunks.push(chunk))
      .on("end", () => {
        try {
          const buffer = Buffer.concat(chunks);
          const decompressed = zlib.gunzipSync(buffer).toString("utf-8");
          req.body = JSON.parse(decompressed);
          next();
        } catch (error) {
          next(error);
        }
      });
  } else {
    jsonParser(req, res, next);
  }
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use("/api/analytics", analyticsRouter);
app.use("/api/game", configRouter);
app.use("/api/experiments", experimentsRouter);

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ message: err.message || "Internal server error" });
});

app.listen(PORT, () => {
  console.log(`Analytics & experimentation API listening on port ${PORT}`);
});
