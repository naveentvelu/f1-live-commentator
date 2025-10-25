import requests, datetime, re, time
from collections import defaultdict
import json
import html

OPENF1 = "https://api.openf1.org/v1"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": "f1-live-commentator/0.1 (+https://github.com/your-repo-or-contact)",
    "Accept": "application/json",
}

def _get(url, **params):
    r = requests.get(url, params=params, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def load_drivers(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return {int(d["driver_number"]): d for d in data}
    

def load_race(path):
    with open(path, "r", encoding="utf-8") as f:
        sessions = json.load(f)
    if isinstance(sessions, dict):
        sessions = [sessions]
    race_session = next((s for s in sessions if s.get("session_type", "").lower() == "race"), None)
    if not race_session:
        raise FileNotFoundError("No 'Race' session found in ../data/sessions.json")


    race_dt = datetime.datetime.fromisoformat(race_session["date_start"])

    meeting = None
    try:
        with open("../data/meetings.json", "r", encoding="utf-8") as mf:
            meetings = json.load(mf)
            if isinstance(meetings, dict):
                meetings = [meetings]
            meetings_by_key = {m["meeting_key"]: m for m in meetings if "meeting_key" in m}
            meeting = meetings_by_key.get(race_session.get("meeting_key"))
    except FileNotFoundError:
        meeting = None

    year = meeting.get("year") if (meeting and "year" in meeting) else race_session.get("year")
    meeting_name = (meeting.get("meeting_name") if meeting else None) or race_session.get("circuit_short_name") or race_session.get("location")

    race = {
        "meeting_key": race_session.get("meeting_key"),
        "session_key": race_session.get("session_key"),
        "date_start": race_dt,
        "date_end": race_session.get("date_end"),
        "year": year,
        "meeting_name": meeting_name,
        "location": race_session.get("location"),
        "country": race_session.get("country_name"),
    }
    return race

def wiki_find_title(name: str, extra_hint: str = "Formula One"):
    """
    Finds the most likely page title for the driver.
    Falls back to 'Name (racing driver)' patterns when available.
    """
    q = f"{name} {extra_hint}"
    res = _get(WIKI_SEARCH, action="query", list="search", format="json", srsearch=q, srlimit=5)
    hits = res.get("query", {}).get("search", [])
    if not hits: return None

    for h in hits:
        title = h["title"]
        tl = title.lower()
        if name.lower() in tl and ("racing driver" in tl or "formula one" in h.get("snippet","").lower()):
            return title
    return hits[0]["title"]

def clean_wiki_text(text: str | None) -> str | None:
    """Remove common Wikipedia bracketed citation markers like [1], [a], [citation needed]."""
    if not text:
        return text
    # remove short bracketed markers commonly used for citations/notes
    text = re.sub(r'\[\s*(?:\d+|[A-Za-z]\w*|citation needed)\s*\]', '', text)
    # collapse whitespace left behind
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def wiki_top_intro(title: str | None) -> str | None:
    """
    Fetch the lead (intro) of the page using action=parse&section=0 and return the
    first meaningful paragraph as plain text.
    """
    if not title:
        return None
    try:
        j = _get(WIKI_SEARCH, action="parse", page=title, prop="text", section=0, format="json")
        html_text = j.get("parse", {}).get("text", {}).get("*", "") or ""
        if not html_text:
            return None

        # Remove tables/infoboxes/navboxes (which often appear before text)
        html_text = re.sub(r'<table[^>]*>.*?</table>', '', html_text, flags=re.DOTALL|re.IGNORECASE)
        # Strip references/superscripts
        html_text = re.sub(r'<sup[^>]*>.*?</sup>', '', html_text, flags=re.DOTALL|re.IGNORECASE)
        # Strip all tags
        text = re.sub(r'<[^>]+>', '', html_text)
        text = html.unescape(text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return None

        # Try to split into paragraphs sensibly. The lead can be one long block; prefer the first sentence-rich chunk.
        paras = [p.strip() for p in re.split(r'(?:\n{2,}|(?<=\.)\s{2,})', text) if p.strip()]
        lead = paras[0] if paras else text

        # Occasionally templates leave artifacts like “[citation needed]” or stray brackets; clean lightly.
        lead = re.sub(r'\[\s*\d+\s*\]', '', lead)          # [1], [2], ...
        lead = re.sub(r'\s*\[\s*citation needed\s*\]\s*', '', lead, flags=re.IGNORECASE)
        return lead if lead else None
    except requests.HTTPError:
        return None


def wiki_section_text(title: str | None, section_title='(Top)') -> str | None:
    """
    Fetch a specific section by title (e.g. "Driver profile") from the page using action=parse.
    If section_title == "(Top)", return the page lead via section=0.
    """
    if not title:
        return None

    # Special-case the top/lead section
    if (section_title or '').strip().lower() in {'(top)', 'lead', 'intro', 'introduction'}:
        return wiki_top_intro(title)

    try:
        j = _get(WIKI_SEARCH, action="parse", page=title, prop="sections", format="json")
        sections = j.get("parse", {}).get("sections", [])
        match_idx = None
        target = section_title.strip().lower().replace("_", " ")

        for s in sections:
            line = (s.get("line") or "").strip().lower()
            anchor = (s.get("anchor") or "").strip().lower()
            if line == target or target in line or anchor == target.replace(" ", "_"):
                match_idx = s.get("index")
                break

        if not match_idx:
            return None

        j2 = _get(WIKI_SEARCH, action="parse", page=title, prop="text", section=match_idx, format="json")
        html_text = j2.get("parse", {}).get("text", {}).get("*", "") or ""
        text = re.sub(r'<[^>]+>', '', html_text)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return None

        paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
        result = paras[0] if paras else text
        return result or None
    except requests.HTTPError:
        return None


def wiki_summary(title: str | None):
    if not title:
        return None

    # REST summary remains the primary source for title/description/extract/urls
    j = _get(WIKI_REST + title)
    summary = {
        "title": j.get("title"),
        "description": clean_wiki_text(j.get("description")),
        "extract": clean_wiki_text(j.get("extract")),
        "content_urls": (j.get("content_urls") or {}).get("desktop", {}).get("page"),
    }

    # Try 'Driver profile' first; fall back to the page lead if not found
    profile = wiki_section_text(title, "Driver profile")
    if not profile:
        profile = wiki_section_text(title, "(Top)")  

    summary["driver_profile"] = profile or None
    return summary

def redact_future_spoilers(text: str | None, cutoff_year: int) -> str | None:
    """
    Naive but effective: drop sentences that mention a year > cutoff_year.
    Keeps the intro bio vibe without “later champion in 202X” leaks.
    """
    if not text: return text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    keep = []
    for s in sentences:
        years = [int(y) for y in re.findall(r'\b(19|20)\d{2}\b', s)]
        if years and max(years) > cutoff_year:
            continue
        keep.append(s)
    return " ".join(keep).strip()

def build_driver_bio(name: str, cutoff_year: int):
    title = wiki_find_title(name, extra_hint="racing driver")
    bio = wiki_summary(title) if title else None

    if bio and bio.get("extract"):
        bio["extract"] = redact_future_spoilers(bio["extract"], cutoff_year)
        bio["driver_profile"] = redact_future_spoilers(bio.get("driver_profile"), cutoff_year)
        print(cutoff_year)
    return bio

# New helper that builds bio using the page as of cutoff datetime
def build_driver_bio_at(name: str, cutoff_dt: datetime.datetime):
    title = wiki_find_title(name, extra_hint="racing driver")
    if not title:
        return None

    # Try to get REST summary (current) as a fallback for title/description/url
    rest = None
    try:
        rest = _get(WIKI_REST + title)
    except Exception:
        rest = None

    summary = {
        "title": (rest or {}).get("title"),
        "description": clean_wiki_text((rest or {}).get("description")) if rest else None,
        "extract": None,
        "content_urls": (rest or {}).get("content_urls", {}).get("desktop", {}).get("page") if rest else None,
    }

    # Prefer the page lead as of the cutoff datetime
    lead = wiki_top_intro_as_of(title, cutoff_dt)
    if lead:
        summary["driver_profile"] = lead
        # Also use the lead as an 'extract' if REST extract is not available
        summary["extract"] = summary.get("extract") or lead
    else:
        # fallback to current summary/sections
        cur = wiki_summary(title)
        if cur:
            summary["driver_profile"] = cur.get("driver_profile")
            summary["extract"] = cur.get("extract")

    # Still redact any sentences that mention years beyond the cutoff
    cutoff_year = cutoff_dt.year
    if summary.get("extract"):
        summary["extract"] = redact_future_spoilers(summary["extract"], cutoff_year)
    if summary.get("driver_profile"):
        summary["driver_profile"] = redact_future_spoilers(summary["driver_profile"], cutoff_year)

    return summary

def _to_iso_z(dt: datetime.datetime) -> str:
    """Return an ISO8601 UTC timestamp string (Z) suitable for MediaWiki rvend param."""
    if dt.tzinfo is None:
        # assume naive datetimes are already in UTC
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def wiki_revision_before(title: str | None, cutoff_dt: datetime.datetime):
    """
    Return the revision id of the last edit to `title` at or before cutoff_dt.
    Uses action=query&prop=revisions with rvend=timestamp.
    """
    if not title:
        return None
    ts = _to_iso_z(cutoff_dt)
    try:
        j = _get(WIKI_SEARCH, action="query", titles=title, prop="revisions", rvlimit=1, rvprop="ids|timestamp", rvend=ts, format="json")
        pages = j.get("query", {}).get("pages", {})
        for p in pages.values():
            revs = p.get("revisions", [])
            if revs:
                return revs[0].get("revid")
        return None
    except requests.HTTPError:
        return None

def wiki_top_intro_as_of(title: str | None, cutoff_dt: datetime.datetime) -> str | None:
    """
    Fetch the lead (intro) of the page as it existed at cutoff_dt.
    Uses the revision id obtained from wiki_revision_before and action=parse with oldid.
    """
    if not title:
        return None
    rev_id = wiki_revision_before(title, cutoff_dt)
    if not rev_id:
        return None
    try:
        j = _get(WIKI_SEARCH, action="parse", oldid=rev_id, prop="text", section=0, format="json")
        html_text = j.get("parse", {}).get("text", {}).get("*", "") or ""
        if not html_text:
            return None
        # Remove tables/infoboxes/navboxes
        html_text = re.sub(r'<table[^>]*>.*?</table>', '', html_text, flags=re.DOTALL|re.IGNORECASE)
        html_text = re.sub(r'<sup[^>]*>.*?</sup>', '', html_text, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', html_text)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return None
        paras = [p.strip() for p in re.split(r'(?:\n{2,}|(?<=\.)\s{2,})', text) if p.strip()]
        lead = paras[0] if paras else text
        lead = re.sub(r'\[\s*\d+\s*\]', '', lead)
        lead = re.sub(r'\s*\[\s*citation needed\s*\]\s*', '', lead, flags=re.IGNORECASE)
        return lead or None
    except requests.HTTPError:
        return None

def build_and_script():
    race = load_race("data/sessions.json")
    drivers = load_drivers("data/drivers.json")

    # determine cutoff datetime (use race['date_start'] which is a datetime)
    cutoff_dt = race["date_start"]

    # build a bios dict keyed by driver number and write to data/drivers_history.json
    bios = {}
    for dnum, d in drivers.items():
        try:
            bio = build_driver_bio_at(d.get("full_name"), cutoff_dt=cutoff_dt)
        except Exception as e:
            bio = {"error": str(e)}
        bios[str(dnum)] = {
            "driver_number": dnum,
            "full_name": d.get("full_name"),
            "team_name": d.get("team_name"),
            "wiki_title": wiki_find_title(d.get("full_name") or "", extra_hint="racing driver"),
            "bio": bio,
        }
        time.sleep(0.1)

    out_path = "data/drivers_history.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bios, f, ensure_ascii=False, indent=2)

    return

build_and_script()

