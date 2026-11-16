# CI/CD: Deploy to Vercel from GitHub

How to make every push to this GitHub repository deploy the Gradio AI Twin (`src/app.py`) to Vercel automatically.

## 1. Approach

The app is a self-hosted Gradio server (`gr.ChatInterface(...).launch()`), not a plain ASGI `app` object, so it is deployed as a **Vercel container image** (Container Runtime, Beta on all plans). With the project's framework preset set to `container` (see `vercel.json` below), Vercel builds `Dockerfile.vercel` on every deployment and runs it as an autoscaling Vercel Function.

Why a container instead of Vercel's zero-config Python runtime:

- No code changes are needed. Gradio reads `GRADIO_SERVER_NAME` / `GRADIO_SERVER_PORT` from the environment, so the container makes it listen on `0.0.0.0:80`.
- The root `pyproject.toml` is a large shared "agents" environment (langchain, google-adk, strands, ...). The zero-config Python runtime would install it and risk the 500 MB bundle limit. The image installs only `src/requirements.txt`.

## 2. Deployment files in the repository

These files are already in the repository. They are reproduced here for reference.

### `Dockerfile.vercel` (repository root)

```docker
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

WORKDIR /app
COPY src/requirements.txt src/requirements.txt
RUN uv pip install --system --no-cache -r src/requirements.txt

COPY src/ src/

ENV GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=80 \
    GRADIO_ANALYTICS_ENABLED=False \
    PYTHONUNBUFFERED=1

EXPOSE 80
CMD ["python", "-m", "src.app"]
```

The container must serve HTTP on port 80 (or on the port set in the `PORT` project environment variable). Data files (`profile.pdf`, `summary.txt`, `aiclone.jpeg`) are resolved relative to the modules, so the working directory does not matter.

### `vercel.json` (repository root)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "container"
}
```

This file is required. On import, Vercel detects `src/app.py` and saves the project as **FastAPI**, which ignores the Dockerfile and fails the build with `Found src/app.py but it does not define a top-level "app" FastAPI instance`. `"framework": null` ("Other") is not enough either: the build succeeds but produces an empty deployment. Only the `container` preset builds the image.

### `.vercelignore` (repository root)

Keeps local-only files out of CLI uploads:

```
.env
.venv/
**/__pycache__/
prompts/
changes/
doc/
```

### `.gitignore` additions

Secrets and the local Vercel link are ignored:

```
.env
.vercel
```

## 3. One-time Vercel setup (Git integration, recommended)

1. Push the repository to GitHub.
2. In the Vercel dashboard: **Add New... > Project > Import Git Repository** and pick this repository (install the Vercel GitHub App when prompted).
3. Keep **Root Directory** as the repository root, where `Dockerfile.vercel` lives. The framework preset comes from `vercel.json` (`container`). Whatever the import screen shows is overridden. No build command or output directory is needed.
4. Add the environment variables (section 4) **before** the first deployment, then click **Deploy**.

From then on:

| Git event | Vercel result |
|-----------|---------------|
| Push / merge to `main` | Production deployment |
| Push to any other branch or a pull request | Preview deployment with its own URL (posted on the PR) |

The production branch can be changed in **Project Settings > Git**.

## 4. Environment variables

The app needs these at runtime. On Vercel there is no `.env` file, so `load_dotenv()` loads nothing and the values come from the project environment.

| Name | Used by | Environments |
|------|---------|--------------|
| `OPENAI_API_KEY` | `app.py` (OpenAI client) | Production, Preview |
| `PUSHOVER_USER` | `tools.py` (notifications) | Production, Preview |
| `PUSHOVER_TOKEN` | `tools.py` (notifications) | Production, Preview |

### Option A: dashboard

**Project Settings > Environment Variables > Add**. Enter the name and value, tick the environments, and mark the value **Sensitive**.

### Option B: Vercel CLI

```
pnpm add -g vercel
vercel login
vercel link                                   # run in the repository root, creates .vercel/
vercel env add OPENAI_API_KEY production      # prompts for the value
vercel env add OPENAI_API_KEY preview
vercel env add PUSHOVER_USER production
vercel env add PUSHOVER_USER preview
vercel env add PUSHOVER_TOKEN production
vercel env add PUSHOVER_TOKEN preview
vercel env ls                                 # verify
```

Optionally, use a separate OpenAI key or Pushover token for Preview, so test deployments can be revoked independently.

**Environment-variable changes apply only to new deployments.** Redeploy after changing them (**Deployments > ... > Redeploy**, or `vercel --prod`).

## 5. Alternative: GitHub Actions instead of Git integration

Use this when deployments must wait for other CI steps. Disconnect the Git integration first (**Project Settings > Git > Disconnect**) to avoid double deployments.

1. Run `vercel link` locally. Copy `orgId` and `projectId` from `.vercel/project.json`.
2. Create a token at **vercel.com > Account Settings > Tokens**.
3. In GitHub: **Settings > Secrets and variables > Actions**, add Repository secrets`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.
4. Add `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
  pull_request:

env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7       # node24 runtime; v4 triggers the Node.js 20 deprecation warning
      - uses: pnpm/action-setup@v6      # node24 runtime
        with:
          version: 10
      - name: Install Vercel CLI
        run: pnpm add -g vercel@65.16.0
      - name: Deploy production
        if: github.ref == 'refs/heads/main'
        run: vercel deploy --prod --yes --token=${{ secrets.VERCEL_TOKEN }}
      - name: Deploy preview
        if: github.ref != 'refs/heads/main'
        run: vercel deploy --yes --token=${{ secrets.VERCEL_TOKEN }}
```

The image is built remotely by Vercel, and runtime variables still come from the Vercel project (section 4). Never put `OPENAI_API_KEY` or the Pushover secrets in GitHub Actions secrets for this workflow; it does not need them.

## 6. Verify a deployment

```
vercel ls                         # recent deployments
vercel inspect <deployment-url>   # build details
vercel logs <deployment-url>      # runtime logs ("Tool called: ..." lines come from tools.py)
```

Open the URL. The title banner should show the `aiclone.jpeg` background, and a question should get an answer.

Preview deployments are behind Vercel Authentication. Use `vercel curl <deployment-url>` to fetch them from the CLI. `vercel inspect <deployment-url>` should list a `λ container` build; an empty Builds list means the image was not built.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Found src/app.py but it does not define a top-level "app" FastAPI instance` | Framework preset is FastAPI | `vercel.json` with `"framework": "container"` |
| Build finishes in milliseconds, no `λ container` in `vercel inspect` | Preset is "Other" (`null`) | Same as above |
| Page returns 500 | `OPENAI_API_KEY` not set: `OpenAI()` raises `Missing credentials` at import | Set the section 4 variables, then redeploy |
| `Node.js 20 is deprecated ... actions/checkout@v4, pnpm/action-setup@v4` | Warning only, not a failure | Use `actions/checkout@v7`, `pnpm/action-setup@v6` |

## 7. Known limitations

- **Cold starts:** containers scale to zero after 5 minutes idle in production (30 s in preview). The first request after idle starts Python, Gradio and parses `profile.pdf`.
- **Gradio queue state is in memory.** Gradio's queue keeps per-session state in the process, and Vercel does not pin requests to an instance. Under parallel load, a follow-up request can land on a different instance and fail. This is fine for a low-traffic personal twin. For heavier traffic, use a single long-lived host instead.
- **Duration:** each request is capped by the plan's max function duration (300 s on Hobby), which is far above a normal chat turn.
- **Rollback:** `vercel rollback` or **Deployments > Promote** on an earlier deployment. Promotion is instant and needs no rebuild.
