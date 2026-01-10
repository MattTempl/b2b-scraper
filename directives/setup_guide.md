# Deployment Guide: B2B Lead Scraper 🚀

This guide turns your code into a live website that you can send to anyone.

## Prerequisites (You already did these!)
- [x] **Service Account Key**: Created and installed (`backend/service_account.json`).
- [x] **Sheet Access**: You shared the Google Sheet with the bot email.
- [ ] **GitHub Repo**: You need to push your local code to a new GitHub repository.

---

## Part 1: Backend (The Brain) - Render.com
*Host the Python API for free.*

1.  Go to [Render.com](https://render.com/) and click **New +** > **Web Service**.
2.  Connect your GitHub repository.
3.  **Settings**:
    *   **Name**: `b2b-backend`
    *   **Root Directory**: `backend` (Important!)
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4.  **Environment Variables** (Scroll down):
    *   Add Key: `APIFY_API_TOKEN`
        *   Value: (Your Apify Token from `.env`)
    *   Add Key: `GOOGLE_CREDENTIALS`
        *   Value: (Open `backend/service_account.json` on your computer, copy the *entire text*, and paste it here).
5.  Click **Create Web Service**.
6.  **Copy the URL** it gives you (e.g., `https://b2b-backend.onrender.com`). You need this for Part 2.

> **Note**: It will take a few minutes to build. If it says "Live", it's ready.

---

## Part 2: Frontend (The Face) - Vercel.com
*Host the Dashboard Website for free.*

1.  Go to [Vercel.com](https://vercel.com/) and click **Add New...** > **Project**.
2.  Import the same GitHub repository.
3.  **Project Settings**:
    *   **Framework Preset**: Next.js (Should auto-detect).
    *   **Root Directory**: Click "Edit" and select `frontend`.
4.  **Environment Variables**:
    *   Name: `NEXT_PUBLIC_API_URL`
    *   Value: (Paste the Render Backend URL from Part 1, e.g., `https://b2b-backend.onrender.com`)
        *   *Important: Do not add a trailing slash `/` at the end.*
5.  Click **Deploy**.

---

## Part 3: Using It
1.  Vercel will give you a domain (e.g., `b2b-scraper.vercel.app`).
2.  Open it in your browser.
3.  Type **"Plumbers"** and **"Austin, TX"**.
4.  Click **FIND LEADS**.
5.  Check your "LA Party Venues" (or newly named) Google Sheet for results!
