import { generateInsights } from "../src/services/insightService.js";

async function run() {
  const result = await generateInsights();
  console.log(`Generated ${result.suggestions.length} tuning suggestions at ${result.generatedAt}`);
}

run().catch((error) => {
  console.error("Analysis engine failed", error);
  process.exitCode = 1;
});
