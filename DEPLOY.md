# 🌍 Deploying Study Buddy to the web (free)

The goal: your client opens **one URL** and uses the app — nothing to download, nothing to install.

**Recommended platform: [Streamlit Community Cloud](https://share.streamlit.io)** — it's free, made for Streamlit apps, gives you a public `https://...streamlit.app` URL, and deploys straight from GitHub. Below are the exact steps (≈10 minutes, one time).

---

## Step 0 — What's already prepared in this repo

- ✅ `config.py` — reads `GROQ_API_KEY` from `.env` locally **or** Streamlit secrets on cloud (no code changes needed between the two)
- ✅ `.streamlit/secrets.toml.example` — shows the exact secrets format
- ✅ `requirements.txt` — cloud-safe dependency pins
- ✅ `.gitignore` — already excludes `.env`, `venv/`, `.chroma/`, `*.pdf` (your key and documents will **not** be pushed)

## Step 1 — Create a GitHub repository

1. Sign up / log in at **https://github.com**
2. Click **+ → New repository** → name it `study-buddy` → set **Private** (recommended) → **Create repository**

## Step 2 — Push this project to GitHub

Run these in the project folder (`C:\Users\chara\Downloads\Files\study-buddy`), one at a time:

```bash
git init
git add .
git commit -m "Study Buddy: multi-agent RAG app with OCR support"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/study-buddy.git
git push -u origin main
```

(Git will prompt for your GitHub username + a token — create one at https://github.com/settings/tokens if asked, or use GitHub Desktop if you prefer clicking.)

## Step 3 — Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and **Sign in with GitHub** (free account)
2. Click **Create app** (or "New app") → **Deploy a public app from GitHub**
3. Fill in:
   - **Repository:** `YOUR_USERNAME/study-buddy`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** pick a nice name, e.g. `study-buddy` → your app will live at `https://study-buddy-XXXX.streamlit.app`
4. **Before clicking Deploy** — open **Advanced settings → Secrets** and paste:

   ```toml
   GROQ_API_KEY = "gsk_paste_your_real_key_here"
   ```

5. Click **Deploy**. First build takes ~5 minutes (it installs packages and downloads the embedding model). Then your public URL is live. 🎉

## Step 4 — Share it

Send your client the URL (`https://...streamlit.app`). They open it in any browser — phone or laptop — upload a PDF, and ask questions. Nothing to install.

## Notes & limits (free tier)

- **Groq free tier:** generous per-minute/per-day limits on `openai/gpt-oss-120b`; if the client hits a 429, the app already shows a friendly "wait a minute" message.
- **Streamlit Cloud free tier:** the app sleeps after ~7 days of inactivity (it wakes on the next visit, but uploads/index are wiped since `.chroma/` is ephemeral on the cloud). For a client demo this is fine; if persistence matters, that's a future upgrade (e.g. remote vector DB).
- **Changing the key later:** edit it under your app's **⋯ menu → Settings → Secrets** on share.streamlit.io — no redeploy needed.
- **Updating the app:** after any code change, `git add . && git commit -m "..." && git push` — the cloud redeploys automatically.

## Alternative platforms (if you outgrow the free tier)

| Platform | Cost | Notes |
|---|---|---|
| Streamlit Community Cloud | Free | What this guide uses |
| Hugging Face Spaces | Free | Same repo, choose "Streamlit" SDK |
| Render / Railway | ~$5/mo | Persistent disk → uploads survive restarts |
| Your own VPS | varies | Full control, `streamlit run app.py` behind nginx |
