# Twenty-eight Frontend

Simple web UI for the Twenty-eight VTON flow (face → body).

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Backend (separate terminal):

```bash
uvicorn api.main:app --reload --port 8000
```

Open [http://localhost:3000](http://localhost:3000)

## Flow

- **Home** — Start flow
- **/flow** — Face → Body → Done (single connected wizard)

All UI copy lives in `src/lib/copy.ts`.
