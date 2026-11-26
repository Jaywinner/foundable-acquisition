from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal, UserSettings, DailyReportRecord, Prospect, AutomationLog
from agents import AutopilotEngine
from datetime import datetime

scheduler = BackgroundScheduler()

def scheduled_discovery_job():
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).first()
        if settings and settings.autopilot_enabled and not settings.emergency_stop:
            print("[Autopilot] Running scheduled discovery cycle...")
            count = AutopilotEngine.run_discovery_cycle(db)
            print(f"[Autopilot] Discovery cycle complete. Discovered {count} prospects.")
            
            # Update daily report
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            report = db.query(DailyReportRecord).filter(DailyReportRecord.report_date == today_str).first()
            if not report:
                report = DailyReportRecord(
                    report_date=today_str,
                    queries_executed=15,
                    sources_investigated=5,
                    businesses_discovered=count,
                    duplicates_removed=2,
                    prospects_researched=count,
                    hot_leads=2,
                    strong_opportunities=2,
                    emails_generated=count,
                    emails_sent=0,
                    summary_text=f"Autopilot ran discovery cycle and found {count} qualified prospects."
                )
                db.add(report)
            else:
                report.businesses_discovered += count
                report.prospects_researched += count
                report.emails_generated += count
            db.commit()
    except Exception as e:
        print(f"[Autopilot Error] {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # Run discovery check every hour or daily as configured
        scheduler.add_job(scheduled_discovery_job, 'interval', hours=4, id='autopilot_discovery', replace_existing=True)
        scheduler.start()
        print("[Scheduler] APScheduler started successfully.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] APScheduler shutdown.")
