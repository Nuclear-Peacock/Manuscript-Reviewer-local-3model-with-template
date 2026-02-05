from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import quote_plus
import requests

@dataclass
class Paper:
    title: str
    year: str | None
    venue: str | None
    authors: list[str]
    doi: str | None
    url: str | None

def search_crossref(query: str, rows: int = 8) -> list[Paper]:
    url = f"https://api.crossref.org/works?query={quote_plus(query)}&rows={rows}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    items = (r.json().get("message") or {}).get("items") or []
    out: list[Paper] = []
    for it in items:
        title = (it.get("title") or [""])[0]
        year = None
        if it.get("issued") and it["issued"].get("date-parts"):
            year = str(it["issued"]["date-parts"][0][0])
        authors = []
        for a in it.get("author") or []:
            nm = " ".join([a.get("given",""), a.get("family","")]).strip()
            if nm:
                authors.append(nm)
        doi = it.get("DOI")
        out.append(Paper(title=title, year=year, venue=(it.get("container-title") or [None])[0], authors=authors[:5], doi=doi, url=it.get("URL")))
    return out

def search_pubmed(query: str, retmax: int = 8) -> list[Paper]:
    es = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={retmax}&term={quote_plus(query)}"
    r = requests.get(es, timeout=30)
    r.raise_for_status()
    ids = ((r.json().get("esearchresult") or {}).get("idlist") or [])
    if not ids:
        return []
    summ = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    r2 = requests.get(summ, params={"db":"pubmed","retmode":"json","id":",".join(ids)}, timeout=30)
    r2.raise_for_status()
    data = r2.json().get("result") or {}
    out: list[Paper] = []
    for pid in ids:
        it = data.get(pid) or {}
        title = it.get("title","")
        pubdate = it.get("pubdate","")
        year = pubdate.split(" ")[0] if pubdate else None
        authors = [a.get("name","") for a in it.get("authors") or [] if a.get("name")]
        doi = None
        for a in it.get("articleids") or []:
            if a.get("idtype") == "doi":
                doi = a.get("value")
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
        out.append(Paper(title=title, year=year, venue=it.get("fulljournalname"), authors=authors[:5], doi=doi, url=url))
    return out

def search_semantic_scholar(query: str, limit: int = 8) -> list[Paper]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": limit, "fields": "title,year,venue,authors,externalIds,url"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    items = (r.json().get("data") or [])
    out: list[Paper] = []
    for it in items:
        ext = it.get("externalIds") or {}
        doi = ext.get("DOI") or ext.get("doi")
        authors = [a.get("name","") for a in it.get("authors") or [] if a.get("name")]
        out.append(Paper(title=it.get("title",""), year=str(it.get("year")) if it.get("year") else None,
                         venue=it.get("venue"), authors=authors[:5], doi=doi, url=it.get("url")))
    return out

def novelty_bundle(keywords: list[str]) -> dict:
    q = " ".join(keywords)
    return {
        "query": q,
        "pubmed": [p.__dict__ for p in search_pubmed(q, 8)],
        "crossref": [p.__dict__ for p in search_crossref(q, 8)],
        "semantic_scholar": [p.__dict__ for p in search_semantic_scholar(q, 8)],
    }

def format_novelty_block(bundle: dict, claimed_novelty: str | None = None, key_refs: list[str] | None = None) -> str:
    lines: list[str] = []
    if claimed_novelty:
        lines.append(f"- Claimed novelty (paraphrased): {claimed_novelty}")
    if key_refs:
        lines.append(f"- Key refs provided: {', '.join(key_refs)}")
    lines.append(f"- Search query: {bundle.get('query','')}")
    def add(name, items):
        if not items:
            return
        lines.append(f"\n{name} (top {min(len(items),8)}):")
        for it in items[:8]:
            title = (it.get('title') or '').strip()
            year = it.get('year') or ''
            venue = it.get('venue') or ''
            doi = it.get('doi') or ''
            url = it.get('url') or ''
            lines.append(f"  • {title} ({year}) {venue} DOI:{doi} {url}".strip())
    add("PubMed", bundle.get("pubmed") or [])
    add("Crossref", bundle.get("crossref") or [])
    add("Semantic Scholar", bundle.get("semantic_scholar") or [])
    return "\n".join(lines) if lines else "(none)"
