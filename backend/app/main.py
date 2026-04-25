import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import User, Search, Lead, Proposal, Campaign, Template, CaseStudy
from .auth import hash_password, verify_password, create_token, decode_token
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    SearchRequest, BulkSearchRequest, NicheScanRequest, SerpRequest,
    PitchRequest, PipelineUpdateRequest, ProposalCreateRequest,
    CampaignCreateRequest, TemplateCreateRequest, CaseStudyCreateRequest,
    CompetitorCompareRequest, NapAuditRequest, BacklinkRequest,
    RankTrackRequest, RoiCalculatorRequest, WebsiteGenerateRequest,
)
from .lead_generator import (
    generate_leads, generate_niche_scan, generate_serp_results,
    generate_competitor_compare, generate_nap_audit, generate_backlinks,
    generate_website,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FreelanceLeads API", version="1.0.0")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Health ──
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "freelanceleads"}


# ── Auth ──
@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "plan": user.plan},
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "plan": user.plan},
    }


@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "email": user.email, "full_name": user.full_name,
        "plan": user.plan, "searches_used": user.searches_used,
        "searches_limit": user.searches_limit, "saved_leads_count": user.saved_leads_count,
        "pitches_sent": user.pitches_sent,
    }


# ── Dashboard ──
@app.get("/api/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recent_searches = db.query(Search).filter(Search.user_id == user.id).order_by(Search.created_at.desc()).limit(5).all()
    saved_leads = db.query(Lead).filter(Lead.user_id == user.id, Lead.saved == True).count()
    return {
        "searches_used": user.searches_used,
        "searches_limit": user.searches_limit,
        "saved_leads": saved_leads,
        "pitches_sent": user.pitches_sent,
        "plan": user.plan,
        "recent_searches": [
            {"id": s.id, "niche": s.niche, "location": s.location, "result_count": s.result_count, "created_at": s.created_at.isoformat()}
            for s in recent_searches
        ],
    }


# ── Lead Search ──
@app.post("/api/search")
def search_leads(req: SearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.searches_used >= user.searches_limit:
        raise HTTPException(status_code=403, detail="Search limit reached. Upgrade your plan.")

    leads = generate_leads(req.niche, req.location, count=40)

    search = Search(user_id=user.id, niche=req.niche, location=req.location, result_count=len(leads))
    db.add(search)
    user.searches_used += 1
    db.commit()
    db.refresh(search)

    db_leads = []
    for ld in leads:
        lead = Lead(
            user_id=user.id, search_id=search.id,
            business_name=ld["business_name"], address=ld["address"],
            city=ld["city"], state=ld["state"], phone=ld["phone"],
            website=ld["website"], rating=ld["rating"],
            review_count=ld["review_count"], opportunity_score=ld["opportunity_score"],
            has_website=ld["has_website"], has_ssl=ld["has_ssl"],
            page_speed=ld["page_speed"], needs=ld["needs"],
            pitch_suggestion=ld["pitch_suggestion"],
            niche=req.niche, location=req.location,
        )
        db.add(lead)
        db_leads.append(lead)
    db.commit()
    for lead in db_leads:
        db.refresh(lead)

    return {
        "search_id": search.id,
        "niche": req.niche,
        "location": req.location,
        "total": len(leads),
        "hot_leads": sum(1 for l in leads if l["opportunity_score"] >= 70),
        "no_website": sum(1 for l in leads if not l["has_website"]),
        "weak_seo": sum(1 for l in leads if any(n["key"] == "weak_seo" for n in l["needs"])),
        "few_reviews": sum(1 for l in leads if any(n["key"] == "few_reviews" for n in l["needs"])),
        "low_rating": sum(1 for l in leads if any(n["key"] == "low_rating" for n in l["needs"])),
        "has_phone": sum(1 for l in leads if l["phone"]),
        "results": [
            {**ld, "id": db_leads[i].id, "saved": False}
            for i, ld in enumerate(leads)
        ],
    }


@app.get("/api/search/{search_id}")
def get_search_results(search_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    search = db.query(Search).filter(Search.id == search_id, Search.user_id == user.id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    leads = db.query(Lead).filter(Lead.search_id == search_id).all()
    return {
        "search_id": search.id, "niche": search.niche, "location": search.location,
        "total": len(leads),
        "results": [
            {
                "id": l.id, "business_name": l.business_name, "address": l.address,
                "city": l.city, "state": l.state, "phone": l.phone,
                "website": l.website, "rating": l.rating, "review_count": l.review_count,
                "opportunity_score": l.opportunity_score, "has_website": l.has_website,
                "needs": l.needs, "pitch_suggestion": l.pitch_suggestion, "saved": l.saved,
                "pipeline_stage": l.pipeline_stage,
            }
            for l in leads
        ],
    }


# ── Bulk Search ──
@app.post("/api/bulk-search")
def bulk_search(req: BulkSearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.searches_used + len(req.cities) > user.searches_limit:
        raise HTTPException(status_code=403, detail="Not enough searches remaining.")
    all_results = []
    for city in req.cities[:10]:
        leads = generate_leads(req.niche, city, count=20)
        all_results.extend(leads)
        search = Search(user_id=user.id, niche=req.niche, location=city, result_count=len(leads))
        db.add(search)
        user.searches_used += 1
    db.commit()
    all_results.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return {"niche": req.niche, "cities": req.cities, "total": len(all_results), "results": all_results}


# ── Niche Scanner ──
@app.post("/api/niche-scan")
def niche_scan(req: NicheScanRequest, user: User = Depends(get_current_user)):
    results = generate_niche_scan(req.niches, req.cities)
    return {"results": results, "service_type": req.service_type}


# ── SERP Analyzer ──
@app.post("/api/serp")
def serp_analyze(req: SerpRequest, user: User = Depends(get_current_user)):
    return generate_serp_results(req.query)


# ── Competitor Compare ──
@app.post("/api/competitor-compare")
def competitor_compare(req: CompetitorCompareRequest, user: User = Depends(get_current_user)):
    return generate_competitor_compare(req.url1, req.url2)


# ── NAP Audit ──
@app.post("/api/nap-audit")
def nap_audit(req: NapAuditRequest, user: User = Depends(get_current_user)):
    return generate_nap_audit(req.business_name)


# ── Backlinks ──
@app.post("/api/backlinks")
def backlinks(req: BacklinkRequest, user: User = Depends(get_current_user)):
    return generate_backlinks(req.domain)


# ── AI Pitch Generator ──
@app.post("/api/pitch")
def generate_pitch(req: PitchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == req.lead_id, Lead.user_id == user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    needs_list = lead.needs if isinstance(lead.needs, list) else []
    need_descriptions = [n.get("label", "") for n in needs_list if isinstance(n, dict)]

    subject = f"Quick question about {lead.business_name}'s online presence"
    body = f"""Hi there,

I came across {lead.business_name} while researching {lead.niche} businesses in {lead.city}, {lead.state}, and I noticed a few things about your online presence that could be costing you customers.

"""
    if not lead.has_website:
        body += f"""Right now, {lead.business_name} doesn't have a website. That means when potential customers search for "{lead.niche} near me" or "{lead.niche} in {lead.city}", they can't find you online — even if you're the best in town.

I build professional websites for {lead.niche} businesses that are designed to rank on Google and convert visitors into calls. I actually put together a quick demo of what your site could look like.

"""
    else:
        issues = []
        for need in needs_list:
            if isinstance(need, dict):
                key = need.get("key", "")
                if key == "slow_site":
                    issues.append(f"your website takes {lead.page_speed} seconds to load (over 53% of visitors leave after 3 seconds)")
                elif key == "no_ssl":
                    issues.append("your site doesn't have an SSL certificate, so Chrome shows a 'Not Secure' warning to visitors")
                elif key == "weak_seo":
                    issues.append("there are several SEO issues (missing meta descriptions, heading tags) making it harder to rank on Google")
                elif key == "no_schema":
                    issues.append("there's no schema markup, which means you're missing out on rich snippets in search results")
        if issues:
            body += "Specifically, I noticed:\n"
            for issue in issues[:3]:
                body += f"  • {issue}\n"
            body += "\n"

    if lead.review_count is not None and lead.review_count < 10:
        body += f"I also noticed you only have {lead.review_count} Google reviews. I have a simple strategy that helps businesses like yours get 5-10 new reviews per month without being pushy.\n\n"

    body += f"""I help {lead.niche} businesses in {lead.city} get more customers through better online presence. Would you be open to a quick 10-minute call this week to discuss how I could help {lead.business_name} stand out?

No pressure at all — happy to share a few free tips either way.

Best regards"""

    user.pitches_sent += 1
    db.commit()

    return {"subject": subject, "body": body, "lead_id": lead.id, "tone": req.tone}


# ── Pipeline / CRM ──
@app.post("/api/leads/{lead_id}/save")
def save_lead(lead_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.saved = True
    user.saved_leads_count += 1
    db.commit()
    return {"saved": True, "id": lead_id}


@app.delete("/api/leads/{lead_id}/save")
def unsave_lead(lead_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.saved = False
    user.saved_leads_count = max(0, user.saved_leads_count - 1)
    db.commit()
    return {"saved": False, "id": lead_id}


@app.put("/api/leads/{lead_id}/stage")
def update_stage(lead_id: int, req: PipelineUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.pipeline_stage = req.stage
    db.commit()
    return {"id": lead_id, "stage": req.stage}


@app.get("/api/pipeline")
def get_pipeline(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    leads = db.query(Lead).filter(Lead.user_id == user.id, Lead.saved == True).all()
    stages = {"new": [], "contacted": [], "replied": [], "proposal": [], "closed": []}
    for lead in leads:
        stage = lead.pipeline_stage or "new"
        if stage in stages:
            stages[stage].append({
                "id": lead.id, "business_name": lead.business_name,
                "city": lead.city, "state": lead.state,
                "opportunity_score": lead.opportunity_score,
                "phone": lead.phone, "website": lead.website,
                "niche": lead.niche, "rating": lead.rating,
                "review_count": lead.review_count,
            })
    return {"stages": stages, "total": len(leads)}


# ── Proposals ──
@app.post("/api/proposals")
def create_proposal(req: ProposalCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = f"""# Proposal for {req.client_name}

## Executive Summary
We propose a comprehensive digital presence overhaul for {req.client_name} to increase online visibility, drive more qualified leads, and establish a dominant local presence.

## Services Included

### 1. Website Design & Development
- Modern, mobile-responsive website
- SEO-optimized page structure
- Fast loading speeds (under 3 seconds)
- SSL certificate installation
- Contact forms and click-to-call buttons

### 2. Local SEO Optimization
- Google Business Profile optimization
- NAP citation building across 46+ directories
- Local keyword targeting
- Schema markup implementation
- Monthly rank tracking reports

### 3. Review Management Strategy
- Automated review request system
- Review response templates
- Reputation monitoring

## Investment
- **Setup fee**: $1,500 (one-time)
- **Monthly retainer**: $500/month
- **Contract term**: 6 months minimum

## Expected Results
- 50-100% increase in organic traffic within 6 months
- 20+ new Google reviews in first 3 months
- Top 3 local pack ranking for primary keywords
"""
    proposal = Proposal(
        user_id=user.id, lead_id=req.lead_id,
        title=req.title, client_name=req.client_name, content=content,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return {"id": proposal.id, "title": proposal.title, "content": content, "status": proposal.status}


@app.get("/api/proposals")
def list_proposals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    proposals = db.query(Proposal).filter(Proposal.user_id == user.id).order_by(Proposal.created_at.desc()).all()
    return [
        {"id": p.id, "title": p.title, "client_name": p.client_name, "status": p.status, "created_at": p.created_at.isoformat()}
        for p in proposals
    ]


# ── Campaigns ──
@app.post("/api/campaigns")
def create_campaign(req: CampaignCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = Campaign(user_id=user.id, name=req.name)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {"id": campaign.id, "name": campaign.name, "status": campaign.status}


@app.get("/api/campaigns")
def list_campaigns(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).filter(Campaign.user_id == user.id).order_by(Campaign.created_at.desc()).all()
    return [
        {"id": c.id, "name": c.name, "status": c.status, "total_leads": c.total_leads,
         "emails_sent": c.emails_sent, "replies": c.replies, "created_at": c.created_at.isoformat()}
        for c in campaigns
    ]


# ── Templates ──
@app.post("/api/templates")
def create_template(req: TemplateCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = Template(user_id=user.id, name=req.name, subject=req.subject, body=req.body, category=req.category)
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "name": template.name, "category": template.category}


@app.get("/api/templates")
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    templates = db.query(Template).filter(Template.user_id == user.id).order_by(Template.created_at.desc()).all()
    return [
        {"id": t.id, "name": t.name, "subject": t.subject, "body": t.body, "category": t.category, "created_at": t.created_at.isoformat()}
        for t in templates
    ]


# ── Case Studies ──
@app.post("/api/case-studies")
def create_case_study(req: CaseStudyCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cs = CaseStudy(
        user_id=user.id, title=req.title, client_name=req.client_name,
        description=req.description, before_metrics=req.before_metrics, after_metrics=req.after_metrics,
    )
    db.add(cs)
    db.commit()
    db.refresh(cs)
    return {"id": cs.id, "title": cs.title, "client_name": cs.client_name}


@app.get("/api/case-studies")
def list_case_studies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    studies = db.query(CaseStudy).filter(CaseStudy.user_id == user.id).order_by(CaseStudy.created_at.desc()).all()
    return [
        {"id": s.id, "title": s.title, "client_name": s.client_name, "published": s.published,
         "before_metrics": s.before_metrics, "after_metrics": s.after_metrics, "created_at": s.created_at.isoformat()}
        for s in studies
    ]


# ── ROI Calculator ──
@app.post("/api/roi-calculate")
def roi_calculate(req: RoiCalculatorRequest, user: User = Depends(get_current_user)):
    additional_traffic = int(req.current_traffic * req.projected_traffic_increase / 100)
    new_total_traffic = req.current_traffic + additional_traffic
    additional_leads = int(additional_traffic * req.conversion_rate / 100)
    avg_customer_value = req.monthly_revenue / max(req.current_traffic * req.conversion_rate / 100, 1)
    additional_revenue = additional_leads * avg_customer_value
    return {
        "current_traffic": req.current_traffic,
        "additional_traffic": additional_traffic,
        "new_total_traffic": new_total_traffic,
        "conversion_rate": req.conversion_rate,
        "additional_leads_per_month": additional_leads,
        "avg_customer_value": round(avg_customer_value, 2),
        "additional_monthly_revenue": round(additional_revenue, 2),
        "additional_annual_revenue": round(additional_revenue * 12, 2),
    }


# ── AI Website Generator ──
@app.post("/api/generate-website")
def gen_website(req: WebsiteGenerateRequest, user: User = Depends(get_current_user)):
    return generate_website(req.business_name, req.niche, req.location, req.phone, req.description)


# ── Rank Tracking (mock) ──
@app.post("/api/rank-tracking")
def rank_tracking(req: RankTrackRequest, user: User = Depends(get_current_user)):
    import random, hashlib
    results = []
    for kw in req.keywords:
        rng = random.Random(hashlib.md5(f"{req.domain}:{kw}".encode()).hexdigest())
        current_rank = rng.randint(1, 50)
        history = [max(1, current_rank + rng.randint(-5, 5)) for _ in range(14)]
        results.append({
            "keyword": kw,
            "current_rank": current_rank,
            "previous_rank": history[-2] if len(history) > 1 else current_rank,
            "best_rank": min(history),
            "history": history,
            "url": f"https://{req.domain}",
            "search_volume": rng.randint(100, 10000),
        })
    return {"domain": req.domain, "location": req.location, "keywords": results}


# ── Link Health (mock) ──
@app.post("/api/link-health")
def link_health(req: BacklinkRequest, user: User = Depends(get_current_user)):
    import random, hashlib
    rng = random.Random(hashlib.md5(req.domain.encode()).hexdigest())
    anchors = {}
    for _ in range(10):
        anchor = rng.choice(["brand name", "click here", "visit site", req.domain, "learn more", "website", "homepage", "best service", "view details", "get quote"])
        anchors[anchor] = anchors.get(anchor, 0) + rng.randint(1, 50)
    monthly_links = [rng.randint(2, 30) for _ in range(12)]
    return {
        "domain": req.domain,
        "total_backlinks": sum(monthly_links),
        "anchor_distribution": anchors,
        "monthly_new_links": monthly_links,
        "velocity_alert": max(monthly_links) > 25,
        "toxic_score": rng.randint(0, 30),
    }
