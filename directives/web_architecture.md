# Architecture: Professional Event Lead Dashboard (Web App)

To professionalize the "Venue Finder" and "Lead Gen" tools so a friend can use them over the internet, we need to migrate from a local script to a hosted Web Application.

## The Stack (The "Pro" Setup)

We will use a modern, scalable stack that separates the **User Interface (Frontend)** from the **Logic (Backend)**.

### 1. Backend (The Brain) - Python & FastAPI
*   **Role**: wrapping your existing Python scripts (`find_venues.py`, `scrape_google_maps.py`) into HTTP API endpoints.
*   **Why**: Your code is already in Python. FastAPI is the modern standard for Python APIs.
*   **Endpoints**:
    *   `POST /api/leads/search`: Triggers the Google Maps scraper.
    *   `POST /api/venues/search`: Triggers the Venue Finder.
    *   `GET /api/jobs/{id}/status`: Checks if the scraping is done.
*   **Authentication Update (CRITICAL)**:
    *   **Current State**: Your script opens a browser on your Mac to log into Google Sheets. This won't work on a server.
    *   **Required Change**: Switch to a **Google Service Account**.
        *   This uses a `.json` key file on the server.
        *   **Usage**: Your friend creates a Google Sheet and *shares* it with the Service Account email (e.g., `bot@app.iam.gserviceaccount.com`) to allow the bot to write to it.

### 2. Frontend (The Face) - Next.js & Tailwind CSS
*   **Role**: A beautiful, dark-mode dashboard where your friend inputs their search criteria.
*   **Why**: Next.js (React) allows for a "Premium" feel with instant feedback, nice forms, and loading states.
*   **Features**:
    *   **Dashboard Home**: Select "Find Leads" or "Find Venues".
    *   **Input Form**: Neat inputs for "Keyword", "Location", "Radius".
    *   **Live Status**: A terminal-like log window showing the bot's progress.
    *   **Result Link**: Shows the Google Sheet URL when done.

### 3. Hosting (The Internet)
*   **Frontend**: Deployed on **Vercel** (Free/Cheap, very fast).
*   **Backend**: Deployed on **Render** or **Railway** (Great for Python/Docker apps).
*   **Apify**: Continues to run in the cloud via API.

---

## Alternative: The Fast Track (Streamlit)
If you want something up and running in **24 hours** rather than a full SaaS build:
*   **Streamlit**: A Python library that turns scripts into web apps automatically.
*   **Pros**: No HTML/CSS/JS knowledge needed. Single file (`app.py`).
*   **Cons**: Looks less custom, strictly "Internal Tool" vibes.

## Roadmap to Build
1.  **Refactor Auth**: Implement `ServiceAccount` logic for Sheets.
2.  **API Layer**: Create `server.py` with FastAPI.
3.  **Frontend MVP**: Build the basic input form in Next.js.
4.  **Connect**: Hook them up and deploy.
