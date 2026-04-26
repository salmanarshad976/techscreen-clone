"""Real API integrations for FreelanceLeads clone.

Uses free-tier APIs:
- Google Places API (Text Search) for real business data
- Google PageSpeed Insights API (free, no key required but key raises quota)
- Google Gemini API for AI pitch generation and website generation
- Google Custom Search API for SERP analysis

Falls back to mock data when API keys are not configured.
"""

import os
import httpx
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
CUSTOM_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def has_google_key() -> bool:
    return bool(GOOGLE_API_KEY)


def has_gemini_key() -> bool:
    return bool(GEMINI_API_KEY)


# ── Google Places API (Text Search) ──

async def search_places(niche: str, location: str, max_results: int = 20) -> list[dict] | None:
    if not has_google_key():
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                PLACES_TEXT_SEARCH_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": GOOGLE_API_KEY,
                    "X-Goog-FieldMask": (
                        "places.displayName,places.formattedAddress,places.rating,"
                        "places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,"
                        "places.types,places.id,places.googleMapsUri"
                    ),
                },
                json={
                    "textQuery": f"{niche} in {location}",
                    "maxResultCount": min(max_results, 20),
                    "languageCode": "en",
                },
            )
            if resp.status_code != 200:
                logger.warning("Places API error %d: %s", resp.status_code, resp.text[:200])
                return None
            data = resp.json()
            places = data.get("places", [])
            return [_parse_place(p, niche, location) for p in places]
    except Exception as e:
        logger.error("Places API exception: %s", e)
        return None


def _parse_place(place: dict, niche: str, location: str) -> dict:
    name = place.get("displayName", {}).get("text", "Unknown Business")
    address = place.get("formattedAddress", "")
    rating = place.get("rating")
    review_count = place.get("userRatingCount", 0)
    website = place.get("websiteUri")
    phone = place.get("nationalPhoneNumber")

    parts = address.split(",")
    city = parts[-3].strip() if len(parts) >= 3 else location.split(",")[0].strip()
    state_zip = parts[-2].strip() if len(parts) >= 2 else ""
    state = state_zip.split()[0] if state_zip else ""

    has_website = bool(website)
    has_ssl = has_website and website.startswith("https") if website else False

    return {
        "business_name": name,
        "address": ", ".join(parts[:-2]).strip() if len(parts) >= 3 else address,
        "city": city,
        "state": state,
        "phone": phone,
        "website": website,
        "rating": rating,
        "review_count": review_count or 0,
        "has_website": has_website,
        "has_ssl": has_ssl,
        "page_speed": None,
        "needs": [],
        "opportunity_score": 0,
        "pitch_suggestion": "",
        "niche": niche,
        "location": location,
        "google_maps_url": place.get("googleMapsUri"),
    }


# ── PageSpeed Insights API (free) ──

async def get_pagespeed(url: str) -> dict | None:
    if not url:
        return None
    try:
        params = {"url": url, "strategy": "mobile", "category": ["performance", "seo"]}
        if has_google_key():
            params["key"] = GOOGLE_API_KEY
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(PAGESPEED_URL, params=params)
            if resp.status_code != 200:
                logger.warning("PageSpeed error %d for %s", resp.status_code, url)
                return None
            data = resp.json()
            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            audits = lighthouse.get("audits", {})

            perf_score = categories.get("performance", {}).get("score", 0)
            seo_score = categories.get("seo", {}).get("score", 0)

            speed_index = audits.get("speed-index", {}).get("numericValue", 0) / 1000
            fcp = audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000
            lcp = audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000

            has_ssl = url.startswith("https")
            has_meta_desc = audits.get("meta-description", {}).get("score", 0) == 1
            has_viewport = audits.get("viewport", {}).get("score", 0) == 1

            return {
                "performance_score": round(perf_score * 100),
                "seo_score": round(seo_score * 100),
                "speed_index": round(speed_index, 1),
                "first_contentful_paint": round(fcp, 1),
                "largest_contentful_paint": round(lcp, 1),
                "has_ssl": has_ssl,
                "has_meta_description": has_meta_desc,
                "has_viewport": has_viewport,
                "load_time": round(speed_index, 1),
            }
    except Exception as e:
        logger.error("PageSpeed exception for %s: %s", url, e)
        return None


# ── Score leads using real data ──

NEEDS_MAP = {
    "no_website": {"label": "No Website", "description": "No website found. Prospects have nowhere to go after finding the business on Google Maps."},
    "slow_site": {"label": "Slow Website", "description": "Website loads in over 5 seconds. 53% of mobile users leave if a page takes over 3 seconds."},
    "no_ssl": {"label": "No SSL", "description": "No HTTPS/SSL certificate. Chrome shows 'Not Secure' warning, scaring away visitors."},
    "weak_seo": {"label": "Weak SEO", "description": "Missing meta descriptions, H1 tags, or proper page titles. Hard to rank on Google."},
    "few_reviews": {"label": "Few Reviews", "description": "Less than 10 Google reviews. Customers compare against competitors with 50+ reviews."},
    "low_rating": {"label": "Low Rating", "description": "Rating below 4.0 stars. This halves click-through from local pack results."},
    "no_social": {"label": "No Social Media", "description": "No social media profiles found. Missing out on brand awareness and local engagement."},
    "no_schema": {"label": "No Schema Markup", "description": "No structured data. Missing rich snippets in Google search results."},
}


def score_lead(lead: dict, pagespeed: dict | None = None) -> dict:
    needs = []

    if not lead["has_website"]:
        needs.append("no_website")
    else:
        if pagespeed:
            lead["page_speed"] = pagespeed["load_time"]
            lead["has_ssl"] = pagespeed["has_ssl"]
            if pagespeed["load_time"] > 5:
                needs.append("slow_site")
            if not pagespeed["has_ssl"]:
                needs.append("no_ssl")
            if pagespeed["seo_score"] < 70 or not pagespeed.get("has_meta_description"):
                needs.append("weak_seo")
        else:
            if not lead.get("has_ssl"):
                needs.append("no_ssl")

    if lead["review_count"] < 10:
        needs.append("few_reviews")
    if lead.get("rating") and lead["rating"] < 4.0:
        needs.append("low_rating")

    score = min(100, len(needs) * 15 + (20 if not lead["has_website"] else 0))

    pitch_parts = []
    if not lead["has_website"]:
        pitch_parts.append("Website Build")
    elif "no_ssl" in needs:
        pitch_parts.append("SSL + Security")
    if "weak_seo" in needs:
        pitch_parts.append("SEO Optimization")
    if "few_reviews" in needs or "low_rating" in needs:
        pitch_parts.append("Review Strategy")
    if "slow_site" in needs:
        pitch_parts.append("Speed Optimization")
    pitch = "Pitch: " + " + ".join(pitch_parts[:3]) if pitch_parts else "Pitch: General Web Presence"

    lead["needs"] = [{"key": n, **NEEDS_MAP[n]} for n in needs]
    lead["opportunity_score"] = score
    lead["pitch_suggestion"] = pitch
    return lead


# ── Google Gemini API ──

GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


async def _call_gemini(prompt: str) -> str | None:
    if not has_gemini_key():
        return None
    async with httpx.AsyncClient(timeout=30) as client:
        for model in GEMINI_MODELS:
            try:
                url = GEMINI_API_URL.format(model=model)
                resp = await client.post(
                    url,
                    params={"key": GEMINI_API_KEY},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                elif resp.status_code == 429:
                    logger.warning("Gemini %s rate limited, trying next model", model)
                    continue
                else:
                    logger.warning("Gemini %s error %d: %s", model, resp.status_code, resp.text[:200])
                    continue
            except Exception as e:
                logger.error("Gemini %s exception: %s", model, e)
                continue
    return None


async def generate_ai_pitch(lead: dict, tone: str = "professional") -> dict | None:
    if not has_gemini_key():
        return None

    needs_text = ", ".join(n.get("label", "") for n in lead.get("needs", []) if isinstance(n, dict))
    prompt = f"""Write a cold outreach email to {lead['business_name']}, a {lead.get('niche', 'local')} business in {lead.get('city', '')}, {lead.get('state', '')}.

Their issues: {needs_text or 'general web presence improvement needed'}.
Rating: {lead.get('rating', 'N/A')} stars with {lead.get('review_count', 0)} reviews.
Website: {lead.get('website', 'None')}.
Page speed: {lead.get('page_speed', 'N/A')} seconds.

Tone: {tone}
Write ONLY the email. Start with a subject line on the first line (format: "Subject: ..."), then a blank line, then the email body. Keep it under 200 words. Be specific about their actual issues. End with a soft CTA for a 10-minute call."""

    text = await _call_gemini(prompt)
    if not text:
        return None

    if text.startswith("Subject:"):
        lines = text.split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip()
        body = lines[1].strip() if len(lines) > 1 else ""
    else:
        subject = f"Quick question about {lead['business_name']}'s online presence"
        body = text

    return {"subject": subject, "body": body}


async def generate_ai_website(business_name: str, niche: str, location: str,
                               phone: str = None, description: str = None) -> dict | None:
    if not has_gemini_key():
        return None

    prompt = f"""Generate a complete, modern, responsive single-page website HTML for:
Business: {business_name}
Niche: {niche}
Location: {location}
Phone: {phone or '(555) 123-4567'}
Description: {description or f'Professional {niche} services in {location}'}

Requirements:
- Complete HTML document with inline CSS (no external dependencies)
- Modern dark professional design with green accents (#16a34a)
- Sections: Hero with CTA, Services (4-6 services relevant to {niche}), About Us, Testimonials (3 fake but realistic), Contact form, Footer
- Mobile responsive
- Clean, professional typography
- Include the phone number and location prominently
- Make it look like a real professional business website

Return ONLY the HTML code, no explanations."""

    html = await _call_gemini(prompt)
    if not html:
        return None

    if html.startswith("```html"):
        html = html[7:]
    if html.startswith("```"):
        html = html[3:]
    if html.endswith("```"):
        html = html[:-3]

    return {
        "business_name": business_name,
        "niche": niche,
        "location": location,
        "phone": phone or "(555) 123-4567",
        "html": html.strip(),
        "generated": True,
        "ai_generated": True,
    }


# ── Google Custom Search API ──

async def search_serp(query: str, location: str = "United States") -> dict | None:
    if not has_google_key():
        return None
    cx = os.getenv("GOOGLE_CUSTOM_SEARCH_CX", "")
    if not cx:
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                CUSTOM_SEARCH_URL,
                params={
                    "key": GOOGLE_API_KEY,
                    "cx": cx,
                    "q": query,
                    "num": 10,
                },
            )
            if resp.status_code != 200:
                logger.warning("Custom Search error %d: %s", resp.status_code, resp.text[:200])
                return None
            data = resp.json()
            items = data.get("items", [])
            competitors = []
            for i, item in enumerate(items[:10]):
                url = item.get("link", "")
                competitors.append({
                    "position": i + 1,
                    "url": url,
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "domain_authority": 0,
                    "word_count": 0,
                    "has_schema": False,
                    "has_ssl": url.startswith("https"),
                    "difficulty": 0,
                })
            search_info = data.get("searchInformation", {})
            return {
                "mode": "keyword",
                "query": query,
                "total_results": int(search_info.get("totalResults", 0)),
                "competitors": competitors,
                "keyword_difficulty": 0,
                "monthly_volume": 0,
                "cpc": 0,
            }
    except Exception as e:
        logger.error("Custom Search exception: %s", e)
        return None
