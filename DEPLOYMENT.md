# Render Deployment Instructions

To deploy the **AeroSafe AI** project to Render (FastAPI backend + PostgreSQL Database), follow this step-by-step guide:

## Step 1: Create a PostgreSQL Database on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **PostgreSQL**.
3. Fill in the configuration:
   * **Name**: `aerosafe-db`
   * **Database**: `aerosafe_db`
   * **User**: `postgres`
4. Click **Create Database**.
5. Once active, copy the **Internal Database URL** (e.g., `postgresql://postgres:...`).

---

## Step 2: Deploy the Web Service on Render
1. From the Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub repository: `saranyaraman8469-cmyk/AeroSafe-AI-Aviation-Safety-Analytics-and-Risk-Prediction`.
3. Configure the settings:
   * **Name**: `aerosafe-api`
   * **Language**: `Python 3`
   * **Branch**: `main`
   * **Build Command**: `pip install -r requirements.txt && python pipeline/ingest.py && python pipeline/model.py`
   * **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
4. Expand the **Advanced** section to add **Environment Variables**:
   * Add `DATABASE_URL` ──► Paste the **Internal Database URL** copied in Step 1.
   * Add `GEMINI_API_KEY` ──► Your Google Gemini API Key (optional, for safety advisory explanations).
5. Click **Deploy Web Service**.

Render will automatically pull the code from GitHub, initialize/seed the database, train the Random Forest model, and spin up the web dashboard.
