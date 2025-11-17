# Crypto Tycoon v1

Een datagedreven, terminal-based tycoon game waarin je een crypto-imperium runt. Gameplay, monetization en UX worden nu continu geoptimaliseerd via een geïntegreerde A/B-testing-, analytics- en live-configlaag.

## Belangrijkste capabilities
- **Realtime marktsimulatie**: volatiliteit, trends en marktsentiment sturen prijsbewegingen.
- **Handel & mining**: koop assets, bouw rigs en bepaal je reward pacing.
- **Experiment framework**: nieuwe spelers worden deterministisch in varianten geplaatst (starter prijzen, daily reward intensiteit, booster-sterkte).
- **Analytics layer**: events worden lokaal gebufferd, gecomprimeerd (gzip) en elke 15s naar `/api/analytics/eventBatch` gestuurd.
- **Live config & tuning**: `GET /api/game/dynamicConfig` levert gemergede settings (static → dynamic → experiment → player). Variabelen kunnen zonder redeploy aangepast worden.
- **Admin dashboard**: React-admin UI (`?admin=true`) met KPIs, cohortkaartjes, experiment-overzicht en automatische tuning hints vanuit de analysis engine.

## Projectstructuur
```
backend/    -> Express API + storage + analysis engine
frontend/   -> Vite + React admin UI
src/        -> Python game + services (analytics client, config manager, experiments)
```

## Installatie & runbooks
1. **Game (Python 3.10+)**
   ```bash
   py main.py
   ```
   Kies een speler-ID zodat experimenten en analytics per account worden bijgehouden.

2. **Backend API**
   ```bash
   cd backend
   npm install        # al uitgevoerd, alleen nodig bij verse clone
   npm run dev        # start op http://localhost:4000
   ```
   Routes o.a.:
   - `POST /api/experiments/assign`
   - `POST /api/analytics/eventBatch`
   - `GET /api/analytics/summary`
   - `GET /api/game/dynamicConfig`
   - `GET /api/analytics/insights`

3. **Admin dashboard**
   ```bash
   cd frontend
   npm install        # al uitgevoerd, alleen nodig bij verse clone
   npm run dev        # standaard op http://localhost:5173
   ```
   Voeg `?admin=true` toe aan de URL om toegang te krijgen.

## Analytics events
De client-side `AnalyticsClient` respecteert een opt-out flag en batcht events (10–20s window). Voorbeelden:
- `session_start`, `session_end`
- `shop_open`
- `purchase_attempt`, `purchase_success`
- `upgrade_performed`
- `retention_reward_claimed`
- `prestige`, `booster_used` (reservering voor toekomstige features)

Back-end payloads worden gecomprimeerd met gzip en non-blocking verstuurd. Falen = drop (geen impact op gameplay).

## Automated tuning & dashboard
- **Analysis engine** (`npm run analysis`): leest event store en schrijft aanbevelingen naar `data/insights.json`.
- **Dashboard metrics**: DAU/WAU/MAU, sessieduur, D1/D3/D7 retention, purchase conversion, booster usage, prestige frequency.
- **Experimentvergelijking**: conversies, sessieduur, income velocity + placeholder Z-score.

## Tests draaien
```bash
py -m unittest discover -s tests
```

## Roadmap ideeën
- Persistentie van saves en cloud-profielen.
- Dagelijkse events en quests met quest analytics.
- UI-upgrade via Rich/Textual.
- Leaderboards met seeds + publishing pipeline.
