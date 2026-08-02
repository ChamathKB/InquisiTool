# Frontend

React + TypeScript (Vite) frontend for InquisiTool.

## Structure

```
src/
  keycloak.ts             — Keycloak singleton (reads VITE_* env vars)
  AuthProvider.tsx        — OIDC init (login-required + PKCE), exposes token + userId
  api.ts                  — typed fetch client, auto-refreshes token before each call
  types.ts                — Campaign, SurveyRequest, SurveyResponse interfaces
  App.tsx                 — BrowserRouter + navbar + 3 routes
  main.tsx                — entry, wraps in AuthProvider
  index.css               — minimal design system (cards, chat bubbles, forms)
  pages/
    CampaignsPage.tsx     — list / create / delete campaigns + "Take Survey" link
    KnowledgeBasePage.tsx — create collection, upload PDF, delete collection
    SurveyPage.tsx        — chat-bubble UI, starts session on mount, sends answers
```

## Dev Setup

1. Install dependencies:

    ```bash
    cd frontend
    npm install
    ```

2. Create `.env` (already included, adjust if needed):

    ```env
    VITE_KEYCLOAK_URL=http://localhost:8080
    VITE_KEYCLOAK_REALM=inquisitool
    VITE_KEYCLOAK_CLIENT_ID=inquisitool-frontend
    ```

3. Run dev server:

    ```bash
    npm run dev
    ```

    Runs on `http://localhost:5173`. API calls are proxied to `http://localhost:8000` via Vite's dev proxy.

## Keycloak Client Setup

Create a new client in the `inquisitool` realm for the frontend:

1. Go to **Keycloak Admin Console** → your realm → **Clients** → **Create client**
2. Set:
   - **Client ID:** `inquisitool-frontend`
   - **Client type:** `OpenID Connect`
3. On the next screen:
   - **Client authentication:** OFF (public client — no secret needed)
   - **Standard flow:** ON
4. On the settings screen:
   - **Valid redirect URIs:** `http://localhost:5173/*`
   - **Valid post logout redirect URIs:** `http://localhost:5173/*`
   - **Web origins:** `http://localhost:5173`
5. Save.

For production, replace `http://localhost:5173` with your deployed frontend URL.

## Production Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static file server or add to the existing Docker Compose setup with an nginx container.

## Docker Compose Deployment

The frontend runs as a separate Nginx container that serves the React build and reverse-proxies API routes (`/campaigns`, `/knowledgebases`, `/query`) to the FastAPI container — no CORS configuration needed.

`VITE_*` variables are baked into the bundle at build time via Docker build args. The docker-compose defaults fall back to `localhost` values, so override them in the root `.env` for production:

```env
VITE_KEYCLOAK_URL=https://auth.yourdomain.com
VITE_KEYCLOAK_REALM=inquisitool
VITE_KEYCLOAK_CLIENT_ID=inquisitool-frontend
```

Then build and start:

```bash
docker-compose up -d --build frontend
```

Or pass them inline without touching `.env`:

```bash
VITE_KEYCLOAK_URL=https://auth.yourdomain.com \
VITE_KEYCLOAK_REALM=inquisitool \
VITE_KEYCLOAK_CLIENT_ID=inquisitool-frontend \
docker-compose up -d --build frontend
```
