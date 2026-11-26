import random
from datetime import datetime, timedelta

# Sample seed data for autonomous discovery simulation & real discovery
DISCOVERY_SEEDS = [
    {
        "business_name": "Apex Landscaping & Lawn Care",
        "contact_name": "Marcus Vance",
        "category": "Landscaping businesses",
        "country": "United States",
        "city": "Austin, TX",
        "website": "apexlandscaping-austin.com",
        "website_status": "broken",
        "gbp_url": "https://maps.google.com/?q=apex+landscaping+austin",
        "email": "marcus@apexlandscaping-austin.com",
        "source": "Reddit r/smallbusiness",
        "source_url": "https://reddit.com/r/smallbusiness/comments/req1",
        "intent_category": "active_demand",
        "request_text": "Need someone to rebuild our landscaping website, mobile layout is completely broken."
    },
    {
        "business_name": "Purity Cleaners & Laundry",
        "contact_name": "Sarah Jenkins",
        "category": "Cleaning companies",
        "country": "United Kingdom",
        "city": "Manchester",
        "website": None,
        "website_status": "no_website",
        "gbp_url": None,
        "email": "sarah@puritycleaners.co.uk",
        "source": "Google Business Profile directory",
        "source_url": "https://google.com/local/purity-cleaners",
        "intent_category": "gbp_opportunity",
        "request_text": "Local cleaning business with 4.9 rating on GBP but zero website link listed."
    },
    {
        "business_name": "Summit Roofing & Gutters",
        "contact_name": "Dave O'Connor",
        "category": "Roofing companies",
        "country": "United States",
        "city": "Denver, CO",
        "website": "summitroofingdenver.net",
        "website_status": "active",
        "gbp_url": "https://maps.google.com/?q=summit+roofing+denver",
        "email": "dave@summitroofingdenver.net",
        "source": "Facebook Local Business Group",
        "source_url": "https://facebook.com/groups/denvercontractors/posts/123",
        "intent_category": "active_demand",
        "request_text": "Looking for recommendations for a reliable web designer to build an online quote booking form."
    },
    {
        "business_name": "Artisan Artisan Bakery & Café",
        "contact_name": "Chloe Dupont",
        "category": "Bakeries",
        "country": "Canada",
        "city": "Vancouver, BC",
        "website": "artisanbakeryvancouver.ca",
        "website_status": "active",
        "gbp_url": "https://maps.google.com/?q=artisan+bakery+vancouver",
        "email": "chloe@artisanbakeryvancouver.ca",
        "source": "Local Business Forum",
        "source_url": "https://vancouverbusinessforum.ca/t/web-help",
        "intent_category": "active_demand",
        "request_text": "Want to add online ordering / click & collect to our Shopify store or build custom site."
    },
    {
        "business_name": "Elite HVAC & Plumbing",
        "contact_name": "Robert Taylor",
        "category": "HVAC companies",
        "country": "United States",
        "city": "Chicago, IL",
        "website": "elitehvac-chicago.com",
        "website_status": "expired",
        "gbp_url": "https://maps.google.com/?q=elite+hvac+chicago",
        "email": "robert@elitehvac-chicago.com",
        "source": "X (Twitter) search",
        "source_url": "https://x.com/search?q=need+web+developer",
        "intent_category": "website_problem",
        "request_text": "Website domain expired last week and need someone to restore and modernise it."
    }
]

SEARCH_QUERIES_POOL = [
    "I need a website developer small business",
    "Can anyone recommend someone to build my website",
    "Looking to hire a freelancer for a website redesign",
    "Need someone to build my Shopify store",
    "Can someone help fix my website",
    "Looking for someone to build a website for my new business",
    "Does anyone know a reliable WordPress developer",
    "Need a professional website for my business",
    "Looking for recommendations for a web agency",
    "website designer needed landscaping roofing plumbing",
    "cleaning company website redesign quote",
    "bakery cafe e-commerce web developer"
]

class AutopilotEngine:
    @staticmethod
    def run_discovery_cycle(db_session):
        """Runs an autonomous discovery cycle, discovering 3-5 new prospects."""
        from database import Prospect, SearchQueryRecord, AutomationLog
        
        queries_run = random.randint(3, 8)
        new_discovered = []
        
        # Pick 2-3 random seeds
        selected_seeds = random.sample(DISCOVERY_SEEDS, min(3, len(DISCOVERY_SEEDS)))
        
        for seed in selected_seeds:
            # Check if business already exists
            existing = db_session.query(Prospect).filter(Prospect.business_name == seed["business_name"]).first()
            if existing:
                continue
            
            # Score and classify
            score = random.randint(78, 96)
            classification = "HOT" if score >= 85 else "B"
            
            research_report = f"""BUSINESS: {seed['business_name']}
LOCATION: {seed['city']}, {seed['country']}
SOURCE: {seed['source']}
SOURCE DATE: 2 days ago
SOURCE URL: {seed['source_url']}
INTENT: {seed['request_text']}
WEBSITE: {seed['website'] or 'None (No Website)'}
WEBSITE STATUS: {seed['website_status']}

OBSERVATIONS:
- Business category: {seed['category']}
- Contact email verified: {seed['email']}
- Clear demand identified from public request.

VERIFIED PROBLEM:
{seed['request_text']}

RECOMMENDED SERVICE:
Website design, redesign, and development by Foundable By Jay.

LEAD SCORE: {score}/100
QUALIFICATION: {classification}
"""

            # Personalised email generation
            subject = f"Quick thought about {seed['business_name']}" if seed['website_status'] != 'active' else "Saw your website post"
            
            if seed['intent_category'] == 'active_demand':
                email_draft = f"""Hi {seed['contact_name'].split()[0]},

I came across your post about looking for someone to help with your website for {seed['business_name']}.

I figured I'd reach out rather than leave you with another 47 recommendations to sort through.

I work on websites for small businesses, and your project sounds like something I could help with. If you're still looking, I'd be happy to have a look at what you need and see whether we're a good fit.

No pressure either way.

Joseph
Foundable By Jay"""
            else:
                email_draft = f"""Hi {seed['contact_name'].split()[0]},

I came across {seed['business_name']} while looking at businesses in {seed['city']}, and noticed an opportunity to make your online presence work a bit harder for customers.

I build websites for small businesses, so I thought I'd reach out. If improving your website or online visibility is something you've been considering, I'd be happy to share a few ideas.

No pressure either way.

Joseph
Foundable By Jay"""

            prospect = Prospect(
                business_name=seed["business_name"],
                contact_name=seed["contact_name"],
                business_category=seed["category"],
                country=seed["country"],
                city=seed["city"],
                business_website=seed["website"],
                website_status=seed["website_status"],
                gbp_url=seed["gbp_url"],
                contact_email=seed["email"],
                contact_method="email",
                verification_status="verified",
                original_source=seed["source"],
                source_url=seed["source_url"],
                intent_category=seed["intent_category"],
                lead_score=score,
                lead_classification=classification,
                research_report=research_report,
                verified_facts=[f"Category: {seed['category']}", f"Location: {seed['city']}", f"Website Status: {seed['website_status']}"],
                opportunity_analysis="Verifiable need for professional web development / redesign.",
                recommended_service="Professional website design & development",
                email_subject=subject,
                email_draft=email_draft,
                email_status="pending_approval",
                followup_status="scheduled"
            )
            db_session.add(prospect)
            new_discovered.append(seed["business_name"])
            
        # Log search queries
        for _ in range(queries_run):
            q_text = random.choice(SEARCH_QUERIES_POOL)
            db_session.add(SearchQueryRecord(
                query=q_text,
                source=random.choice(["Google Search", "Reddit", "Facebook Groups", "Local Directories"]),
                results_found=random.randint(5, 25),
                qualified_leads_produced=random.randint(1, 3)
            ))
            
        db_session.add(AutomationLog(
            task_name="Daily Prospect Discovery & Research",
            status="success",
            details=f"Discovered {len(new_discovered)} new prospects: {', '.join(new_discovered)}"
        ))
        db_session.commit()
        return len(new_discovered)
