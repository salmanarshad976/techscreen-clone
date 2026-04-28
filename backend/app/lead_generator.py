"""Simulated lead generation with realistic data when no API keys are available."""

import random
import hashlib

FIRST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson",
    "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Clark", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Hill",
    "Green", "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Gonzalez"
]

BUSINESS_SUFFIXES = {
    "hvac": ["Heating & Cooling", "HVAC Services", "Climate Control", "Air Conditioning", "Mechanical", "Comfort Systems", "Indoor Air", "Temperature Pros"],
    "plumber": ["Plumbing", "Plumbing & Drain", "Pipe Masters", "Water Works", "Plumbing Solutions", "Drain Pros", "Leak Fixers"],
    "dentist": ["Dental", "Family Dentistry", "Dental Care", "Smile Center", "Dental Group", "Orthodontics", "Dental Studio"],
    "electrician": ["Electric", "Electrical Services", "Power Solutions", "Wiring Pros", "Electric Co.", "Electrical Contractors"],
    "roofing": ["Roofing", "Roof Masters", "Roofing Solutions", "Roof Repair", "Roofing Co.", "Top Notch Roofing"],
    "landscaping": ["Landscaping", "Lawn Care", "Green Spaces", "Garden Pros", "Outdoor Living", "Yard Masters"],
    "auto repair": ["Auto Repair", "Automotive", "Car Care", "Auto Service", "Mechanic Shop", "Motor Works"],
    "restaurant": ["Kitchen", "Bistro", "Grill", "Diner", "Eatery", "Cafe", "Restaurant", "Food Co."],
    "lawyer": ["Law Firm", "Legal Services", "Attorneys at Law", "Law Group", "Legal Associates", "Law Office"],
    "real estate": ["Realty", "Real Estate Group", "Properties", "Home Experts", "Real Estate Solutions"],
}

STREET_NAMES = [
    "Main St", "Oak Ave", "Elm St", "Cedar Blvd", "Pine Dr", "Maple Ln", "Washington Ave",
    "Park Rd", "Lake Dr", "Hill St", "River Rd", "Broadway", "Market St", "Commerce Dr",
    "Industrial Blvd", "University Ave", "Highway 290", "Memorial Dr", "Westheimer Rd"
]

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


def _seed_random(niche: str, location: str, index: int) -> random.Random:
    seed = hashlib.md5(f"{niche}:{location}:{index}".encode()).hexdigest()
    return random.Random(seed)


def _generate_phone(rng: random.Random, area_codes: list[str]) -> str:
    area = rng.choice(area_codes)
    return f"({area}) {rng.randint(200,999)}-{rng.randint(1000,9999)}"


CITY_DATA = {
    "houston": {"state": "TX", "zip_prefix": "770", "area_codes": ["713", "281", "832"]},
    "dallas": {"state": "TX", "zip_prefix": "752", "area_codes": ["214", "972", "469"]},
    "austin": {"state": "TX", "zip_prefix": "787", "area_codes": ["512", "737"]},
    "san antonio": {"state": "TX", "zip_prefix": "782", "area_codes": ["210"]},
    "new york": {"state": "NY", "zip_prefix": "100", "area_codes": ["212", "718", "646"]},
    "los angeles": {"state": "CA", "zip_prefix": "900", "area_codes": ["213", "310", "323"]},
    "chicago": {"state": "IL", "zip_prefix": "606", "area_codes": ["312", "773"]},
    "phoenix": {"state": "AZ", "zip_prefix": "850", "area_codes": ["602", "480"]},
    "miami": {"state": "FL", "zip_prefix": "331", "area_codes": ["305", "786"]},
    "atlanta": {"state": "GA", "zip_prefix": "303", "area_codes": ["404", "678"]},
    "denver": {"state": "CO", "zip_prefix": "802", "area_codes": ["303", "720"]},
    "seattle": {"state": "WA", "zip_prefix": "981", "area_codes": ["206", "425"]},
    "boston": {"state": "MA", "zip_prefix": "021", "area_codes": ["617", "857"]},
    "las vegas": {"state": "NV", "zip_prefix": "891", "area_codes": ["702"]},
    "portland": {"state": "OR", "zip_prefix": "972", "area_codes": ["503", "971"]},
}


def _get_city_data(location: str) -> dict:
    loc_lower = location.lower().strip()
    for city, data in CITY_DATA.items():
        if city in loc_lower:
            return {**data, "city": city.title()}
    return {"state": "TX", "zip_prefix": "750", "area_codes": ["214"], "city": location.split(",")[0].strip().title()}


def generate_leads(niche: str, location: str, count: int = 40) -> list[dict]:
    city_data = _get_city_data(location)
    niche_lower = niche.lower().strip()
    suffixes = BUSINESS_SUFFIXES.get(niche_lower, [f"{niche.title()} Services", f"{niche.title()} Co.", f"{niche.title()} Pros", f"{niche.title()} Solutions", f"{niche.title()} Experts"])

    leads = []
    for i in range(count):
        rng = _seed_random(niche, location, i)
        name_prefix = rng.choice(FIRST_NAMES)
        suffix = rng.choice(suffixes)
        business_name = f"{name_prefix}'s {suffix}" if rng.random() > 0.4 else f"{city_data['city']} {suffix}"

        has_website = rng.random() > 0.18
        rating = round(rng.uniform(1.0, 5.0), 1) if rng.random() > 0.05 else None
        review_count = rng.randint(0, 200) if rating else 0
        has_ssl = has_website and rng.random() > 0.3
        page_speed = round(rng.uniform(1.5, 12.0), 1) if has_website else None

        needs = []
        if not has_website:
            needs.append("no_website")
        if has_website and not has_ssl:
            needs.append("no_ssl")
        if has_website and page_speed and page_speed > 5:
            needs.append("slow_site")
        if has_website and rng.random() > 0.5:
            needs.append("weak_seo")
        if review_count < 10:
            needs.append("few_reviews")
        if rating and rating < 4.0:
            needs.append("low_rating")
        if rng.random() > 0.6:
            needs.append("no_social")
        if has_website and rng.random() > 0.7:
            needs.append("no_schema")

        score = min(100, len(needs) * 15 + rng.randint(0, 10))
        if not has_website:
            score = min(100, score + 20)

        pitch_parts = []
        if not has_website:
            pitch_parts.append("Website Build")
        elif not has_ssl:
            pitch_parts.append("SSL + Security")
        if "weak_seo" in needs:
            pitch_parts.append("SEO Optimization")
        if "few_reviews" in needs or "low_rating" in needs:
            pitch_parts.append("Review Strategy")
        if "slow_site" in needs:
            pitch_parts.append("Speed Optimization")
        if "no_social" in needs:
            pitch_parts.append("Social Media Setup")
        pitch_suggestion = "Pitch: " + " + ".join(pitch_parts[:3]) if pitch_parts else "Pitch: General Web Presence"

        street_num = rng.randint(100, 9999)
        street = rng.choice(STREET_NAMES)
        zip_code = f"{city_data['zip_prefix']}{rng.randint(10,99)}"

        domain_name = business_name.lower().replace("'s ", "").replace(" ", "").replace("&", "and")[:20]
        website = f"https://www.{domain_name}.com" if has_website else None

        leads.append({
            "business_name": business_name,
            "address": f"{street_num} {street}",
            "city": city_data["city"],
            "state": city_data["state"],
            "zip": zip_code,
            "phone": _generate_phone(rng, city_data["area_codes"]),
            "website": website,
            "rating": rating,
            "review_count": review_count,
            "opportunity_score": score,
            "has_website": has_website,
            "has_ssl": has_ssl,
            "page_speed": page_speed,
            "needs": [{"key": n, **NEEDS_MAP[n]} for n in needs],
            "pitch_suggestion": pitch_suggestion,
            "niche": niche,
            "location": location,
        })

    leads.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return leads


def generate_niche_scan(niches: list[str], cities: list[str]) -> list[dict]:
    results = []
    for niche in niches:
        for city in cities:
            rng = _seed_random(niche, city, 0)
            business_count = rng.randint(80, 600)
            weak_pct = rng.randint(15, 55)
            results.append({
                "niche": niche,
                "city": city,
                "business_count": business_count,
                "weak_presence_pct": weak_pct,
                "opportunity_score": min(100, weak_pct * 2 + rng.randint(0, 10)),
                "avg_cpc": round(rng.uniform(2.0, 45.0), 2),
                "monthly_search_volume": rng.randint(500, 15000),
                "keyword_difficulty": rng.randint(10, 80),
            })
    results.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return results


def generate_serp_results(query: str) -> dict:
    rng = random.Random(hashlib.md5(query.encode()).hexdigest())
    is_url = "." in query and " " not in query

    if is_url:
        return {
            "mode": "website",
            "url": query if query.startswith("http") else f"https://{query}",
            "domain_authority": rng.randint(5, 85),
            "page_speed_mobile": rng.randint(20, 95),
            "page_speed_desktop": rng.randint(40, 99),
            "backlinks": rng.randint(10, 50000),
            "referring_domains": rng.randint(5, 5000),
            "organic_traffic": rng.randint(100, 500000),
            "organic_keywords": rng.randint(50, 20000),
            "issues": [
                {"severity": "high", "title": "Missing meta descriptions on 12 pages", "fix": "Add unique meta descriptions to each page"},
                {"severity": "high", "title": f"Page speed score: {rng.randint(20,45)}/100 on mobile", "fix": "Optimize images, enable compression, reduce JavaScript"},
                {"severity": "medium", "title": "No schema markup detected", "fix": "Add LocalBusiness structured data"},
                {"severity": "medium", "title": f"Only {rng.randint(2,8)} internal links per page", "fix": "Improve internal linking structure"},
                {"severity": "low", "title": "No Open Graph tags", "fix": "Add OG tags for social sharing"},
            ]
        }
    else:
        competitors = []
        for i in range(10):
            r = _seed_random(query, "serp", i)
            domain = f"{r.choice(['best','top','pro','local','city'])}{query.replace(' ','')[:10]}{r.randint(1,99)}.com"
            competitors.append({
                "position": i + 1,
                "url": f"https://www.{domain}",
                "title": f"{query.title()} - {r.choice(['Best', 'Top Rated', 'Professional', '#1', 'Trusted'])} Services",
                "domain_authority": rng.randint(10, 75),
                "word_count": rng.randint(300, 5000),
                "has_schema": rng.random() > 0.5,
                "has_ssl": rng.random() > 0.2,
                "difficulty": rng.randint(15, 85),
            })
        return {
            "mode": "keyword",
            "query": query,
            "keyword_difficulty": rng.randint(20, 70),
            "monthly_volume": rng.randint(500, 20000),
            "cpc": round(rng.uniform(1.5, 35.0), 2),
            "competitors": competitors,
        }


def generate_competitor_compare(url1: str, url2: str) -> dict:
    rng1 = random.Random(hashlib.md5(url1.encode()).hexdigest())
    rng2 = random.Random(hashlib.md5(url2.encode()).hexdigest())

    def metrics(rng):
        return {
            "domain_authority": rng.randint(5, 80),
            "page_speed": rng.randint(20, 95),
            "backlinks": rng.randint(10, 10000),
            "organic_keywords": rng.randint(20, 5000),
            "monthly_traffic": rng.randint(100, 50000),
            "has_ssl": rng.random() > 0.3,
            "mobile_friendly": rng.random() > 0.4,
            "schema_markup": rng.random() > 0.5,
            "social_profiles": rng.randint(0, 5),
            "review_count": rng.randint(0, 200),
            "avg_rating": round(rng.uniform(2.5, 5.0), 1),
        }

    return {
        "site1": {"url": url1, **metrics(rng1)},
        "site2": {"url": url2, **metrics(rng2)},
    }


def generate_nap_audit(business_name: str) -> dict:
    rng = random.Random(hashlib.md5(business_name.encode()).hexdigest())
    directories = [
        "Google Business Profile", "Yelp", "Facebook", "Yellow Pages", "BBB",
        "Angi", "Thumbtack", "Manta", "Foursquare", "Apple Maps",
        "Bing Places", "MapQuest", "CitySearch", "Superpages", "DexKnows",
        "Hotfrog", "Brownbook", "Chamberofcommerce.com", "Merchantcircle", "Ezlocal",
        "Showmelocal", "Tupalo", "Cylex", "eLocal", "Localpages",
        "YellowBot", "2findlocal", "iBegin", "Bizwiki", "Lacartes",
        "LocalDatabase", "USCity.net", "Citysquares", "Hub.biz", "Tuugo",
        "AddBusiness", "Opendi", "Fyple", "GoLocalPro", "Find-Us-Here",
        "MyHuckleberry", "Nexport", "Wand.com", "Yext PowerListings", "Neustar",
        "Data Axle"
    ]
    results = []
    for d in directories:
        status = rng.choice(["found_correct", "found_incorrect", "not_found", "not_found", "found_correct"])
        results.append({
            "directory": d,
            "status": status,
            "name_match": status == "found_correct",
            "address_match": status == "found_correct" or (status == "found_incorrect" and rng.random() > 0.5),
            "phone_match": status == "found_correct" or (status == "found_incorrect" and rng.random() > 0.5),
        })
    correct = sum(1 for r in results if r["status"] == "found_correct")
    incorrect = sum(1 for r in results if r["status"] == "found_incorrect")
    missing = sum(1 for r in results if r["status"] == "not_found")
    return {
        "business_name": business_name,
        "total_directories": len(directories),
        "correct": correct,
        "incorrect": incorrect,
        "missing": missing,
        "score": round(correct / len(directories) * 100),
        "results": results,
    }


def generate_backlinks(domain: str) -> dict:
    rng = random.Random(hashlib.md5(domain.encode()).hexdigest())
    backlinks = []
    for i in range(rng.randint(15, 50)):
        r = _seed_random(domain, "bl", i)
        source = f"{r.choice(['blog','news','directory','forum','wiki'])}{r.randint(1,999)}.{r.choice(['com','org','net','io'])}"
        backlinks.append({
            "source_url": f"https://{source}/page-{r.randint(1,100)}",
            "source_domain": source,
            "domain_rating": r.randint(5, 80),
            "anchor_text": r.choice([domain, "click here", "visit website", "learn more", domain.split(".")[0]]),
            "link_type": r.choice(["dofollow", "nofollow"]),
            "first_seen": f"2024-{r.randint(1,12):02d}-{r.randint(1,28):02d}",
            "geo_fit": r.choice(["high", "medium", "low"]),
        })
    return {
        "domain": domain,
        "total_backlinks": len(backlinks),
        "referring_domains": len(set(b["source_domain"] for b in backlinks)),
        "dofollow_pct": round(sum(1 for b in backlinks if b["link_type"] == "dofollow") / len(backlinks) * 100),
        "backlinks": backlinks,
    }


def generate_website(business_name: str, niche: str, location: str, phone: str = None, description: str = None) -> dict:
    return {
        "business_name": business_name,
        "niche": niche,
        "location": location,
        "phone": phone or "(555) 123-4567",
        "sections": ["hero", "services", "about", "testimonials", "contact", "footer"],
        "color_scheme": {"primary": "#16a34a", "secondary": "#1e293b", "accent": "#22d3ee"},
        "generated": True,
    }
