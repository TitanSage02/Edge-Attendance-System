# Server — Frontend (React + TypeScript)

Admin dashboard for the Edge Attendance System. Lets administrators and trainers enroll students, monitor edge units, review attendance in real time, and run exports.

## Tech

React 18 · TypeScript · Vite · Tailwind CSS · shadcn/ui · TanStack Query · React Router · React Hook Form + Zod · Axios · WebSockets.

## Setup & run

This project standardizes on **npm** (a single lockfile, `package-lock.json`).

```bash
cd server/frontend
cp .env.example .env            # set VITE_API_URL to your backend
npm install
npm run dev                     # http://localhost:5173
```

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start the Vite dev server (HMR) |
| `npm run build` | Production build |
| `npm run build:dev` | Development-mode build |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint |

## Configuration

All runtime config comes from `VITE_*` environment variables (see `.env.example`):

- `VITE_API_URL` — backend API base URL (e.g. `http://localhost:8000/api/v1`)
- `VITE_API_TIMEOUT` / `VITE_API_LONG_TIMEOUT` / `VITE_API_HEAVY_TIMEOUT` — request timeouts

## Features

- 👥 Student management (enrollment, RFID + face)
- ✅ Real-time presence tracking via WebSockets
- 📚 Module/class management
- 🔔 Absence and event alerts
- 📊 Analytics dashboards and exports
- 👤 Role-based user management
- 🤖 Optional AI assistant (RAG) panel

## Structure

```
server/frontend/
├── public/             # static assets
├── src/
│   ├── components/     # UI components (incl. shadcn/ui)
│   ├── hooks/          # custom hooks (auth, toast, ...)
│   ├── pages/          # route pages
│   ├── services/       # API clients + WebSocket layer
│   ├── types/          # shared TypeScript types
│   └── utils/          # helpers
└── vite.config.ts
```
