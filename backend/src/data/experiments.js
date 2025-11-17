export const experimentCatalog = [
  {
    id: "starter_price_test",
    active: true,
    assignment: "weighted",
    weights: { A: 0.5, B: 0.5 },
    variants: [
      { id: "A", price: 1.99, label: "Value Starter Pack" },
      { id: "B", price: 3.49, label: "Premium Starter Pack" }
    ]
  },
  {
    id: "dailyRewardIntensity",
    active: true,
    assignment: "balanced",
    variants: [
      { id: "soft", multiplier: 1.0 },
      { id: "medium", multiplier: 1.25 },
      { id: "aggressive", multiplier: 1.75 }
    ]
  },
  {
    id: "booster_strength",
    active: false,
    assignment: "weighted",
    weights: { base: 0.6, plus: 0.4 },
    variants: [
      { id: "base", duration: 300, boost: 1.1 },
      { id: "plus", duration: 420, boost: 1.35 }
    ]
  }
];
