from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./foundable_autopilot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    business_name = Column(String, default="Foundable By Jay")
    services = Column(JSON, default=[
        "Professional business website design and development",
        "Mobile-friendly website redesigns",
        "Website development for businesses with no website",
        "Website repairs, improvements, and modernisation",
        "WordPress, Wix, Shopify, Webflow, Squarespace development",
        "E-commerce website development",
        "Google Business Profile creation, optimisation, and management"
    ])
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True, index=True)
    autopilot_enabled = Column(Boolean, default=False)
    research_enabled = Column(Boolean, default=True)
    email_sending_enabled = Column(Boolean, default=False)
    followup_enabled = Column(Boolean, default=True)
    inbox_monitoring_enabled = Column(Boolean, default=True)
    emergency_stop = Column(Boolean, default=False)
    
    daily_research_budget = Column(Integer, default=30)
    daily_email_limit = Column(Integer, default=5)
    max_new_contacts_per_day = Column(Integer, default=10)
    max_followups_per_day = Column(Integer, default=10)
    min_lead_score = Column(Integer, default=70)
    min_source_confidence = Column(Float, default=0.8)
    
    target_countries = Column(JSON, default={"US": 60, "UK": 20, "Canada": 15, "Other": 5})
    target_industries = Column(JSON, default=[
        "Cleaning companies", "Landscaping businesses", "Contractors", "Roofing companies",
        "Plumbing companies", "Electricians", "HVAC companies", "Auto repair shops",
        "Restaurants", "Bakeries", "Cafés", "Fitness studios", "Local retailers", "Photographers"
    ])
    excluded_industries = Column(JSON, default=[])
    
    timezone = Column(String, default="Africa/Lagos")
    email_approval_mode = Column(String, default="semi-automatic") # manual, semi-automatic, autopilot
    followup_timing_days = Column(Integer, default=4)
    second_followup_days = Column(Integer, default=7)
    max_followups = Column(Integer, default=2)
    ai_model = Column(String, default="gpt-4o")
    monthly_ai_budget_usd = Column(Float, default=50.0)
    monthly_email_budget = Column(Integer, default=500)
    current_month_spend_usd = Column(Float, default=2.45)

class Prospect(Base):
    __tablename__ = "prospects"
    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, index=True)
    contact_name = Column(String, nullable=True)
    business_category = Column(String, index=True)
    country = Column(String, index=True)
    city = Column(String, index=True)
    business_website = Column(String, nullable=True)
    website_status = Column(String, default="active") # active, broken, no_website, expired
    gbp_url = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_method = Column(String, default="email")
    verification_status = Column(String, default="verified") # verified, unverified, manual_check
    
    original_source = Column(String)
    source_url = Column(String)
    source_date = Column(DateTime, default=datetime.utcnow)
    discovery_date = Column(DateTime, default=datetime.utcnow)
    
    intent_category = Column(String, default="active_demand") # active_demand, website_problem, growth_signal, gbp_opportunity
    lead_score = Column(Integer, default=75)
    lead_classification = Column(String, default="B") # HOT, B, C, D, E
    
    research_report = Column(Text, nullable=True)
    verified_facts = Column(JSON, default=[])
    opportunity_analysis = Column(Text, nullable=True)
    recommended_service = Column(String, nullable=True)
    
    email_subject = Column(String, nullable=True)
    email_draft = Column(Text, nullable=True)
    email_status = Column(String, default="draft") # draft, pending_approval, approved, sent, rejected, replied
    last_contact_date = Column(DateTime, nullable=True)
    reply_status = Column(String, default="none") # none, interested, pricing, meeting, not_interested, out_of_office, unsubscribe
    followup_status = Column(String, default="scheduled") # scheduled, sent_1, sent_2, completed, cancelled
    opt_out = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=[])

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="queued") # queued, sent, failed, delivered
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    message_type = Column(String, default="initial") # initial, followup_1, followup_2

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, unique=True, index=True) # e.g. "gmail"
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    is_connected = Column(Boolean, default=False)
    account_email = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

class SuppressionEntry(Base):
    __tablename__ = "suppression_list"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    domain = Column(String, index=True, nullable=True)
    reason = Column(String)
    added_at = Column(DateTime, default=datetime.utcnow)

class SearchQueryRecord(Base):
    __tablename__ = "search_queries"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String)
    source = Column(String)
    results_found = Column(Integer, default=0)
    qualified_leads_produced = Column(Integer, default=0)
    executed_at = Column(DateTime, default=datetime.utcnow)

class AutomationLog(Base):
    __tablename__ = "automation_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String)
    status = Column(String) # success, warning, error
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DailyReportRecord(Base):
    __tablename__ = "daily_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(String, unique=True)
    queries_executed = Column(Integer, default=0)
    sources_investigated = Column(Integer, default=0)
    businesses_discovered = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    prospects_researched = Column(Integer, default=0)
    hot_leads = Column(Integer, default=0)
    strong_opportunities = Column(Integer, default=0)
    emails_generated = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)
    interested_replies = Column(Integer, default=0)
    meetings_booked = Column(Integer, default=0)
    summary_text = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
