"""Link verification and recovery engine with persistent caching and DOI handle verification."""

import time
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from src.research_gaps.models import (
    LinkVerificationResult,
    LinkStatus,
    ExtractedPaperInfo,
    ResearchProblem,
    SupervisorMatch,
    _normalize_doi
)
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'
DOI_HANDLE_API = "https://doi.org/api/handles/"


class LinkVerifier:
    """Validates external academic and researcher URLs, with recovery, DOI API handle checks, and caching."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        timeout: int = 10,
        rate_limit_delay: float = 0.5,
        retry_attempts: int = 2
    ):
        self.cache_dir = cache_dir or (DATA_DIR / 'link_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'link_cache.json'
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AlertMeResearchAssistant/1.0; +https://github.com/AlertMe)'
        })
        self.cache = self.load_cache()

    def normalize_doi(self, raw_doi: Optional[str]) -> Optional[str]:
        """Normalize DOI string or return None if invalid/doi_hash."""
        return _normalize_doi(raw_doi)

    def build_doi_url(self, clean_doi: str) -> str:
        """Percent-encode DOI path for canonical https://doi.org/<doi>."""
        if not clean_doi:
            return ""
        encoded = urllib.parse.quote(clean_doi, safe='/')
        return f"https://doi.org/{encoded}"

    def _find_canonical_url(self, paper: Any) -> str:
        """Find canonical URL for a paper, prioritizing normalized DOI URL."""
        doi = getattr(paper, 'doi', None) or (paper.get('doi') if isinstance(paper, dict) else None)
        clean_doi = self.normalize_doi(doi)
        if clean_doi:
            return self.build_doi_url(clean_doi)
        url = getattr(paper, 'url', None) or (paper.get('url') if isinstance(paper, dict) else "")
        return url or ""

    def verify_doi(self, raw_doi: Optional[str]) -> LinkVerificationResult:
        """Verifies DOI using the official DOI REST API (GET https://doi.org/api/handles/<doi>)."""
        now_str = datetime.now(timezone.utc).isoformat()
        clean_doi = self.normalize_doi(raw_doi)

        if not clean_doi:
            return LinkVerificationResult(
                url=raw_doi or "",
                link_url="",
                link_type="doi",
                link_status=LinkStatus.NONE if not raw_doi else LinkStatus.DEAD,
                http_status=0,
                last_verified=now_str,
                verified_at=now_str,
            )

        doi_url = self.build_doi_url(clean_doi)

        if doi_url in self.cache and self._is_cache_valid(self.cache[doi_url]):
            return self.cache[doi_url]

        # Query DOI REST API
        try:
            quoted_handle = urllib.parse.quote(clean_doi, safe='/')
            resp = self.session.get(f"{DOI_HANDLE_API}{quoted_handle}", timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                code = data.get("responseCode")
                if code == 1:
                    # Registered! Follow redirect once to destination
                    try:
                        red_resp = self.session.get(doi_url, timeout=self.timeout, allow_redirects=True)
                        dest_url = red_resp.url if red_resp.history else doi_url
                        if red_resp.status_code in (200, 301, 302, 307, 308):
                            status = LinkStatus.VERIFIED
                        elif red_resp.status_code in (403, 429, 999):
                            status = LinkStatus.BLOCKED
                        elif red_resp.status_code in (404, 410):
                            status = LinkStatus.DEAD
                        else:
                            status = LinkStatus.VERIFIED
                        res = LinkVerificationResult(
                            url=doi_url,
                            link_url=doi_url,
                            link_type="doi",
                            link_status=status,
                            canonical_url=dest_url,
                            http_status=red_resp.status_code,
                            last_verified=now_str,
                            verified_at=now_str,
                        )
                    except Exception:
                        res = LinkVerificationResult(
                            url=doi_url,
                            link_url=doi_url,
                            link_type="doi",
                            link_status=LinkStatus.VERIFIED,
                            http_status=200,
                            last_verified=now_str,
                            verified_at=now_str,
                        )
                    self.cache[doi_url] = res
                    self.save_cache(self.cache)
                    return res
                elif code == 100:
                    res = LinkVerificationResult(
                        url=doi_url,
                        link_url=doi_url,
                        link_type="doi",
                        link_status=LinkStatus.DEAD,
                        http_status=404,
                        last_verified=now_str,
                        verified_at=now_str,
                    )
                    self.cache[doi_url] = res
                    self.save_cache(self.cache)
                    return res
        except requests.exceptions.Timeout:
            res = LinkVerificationResult(
                url=doi_url,
                link_url=doi_url,
                link_type="doi",
                link_status=LinkStatus.BLOCKED,
                http_status=0,
                last_verified=now_str,
                verified_at=now_str,
            )
            self.cache[doi_url] = res
            self.save_cache(self.cache)
            return res
        except Exception:
            pass

        res = LinkVerificationResult(
            url=doi_url,
            link_url=doi_url,
            link_type="doi",
            link_status=LinkStatus.BLOCKED,
            http_status=0,
            last_verified=now_str,
            verified_at=now_str,
        )
        self.cache[doi_url] = res
        self.save_cache(self.cache)
        return res

    def select_best_link(self, paper_meta: Dict[str, Any]) -> LinkVerificationResult:
        """Selects the first working link according to strict fallback hierarchy:
        1. Verified DOI (https://doi.org/<doi>)
        2. OpenAlex open-access URL or landing page
        3. arXiv URL (https://arxiv.org/abs/<arxiv_id>)
        4. Semantic Scholar URL (https://www.semanticscholar.org/paper/<s2_id>)
        5. OpenAlex work page (https://openalex.org/<work_id>)

        Returns LinkVerificationResult with link_status: 'verified', 'blocked', 'dead', or 'none'.
        """
        now_str = datetime.now(timezone.utc).isoformat()

        # Candidates in fallback order
        candidates: List[Tuple[str, str, str]] = []  # (raw_value, type, constructed_url)

        # 1. DOI
        doi_raw = paper_meta.get("doi")
        clean_doi = self.normalize_doi(doi_raw)
        if clean_doi:
            candidates.append((clean_doi, "doi", self.build_doi_url(clean_doi)))

        # 2. OpenAlex Open Access or landing page
        oa_url = paper_meta.get("oa_url") or paper_meta.get("open_access_url") or paper_meta.get("url")
        if oa_url and not "doi_" in str(oa_url) and not "openalex.org/W" in str(oa_url) and not "arxiv.org" in str(oa_url):
            candidates.append((oa_url, "openalex_oa", oa_url))

        # 3. arXiv
        arxiv_id = paper_meta.get("arxiv_id")
        if arxiv_id:
            clean_arxiv = re.sub(r'^(arxiv:\s*|https?://arxiv\.org/(abs|pdf)/)', '', str(arxiv_id), flags=re.IGNORECASE).strip()
            if clean_arxiv:
                candidates.append((clean_arxiv, "arxiv", f"https://arxiv.org/abs/{clean_arxiv}"))

        # 4. Semantic Scholar
        s2_url = paper_meta.get("semantic_scholar_url") or paper_meta.get("s2_url")
        s2_id = paper_meta.get("paper_id") if "paper_id" in paper_meta and not str(paper_meta["paper_id"]).startswith("paper_") else None
        if s2_url and "semanticscholar.org" in str(s2_url):
            candidates.append((s2_url, "semantic_scholar", s2_url))
        elif s2_id:
            candidates.append((s2_id, "semantic_scholar", f"https://www.semanticscholar.org/paper/{s2_id}"))

        # 5. OpenAlex Work Page
        openalex_id = paper_meta.get("openalex_id") or paper_meta.get("openalex_author_id")
        if openalex_id and str(openalex_id).startswith("W"):
            candidates.append((openalex_id, "openalex_work", f"https://openalex.org/{openalex_id}"))

        # Test candidate links in fallback order
        for val, link_type, url in candidates:
            if not url or "doi_" in url or "paper_" in url:
                continue
            if link_type == "doi":
                res = self.verify_doi(val)
            else:
                res = self.verify_url(url)
                res.link_type = link_type

            if res.link_status in (LinkStatus.VERIFIED, LinkStatus.BLOCKED):
                res.link_type = link_type
                res.link_url = url
                return res

        # If all candidates fail or none exist
        return LinkVerificationResult(
            url="",
            link_url="",
            link_type="none",
            link_status=LinkStatus.DEAD if candidates else LinkStatus.NONE,
            http_status=0,
            last_verified=now_str,
            verified_at=now_str,
        )

    def _is_malformed_url(self, url: str) -> bool:
        """Check if URL is structurally malformed."""
        try:
            if not url or "doi_" in url or "paper_" in url:
                return True
            parsed = urlparse(url)
            return not (parsed.scheme in ['http', 'https'] and parsed.netloc)
        except Exception:
            return True

    def _is_soft_404(self, response: requests.Response) -> bool:
        """Detect soft-404 error pages that return HTTP 200."""
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            text = response.text.lower()
            return any(phrase in text for phrase in ['page not found', 'article not found', '404 not found'])
        return False

    def load_cache(self) -> Dict[str, LinkVerificationResult]:
        """Load cached link verification results from JSON."""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: LinkVerificationResult.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load link cache: {e}")
            return {}

    def save_cache(self, cache: Dict[str, LinkVerificationResult]) -> None:
        """Atomically persist verification cache to disk."""
        try:
            data = {k: v.to_dict() for k, v in cache.items()}
            _atomic_write_json(self.cache_file, data)
        except Exception as e:
            logger.error(f"Failed to save link cache: {e}")

    def _is_cache_valid(self, result: LinkVerificationResult, ttl_hours: int = 168) -> bool:
        """Check if cached verification is still fresh (default 7 days)."""
        lv = result.verified_at or result.last_verified
        if not lv:
            return False
        try:
            if isinstance(lv, str):
                lv_dt = datetime.fromisoformat(lv.replace("Z", "+00:00"))
            else:
                lv_dt = lv
            if lv_dt.tzinfo is None:
                lv_dt = lv_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - lv_dt).total_seconds() < ttl_hours * 3600
        except Exception:
            return False

    def _check_url(self, url: str) -> LinkVerificationResult:
        """Perform HTTP check on a URL with redirect detection."""
        now_str = datetime.now(timezone.utc).isoformat()

        if self._is_malformed_url(url):
            return LinkVerificationResult(
                url=url,
                link_url="",
                link_status=LinkStatus.DEAD,
                http_status=0,
                last_verified=now_str,
                verified_at=now_str,
            )

        for attempt in range(self.retry_attempts + 1):
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                redirected = bool(response.history)
                final_url = response.url if redirected else url

                if response.status_code == 200:
                    if self._is_soft_404(response):
                        return LinkVerificationResult(
                            url=url,
                            link_url=url,
                            link_status=LinkStatus.DEAD,
                            http_status=404,
                            last_verified=now_str,
                            verified_at=now_str,
                        )
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        canonical_url=final_url if redirected else url,
                        link_status=LinkStatus.VERIFIED,
                        http_status=response.status_code,
                        redirect_target=final_url if redirected else "",
                        last_verified=now_str,
                        verified_at=now_str,
                    )
                elif response.status_code in [403, 429, 999]:
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        link_status=LinkStatus.BLOCKED,
                        http_status=response.status_code,
                        last_verified=now_str,
                        verified_at=now_str,
                    )
                elif response.status_code in [404, 410]:
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        link_status=LinkStatus.DEAD,
                        http_status=response.status_code,
                        last_verified=now_str,
                        verified_at=now_str,
                    )
                else:
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        link_status=LinkStatus.VERIFIED if response.status_code < 400 else LinkStatus.BLOCKED,
                        http_status=response.status_code,
                        last_verified=now_str,
                        verified_at=now_str,
                    )

            except requests.exceptions.Timeout:
                if attempt == self.retry_attempts:
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        link_status=LinkStatus.BLOCKED,
                        http_status=0,
                        last_verified=now_str,
                        verified_at=now_str,
                    )
            except requests.exceptions.RequestException:
                if attempt == self.retry_attempts:
                    return LinkVerificationResult(
                        url=url,
                        link_url=url,
                        link_status=LinkStatus.BLOCKED,
                        http_status=0,
                        last_verified=now_str,
                        verified_at=now_str,
                    )

            time.sleep(self.rate_limit_delay)

        return LinkVerificationResult(
            url=url,
            link_url=url,
            link_status=LinkStatus.NONE,
            http_status=0,
            last_verified=now_str,
            verified_at=now_str,
        )

    def verify_url(self, url: str) -> LinkVerificationResult:
        """Verify a single URL, using cache if valid."""
        if not url or "doi_" in url or "paper_" in url:
            return LinkVerificationResult(
                url="",
                link_url="",
                link_status=LinkStatus.DEAD,
                http_status=0,
                last_verified=datetime.now(timezone.utc).isoformat(),
                verified_at=datetime.now(timezone.utc).isoformat(),
            )

        if url in self.cache and self._is_cache_valid(self.cache[url]):
            return self.cache[url]

        result = self._check_url(url)
        self.cache[url] = result
        self.save_cache(self.cache)
        return result

    def verify_urls(self, urls: List[str]) -> List[LinkVerificationResult]:
        """Verify a batch of URLs with rate limiting."""
        results = []
        for url in urls:
            results.append(self.verify_url(url))
        return results

    def verify_all_links(
        self,
        papers: List[ExtractedPaperInfo],
        problems: List[ResearchProblem],
        supervisors: List[SupervisorMatch],
    ) -> Dict[str, LinkVerificationResult]:
        """Verify all external links across papers, problems, and supervisors."""
        all_urls = set()

        for paper in papers:
            if paper.url and not "doi_" in paper.url:
                all_urls.add(paper.url)
            clean_doi = self.normalize_doi(paper.doi)
            if clean_doi:
                all_urls.add(self.build_doi_url(clean_doi))

        for supervisor in supervisors:
            if supervisor.profile_url:
                all_urls.add(supervisor.profile_url)
            if supervisor.google_scholar_url:
                all_urls.add(supervisor.google_scholar_url)
            if supervisor.semantic_scholar_url:
                all_urls.add(supervisor.semantic_scholar_url)

        logger.info(f"Verifying {len(all_urls)} unique external links")
        results = {}
        for url in all_urls:
            results[url] = self.verify_url(url)

        return results
