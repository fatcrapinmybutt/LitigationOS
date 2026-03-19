# Events / Timeline API (v1)

## GET /api/events
Params:
- seed=NODE_ID (optional)
- from=YYYY-MM-DD (optional)
- to=YYYY-MM-DD (optional)
- limit=500 (optional, max 5000)

## GET /api/timeline
Events linked to a seed in a ±window around today.
Params:
- seed=NODE_ID (required)
- days=365 (optional; max 3650)
- limit=500 (optional; max 5000)

## GET /api/event
Params:
- id=EVENT_ID (required)

## POST /api/event
Create a manual event.
Body:
{
  "title": "…",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD" (optional),
  "tags": "csv" (optional),
  "node_id": "NODE_ID" (optional),
  "provenance_json": {...} (optional)
}
