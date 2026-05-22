# SeeWeeS Dispatch Report Dashboard

Standalone Next.js prototype for the UCLA MSBA AI Agents Project Challenge dashboard.

The dashboard uses static KPI snapshots from the completed teammate LangGraph pipeline. It does not import Python code, CSV files, PDFs, generated reports, or anything outside this `web/` folder, so the folder can be moved into another repository and still run independently.

## Local Development

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
```

## Vercel

Deploy this folder as the Vercel project root.

## Data Source

The static scenario data lives in `lib/scenarios.ts` and reflects these teammate pipeline scenarios:

- Demand Spike x1.2
- Driver Shortage: 30% unavailable
- Warehouse Closure: Boston-MGH
- Weather Event: risk 2/3

If the Python pipeline outputs new KPI results later, update `lib/scenarios.ts` and rebuild the app.
