import fs from "fs/promises";
import path from "path";

const ROOT = path.resolve(process.cwd(), "data");

export async function readJSON(fileName, fallback) {
  try {
    const filePath = path.join(ROOT, fileName);
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw);
  } catch (error) {
    return fallback ?? null;
  }
}

export async function writeJSON(fileName, payload) {
  const filePath = path.join(ROOT, fileName);
  await fs.writeFile(filePath, JSON.stringify(payload, null, 2), "utf-8");
  return payload;
}
