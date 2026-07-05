# Twenty-eight

The new generation of virtual try-on

## Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then add your API keys
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment variables

| File | Purpose |
|------|---------|
| `.env.example` | Backend (OpenRouter, providers, models) |
| `frontend/.env.example` | Frontend (`BACKEND_URL`) |

Copy each to `.env` and fill in your values. **Do not commit `.env` files.**

## Project layout

- `api/` — FastAPI routes
- `services/` — Face/body generation pipeline
- `frontend/` — Next.js UI
- `outputs/` — Generated images (gitignored; folder kept via `.gitkeep`)
