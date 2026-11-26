# Foundable Acquisition
## Autonomous Client Discovery, Research, Personalised Outreach & Email Automation Platform for Foundable By Jay

Foundable Acquisition is an intelligent client-acquisition automation system designed to autonomously perform the complete prospecting workflow:
**Find prospects → Investigate them → Verify their needs → Score them → Research their business → Identify opportunities → Craft a personalised message → Send the message → Track results → Follow up intelligently → Repeat daily.**

---

## 🚀 Live Production Deployment & Gmail Integration

### 1. Push to GitHub
1. Create a new repository on GitHub named `foundable-acquisition`.
2. Run the following commands in your local project directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Foundable Acquisition"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/foundable-acquisition.git
   git push -u origin main
   ```

### 2. Deploy Live (Render / Railway / Fly.io / Heroku)
- Connect your GitHub repository to **Render.com** (or Railway).
- Render will automatically detect `render.yaml` or `Dockerfile`.
- Set build command: `pip install -r backend/requirements.txt`
- Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### 3. Connect Live Gmail OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Gmail API**.
3. Create **OAuth 2.0 Credentials** (Web Application).
4. Add your live app redirect URI (e.g., `https://your-app.onrender.com/api/auth/gmail/callback`).
5. Set `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in your live cloud deployment environment variables.
6. In the app's **Settings & Setup** tab, click **Connect Gmail Account** to authorize live email sending through your business inbox (`Foundable By Jay`).

---

## 🛠️ Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL, APScheduler.
- **Frontend**: React, Tailwind CSS, Modern Mobile-First PWA UI.
- **Brand Palette**: Deep Navy (`#1F3446`), Warm Gold (`#E1A94B`), Cream (`#F6F3E9`), Teal (`#6FA9B8`), Charcoal (`#2B2B2B`).
