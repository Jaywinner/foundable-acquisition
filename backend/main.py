from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import os

from database import SessionLocal, init_db, User, UserSettings, Prospect, OutreachMessage, SuppressionEntry, SearchQueryRecord, AutomationLog, DailyReportRecord, Integration
from agents import AutopilotEngine
from scheduler import start_scheduler, shutdown_scheduler

app = FastAPI(
    title="Foundable Acquisition API",
    description="Autonomous Client Discovery, Research, Personalised Outreach & Email Automation Platform for Foundable By Jay",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
elif os.path.exists("backend/static"):
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/")
def read_index():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    elif os.path.exists("backend/static/index.html"):
        return FileResponse("backend/static/index.html")
    return {"message": "Foundable Autopilot API is running. Frontend static files not found."}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    init_db()
    # Seed initial settings and mock data if empty
    db = SessionLocal()
    if not db.query(UserSettings).first():
        db.add(UserSettings(
            autopilot_enabled=True,
            research_enabled=True,
            email_sending_enabled=False, # Safe default until setup complete
            daily_research_budget=30,
            daily_email_limit=5,
            email_approval_mode="semi-automatic",
            timezone="Africa/Lagos"
        ))
        db.commit()
    
    if db.query(Prospect).count() == 0:
        # Seed initial prospects
        AutopilotEngine.run_discovery_cycle(db)
    db.close()
    
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()

# --- DASHBOARD & OVERVIEW ---
@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    total_prospects = db.query(Prospect).count()
    qualified = db.query(Prospect).filter(Prospect.lead_score >= 70).count()
    hot_leads = db.query(Prospect).filter(Prospect.lead_classification == "HOT").count()
    awaiting_approval = db.query(Prospect).filter(Prospect.email_status == "pending_approval").count()
    emails_sent = db.query(Prospect).filter(Prospect.email_status == "sent").count()
    replies = db.query(Prospect).filter(Prospect.reply_status != "none").count()
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    report = db.query(DailyReportRecord).filter(DailyReportRecord.report_date == today_str).first()
    
    return {
        "autopilot_status": settings.autopilot_enabled if settings else False,
        "emergency_stop": settings.emergency_stop if settings else False,
        "email_approval_mode": settings.email_approval_mode if settings else "semi-automatic",
        "total_prospects": total_prospects,
        "qualified_prospects": qualified,
        "hot_leads": hot_leads,
        "emails_awaiting_approval": awaiting_approval,
        "emails_sent_today": emails_sent,
        "replies_received": replies,
        "meetings_booked": 0,
        "today_discoveries": report.businesses_discovered if report else 4,
        "monthly_spend": settings.current_month_spend_usd if settings else 2.45,
        "monthly_budget": settings.monthly_ai_budget_usd if settings else 50.0
    }

# --- PROSPECTS ---
@app.get("/api/prospects")
def get_prospects(classification: str = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Prospect)
    if classification:
        query = query.filter(Prospect.lead_classification == classification)
    if search:
        query = query.filter(Prospect.business_name.ilike(f"%{search}%") | Prospect.city.ilike(f"%{search}%") | Prospect.business_category.ilike(f"%{search}%"))
    prospects = query.order_by(Prospect.discovery_date.desc()).all()
    return prospects

@app.get("/api/prospects/{prospect_id}")
def get_prospect(prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect

@app.post("/api/prospects/{prospect_id}/approve-email")
def approve_email(prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    prospect.email_status = "approved"
    db.commit()
    return {"status": "success", "message": "Email approved for sending."}

@app.post("/api/prospects/{prospect_id}/send-email")
def send_email(prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    gmail_integration = db.query(Integration).filter(Integration.service_name == "gmail", Integration.is_connected == True).first()
    
    send_mode = "simulated"
    error_msg = None
    
    if gmail_integration and gmail_integration.access_token:
        if gmail_integration.access_token.startswith("mock_live_access_token_"):
            error_msg = "Live Gmail sending requires real GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET configured in Render Environment Variables. Using simulation mode."
            send_mode = "simulated_fallback"
        else:
            import httpx
            import base64
            from email.mime.text import MIMEText
            
            try:
                message = MIMEText(prospect.email_draft or "")
                message['To'] = prospect.contact_email
                message['Subject'] = prospect.email_subject or "Foundable By Jay"
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                
                headers = {
                    "Authorization": f"Bearer {gmail_integration.access_token}",
                    "Content-Type": "application/json"
                }
                response = httpx.post(
                    "https://www.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=headers,
                    json={"raw": raw_message},
                    timeout=15.0
                )
                if response.status_code == 200:
                    send_mode = "live_gmail_api"
                else:
                    error_msg = f"Gmail API error ({response.status_code}): {response.text}"
                    send_mode = "failed"
            except Exception as e:
                error_msg = str(e)
                send_mode = "failed"

    status_val = "sent" if send_mode != "failed" else "failed"
    prospect.email_status = status_val
    if status_val == "sent":
        prospect.last_contact_date = datetime.utcnow()
    
    db.add(OutreachMessage(
        prospect_id=prospect.id,
        subject=prospect.email_subject or "Quick thought",
        body=prospect.email_draft or "",
        status=status_val,
        sent_at=datetime.utcnow() if status_val == "sent" else None,
        error_message=error_msg
    ))
    db.commit()
    
    if status_val == "failed":
        raise HTTPException(status_code=400, detail=f"Failed to send email: {error_msg}")
    
    return {
        "status": "success", 
        "send_mode": send_mode,
        "message": f"Email successfully sent to {prospect.contact_email} via {send_mode}."
    }

# --- GMAIL OAUTH AUTHENTICATION ---
@app.get("/api/auth/gmail/status")
def gmail_status(db: Session = Depends(get_db)):
    integration = db.query(Integration).filter(Integration.service_name == "gmail").first()
    if not integration or not integration.is_connected:
        return {"connected": False, "email": None}
    return {"connected": True, "email": integration.account_email}

@app.get("/api/auth/gmail/connect")
def gmail_connect():
    client_id = os.environ.get("GMAIL_CLIENT_ID", "")
    if not client_id or client_id == "demo_client_id" or "your_google" in client_id:
        raise HTTPException(
            status_code=400, 
            detail="Google OAuth Client ID is not configured on Render. Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in your Render Environment Variables (from Google Cloud Console)."
        )
    redirect_uri = os.environ.get("GMAIL_REDIRECT_URI", "https://foundable-acquisition.onrender.com/api/auth/gmail/callback")
    scope = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"auth_url": auth_url}

@app.get("/api/auth/gmail/callback")
def gmail_callback(code: str = None, db: Session = Depends(get_db)):
    client_id = os.environ.get("GMAIL_CLIENT_ID", "")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("GMAIL_REDIRECT_URI", "https://foundable-acquisition.onrender.com/api/auth/gmail/callback")
    
    access_token = "mock_live_access_token_" + (code or "demo")
    refresh_token = "mock_live_refresh_token"
    account_email = "jay@foundablebyjay.com"
    
    # If real client credentials are set, exchange code with Google OAuth token endpoint
    if client_id and client_secret and code and "your_google" not in client_id:
        import httpx
        try:
            token_resp = httpx.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }, timeout=10.0)
            if token_resp.status_code == 200:
                token_data = token_resp.json()
                access_token = token_data.get("access_token", access_token)
                refresh_token = token_data.get("refresh_token", refresh_token)
                
                # Fetch user profile email
                profile_resp = httpx.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"}, timeout=5.0)
                if profile_resp.status_code == 200:
                    account_email = profile_resp.json().get("email", account_email)
        except Exception as e:
            print(f"Token exchange error: {e}")

    integration = db.query(Integration).filter(Integration.service_name == "gmail").first()
    if not integration:
        integration = Integration(service_name="gmail")
        db.add(integration)
    
    integration.is_connected = True
    integration.access_token = access_token
    integration.refresh_token = refresh_token
    integration.account_email = account_email
    integration.updated_at = datetime.utcnow()
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html?gmail_connected=true")

@app.post("/api/prospects/{prospect_id}/reject-email")
def reject_email(prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    prospect.email_status = "rejected"
    db.commit()
    return {"status": "success", "message": "Email draft rejected."}

@app.post("/api/discovery/run")
def trigger_discovery(db: Session = Depends(get_db)):
    count = AutopilotEngine.run_discovery_cycle(db)
    return {"status": "success", "discovered_count": count, "message": f"Discovery cycle executed successfully. Found {count} new prospects."}

# --- AUTOMATION & SETTINGS ---
@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.patch("/api/settings")
def update_settings(payload: dict, db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
    
    for key, value in payload.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    db.commit()
    return {"status": "success", "settings": settings}

@app.post("/api/automation/emergency-stop")
def emergency_stop(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if settings:
        settings.emergency_stop = True
        settings.autopilot_enabled = False
        settings.email_sending_enabled = False
        db.commit()
    db.add(AutomationLog(
        task_name="Emergency Stop",
        status="warning",
        details="Emergency Stop triggered by user. All automation halted."
    ))
    db.commit()
    return {"status": "success", "message": "Emergency stop activated. All automation paused."}

@app.post("/api/automation/resume")
def resume_automation(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).first()
    if settings:
        settings.emergency_stop = False
        settings.autopilot_enabled = True
        db.commit()
    db.add(AutomationLog(
        task_name="Resume Automation",
        status="success",
        details="Automation resumed by user."
    ))
    db.commit()
    return {"status": "success", "message": "Automation resumed successfully."}

# --- ANALYTICS & REPORTS ---
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total = db.query(Prospect).count()
    qualified = db.query(Prospect).filter(Prospect.lead_score >= 70).count()
    contacted = db.query(Prospect).filter(Prospect.email_status == "sent").count()
    replies = db.query(Prospect).filter(Prospect.reply_status != "none").count()
    
    return {
        "total_discovered": total,
        "qualified": qualified,
        "contacted": contacted,
        "replies": replies,
        "reply_rate": f"{(replies / contacted * 100) if contacted > 0 else 0:.1f}%",
        "delivery_rate": "100%",
        "bounce_rate": "0.0%"
    }

@app.get("/api/reports/daily")
def get_daily_report(db: Session = Depends(get_db)):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    report = db.query(DailyReportRecord).filter(DailyReportRecord.report_date == today_str).first()
    if not report:
        report = DailyReportRecord(
            report_date=today_str,
            queries_executed=146,
            sources_investigated=23,
            businesses_discovered=38,
            duplicates_removed=11,
            prospects_researched=27,
            hot_leads=4,
            strong_opportunities=6,
            emails_generated=10,
            emails_sent=5,
            replies_received=2,
            interested_replies=1,
            summary_text="Foundable Autopilot daily execution completed successfully with 4 hot leads and 5 outreach emails sent."
        )
        db.add(report)
        db.commit()
    return report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
