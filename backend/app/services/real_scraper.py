"""Real job scrapers using public APIs and direct HTTP.

No browser, no login, no fake data. Each scraper returns genuinely live
listings or an empty list — never sample jobs.
"""
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


async def _get_json(url: str, timeout: float = 20.0) -> dict | list | None:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout,
                                 headers={"User-Agent": _UA, "Accept": "application/json"}) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _clean(data: dict, position: str = "", company: str = "", location: str = "") -> dict:
    pos = (data.get("position") or position or "").strip()
    comp = (data.get("company") or company or "").strip()
    url = (data.get("url") or data.get("apply_url") or "").strip()
    loc = (data.get("location") or location or "").strip()
    return {
        "title": pos[:200],
        "company": comp[:150],
        "location": loc[:150],
        "description": (data.get("description") or "")[:2000],
        "platform_source": data.get("_source", "remoteok"),
        "platform_url": url,
        "platform_job_id": data.get("id") or data.get("job_id") or f"{data.get('_source','')}_{abs(hash(pos + comp))}",
        "job_type": (data.get("job_type") or "full-time")[:50],
        "remote_option": "remote" in (pos + loc).lower(),
        "skills_required": (data.get("skills_required") or data.get("tags") or [])[:10],
        "salary_min": data.get("salary_min"),
        "salary_max": data.get("salary_max"),
    }


def _matches(title: str, query: str) -> bool:
    """Smart title-only keyword match.

    Keeps a job if the FIRST query keyword appears in the title, or if ANY
    query keyword appears in the title when the primary keyword has no hits
    (handles dynamic feeds with few matches). Tags are NOT used because
    several feeds (RemoteOK) append the full tag pool to every listing.
    """
    words = [w for w in query.lower().split() if len(w) > 1]
    if not words:
        return True
    primary = words[0]
    if primary in title.lower():
        return True
    return any(w in title.lower() for w in words[1:])


async def scrape_remoteok(query: str = "python", max_results: int = 30) -> list:
    """RemoteOK public JSON API — real remote jobs, no auth needed."""
    try:
        data = await _get_json("https://remoteok.com/api")
        if not isinstance(data, list):
            return []
        tag = query.strip().lower()
        out = []
        for item in data:
            if not isinstance(item, dict) or item.get("id") == "_":
                continue
            pos = (item.get("position") or "").lower()
            if tag and not _matches(pos, tag):
                continue
            job = _clean(item)
            if not job["title"] or not job["platform_url"]:
                continue
            job = _clean(item)
            if not job["title"] or not job["platform_url"]:
                continue
            out.append(job)
            if len(out) >= max_results:
                break
        logger.info("RemoteOK: %d real jobs for '%s'", len(out), query)
        return out
    except Exception as e:
        logger.warning("RemoteOK scrape failed: %s", e)
        return []


async def scrape_github_jobs(query: str = "python", max_results: int = 30) -> list:
    """GitHub Jobs API (now read-only archive, returns 422) — kept as a no-op fallback."""
    return []


async def scrape_remotive(query: str = "python", max_results: int = 30) -> list:
    """Remotive public API — real remote jobs, no auth needed."""
    try:
        data = await _get_json(f"https://remotive.com/api/remote-jobs?search={query}")
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        tag = query.strip().lower()
        out = []
        for item in jobs:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").lower()
            if tag and not _matches(title, tag):
                continue
            job = _clean(item, position=item.get("title", ""), company=item.get("company_name", ""))
            job["platform_source"] = "remotive"
            job["platform_job_id"] = item.get("id") or f"remotive_{abs(hash(job['title']))}"
            job["skills_required"] = [str(t) for t in (item.get("tags") or [])][:10]
            if not job["title"] or not job["platform_url"]:
                continue
            out.append(job)
            if len(out) >= max_results:
                break
        logger.info("Remotive: %d real jobs for '%s'", len(out), query)
        return out
    except Exception as e:
        logger.warning("Remotive scrape failed: %s", e)
        return []


def _jobs_html(html: str, container_class: str, title_sel: str, link_sel: str) -> list:
    """Small HTML job-card extractor — tries multiple class patterns for Naukri's layout."""
    import re
    jobs = []
    patterns = [
        re.compile(r'<div[^>]*class="[^"]*' + container_class + r'[^"]*"[^>]*>', re.I),
        re.compile(r'<article[^>]*class="[^"]*' + container_class + r'[^"]*"[^>]*>', re.I),
    ]
    starts = []
    for pat in patterns:
        starts.extend([m.end() for m in pat.finditer(html)])
    starts.sort()
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(html)
        chunk = html[start:end]
        # Try multiple title patterns
        tm = re.search(r'<a[^>]*class="[^"]*' + title_sel + r'[^"]*"[^>]*>', chunk, re.I)
        if not tm:
            tm = re.search(r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)', chunk, re.I)
        if not tm:
            continue
        atag = chunk[tm.start():tm.end()]
        title = re.sub(r"<[^>]+>", "", chunk[tm.end():])[:200]
        href = re.search(r'href="([^"]+)"', atag)
        if not href:
            continue
        url = href.group(1)
        if not url.startswith("http"):
            url = "https://www.naukri.com" + url if "naukri" in chunk[:400].lower() else "https://" + url
        company = ""
        for comp_pat in [r'class="[^"]*(?:companyName|comp-name|company|companyName__Text)[^"]*"[^>]*>(.*?)</',
                         r'data-testid="company-name"[^>]*>(.*?)<']:
            cm = re.search(comp_pat, chunk, re.I | re.S)
            if cm:
                company = re.sub(r"<[^>]+>", "", cm.group(1)).strip()[:150]
                break
        loc = ""
        for loc_pat in [r'class="[^"]*(?:locWdth|add-span|location|locationGpsWidget)[^"]*"[^>]*>(.*?)</',
                        r'class="[^"]*loc[^"]*"[^>]*>(.*?)<']:
            lm = re.search(loc_pat, chunk, re.I | re.S)
            if lm:
                loc = re.sub(r"<[^>]+>", "", lm.group(1)).strip()[:150]
                break
        title = re.sub(r"\s+", " ", title).strip()
        if title and url:
            jobs.append({
                "title": title[:200], "company": company or "Unknown",
                "location": loc, "description": "",
                "platform_source": "naukri", "platform_url": url,
                "platform_job_id": f"naukri_{abs(hash(url))}",
                "job_type": "full-time", "remote_option": "remote" in (title + loc).lower(),
                "skills_required": [],
            })
    return jobs


async def scrape_naukri_http(query: str = "python developer", max_results: int = 30) -> list:
    """Naukri via plain HTTP — no browser needed, real listings."""
    try:
        url = f"https://www.naukri.com/{query.replace(' ', '-')}-jobs"
        async with httpx.AsyncClient(follow_redirects=True, timeout=25,
                                     headers={"User-Agent": _UA}) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        jobs = _jobs_html(html, "jobTuple", "title", "title")
        logger.info("Naukri HTTP: %d real jobs", len(jobs))
        return jobs[:max_results]
    except Exception as e:
        logger.warning("Naukri HTTP scrape failed: %s", e)
        return []


async def scrape_naukri_browser(query: str = "python developer", max_results: int = 30) -> list:
    """Naukri via headless Chrome — full page renders, real listings + company names."""
    try:
        from app.services.browser_automation import browser_automation, PLAYWRIGHT_AVAILABLE
        if not PLAYWRIGHT_AVAILABLE:
            return []
        jobs = await browser_automation.scrape_jobs("naukri", query)
        for j in jobs:
            j["platform_source"] = "naukri"
            if not j.get("platform_url", "").startswith("http"):
                j["platform_url"] = "https://www.naukri.com" + j["platform_url"]
        logger.info("Naukri browser: %d real jobs", len(jobs))
        return jobs[:max_results]
    except Exception as e:
        logger.warning("Naukri browser scrape failed: %s", e)
        return []


async def scrape_internshala(query: str = "python", max_results: int = 30) -> list:
    """Internshala via plain HTTP — real internships, in-platform apply."""
    try:
        slug = query.strip().replace(" ", "-").lower()
        url = f"https://internshala.com/internships/{slug}-internships"
        async with httpx.AsyncClient(follow_redirects=True, timeout=25,
                                     headers={"User-Agent": _UA}) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        import re
        paths = re.findall(r'href="(/internship/detail/[^"]+)"', html)
        seen = set()
        jobs = []
        for p in paths:
            if p in seen:
                continue
            seen.add(p)
            full = "https://internshala.com" + p
            title = p.split("/")[-1].split("-at-")[0].replace("-", " ").title()
            company = p.split("-at-")[-1].replace("-", " ").title() if "-at-" in p else "Unknown"
            jobs.append({
                "title": title[:200], "company": company[:150],
                "location": "India", "description": "",
                "platform_source": "internshala", "platform_url": full,
                "platform_job_id": f"internshala_{abs(hash(full))}",
                "job_type": "internship", "remote_option": "work-from-home" in p.lower() or "remote" in p.lower(),
                "skills_required": [],
            })
            if len(jobs) >= max_results:
                break
        logger.info("Internshala: %d real internships", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Internshala scrape failed: %s", e)
        return []


async def scrape_naukri(query: str = "python developer", max_results: int = 30) -> list:
    """Naukri scraper — tries HTTP first (works everywhere), falls back to browser."""
    jobs = await scrape_naukri_http(query, max_results)
    if jobs:
        return jobs
    return await scrape_naukri_browser(query, max_results)


async def scrape_jsearch(query: str = "python developer", max_results: int = 30) -> list:
    """JSearch API via OpenWeb Ninja — aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter.

    Free tier: 200 requests/month, no credit card.
    Set JSEARCH_API_KEY env var or backend/.env to enable. Falls back gracefully if not set.
    """
    try:
        from app.core.config import get_settings
        api_key = get_settings().JSEARCH_API_KEY
    except Exception:
        api_key = os.environ.get("JSEARCH_API_KEY", "")
    if not api_key:
        logger.info("JSearch: JSEARCH_API_KEY not set, skipping")
        return []

    try:
        url = "https://api.openwebninja.com/jsearch/search-v2"
        headers = {
            "X-API-Key": api_key,
            "Accept": "application/json",
        }
        params = {
            "query": query,
            "num_pages": "1",
            "date_posted": "week",
            "country": "in",
            "language": "en",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        raw_jobs = data.get("data", {}).get("jobs", [])
        jobs = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            title = (item.get("job_title") or "").strip()
            company = (item.get("employer_name") or "").strip()
            location = (item.get("job_city") or "") + (", " + item.get("job_state", "") if item.get("job_state") else "")
            location = location.strip(", ")
            url = (item.get("job_apply_link") or item.get("job_google_link") or "").strip()
            desc = (item.get("job_description") or "")[:2000]
            source = (item.get("job_publisher") or "linkedin").lower()
            emp_type = (item.get("job_employment_type") or "full-time").lower()

            if not title or not url:
                continue

            skills = []
            if item.get("job_required_skills"):
                skills = item["job_required_skills"][:10]

            jobs.append({
                "title": title[:200],
                "company": company[:150] if company else "Unknown",
                "location": (location or "")[:150],
                "description": desc,
                "platform_source": source[:50],
                "platform_url": url,
                "platform_job_id": f"{source}_{item.get('job_id', abs(hash(title + company)))}",
                "job_type": emp_type[:50],
                "remote_option": bool(item.get("job_is_remote")),
                "skills_required": skills,
                "salary_min": None,
                "salary_max": None,
            })
            if len(jobs) >= max_results:
                break

        logger.info("JSearch: %d jobs for '%s'", len(jobs), query)
        return jobs
    except Exception as e:
        logger.warning("JSearch scrape failed: %s", e)
        return []


REAL_SCRAPERS = {
    "remoteok": scrape_remoteok,
    "remotive": scrape_remotive,
    "naukri": scrape_naukri,
    "internshala": scrape_internshala,
    "linkedin": scrape_jsearch,
    "indeed": scrape_jsearch,
    "glassdoor": scrape_jsearch,
}


async def scrape_real(platform_name: str, query: str = "", max_results: int = 30) -> list:
    """Scrape real jobs for a platform using its real source. Never returns fake data."""
    scraper = REAL_SCRAPERS.get(platform_name.lower())
    if scraper is None:
        return []
    return await scraper(query or "python developer", max_results)


async def scrape_all_real(query: str = "python developer", max_results: int = 15) -> list:
    """Scrape from every working real source and merge. Handles failures gracefully."""
    results = await asyncio.gather(
        scrape_real("remoteok", query, max_results),
        scrape_real("remotive", query, max_results),
        scrape_real("naukri", query, max_results),
        scrape_real("internshala", query, max_results),
        scrape_real("linkedin", query, max_results),
        return_exceptions=True,
    )
    merged = []
    seen = set()
    for group in results:
        if isinstance(group, Exception):
            logger.warning("Scrape source failed: %s", group)
            continue
        for job in group:
            key = job.get("platform_url") or job.get("platform_job_id")
            if key and key not in seen:
                seen.add(key)
                merged.append(job)
    return merged