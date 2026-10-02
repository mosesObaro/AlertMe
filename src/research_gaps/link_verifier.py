"""Link verification and recovery engine with persistent caching."""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from src.research_gaps.models import (
    LinkVerificationResult,
    LinkStatus,
    ExtractedPaperInfo,
    ResearchProblem,
    SupervisorMatch
)
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'


class LinkVerifier:
    """Validates external academic and researcher URLs, with recovery and caching."""

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

    def _is_malformed_url(self, url: str) -> bool:
        """Check if URL is structurally malformed."""
        try:
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
        if not result.last_verified:
            return False
        try:
            lv = result.last_verified
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
                link_status=LinkStatus.BROKEN,
                http_status=0,
                last_verified=now_str,
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
                            link_status=LinkStatus.BROKEN,
                            http_status=404,
                            last_verified=now_str,
                        )
                    return LinkVerificationResult(
                        url=url,
                        canonical_url=final_url if redirected else url,
                        link_status=LinkStatus.REDIRECTED if redirected else LinkStatus.VALID,
                        http_status=response.status_code,
                        redirect_target=final_url if redirected else "",
                        last_verified=now_str,
                    )
                elif response.status_code in [404, 410]:
                    return LinkVerificationResult(
                        url=url,
                        link_status=LinkStatus.BROKEN,
                        http_status=response.status_code,
                        last_verified=now_str,
                    )
                else:
                    return LinkVerificationResult(
                        url=url,
                        link_status=LinkStatus.UNKNOWN,
                        http_status=response.status_code,
                        last_verified=now_str,
                    )

            except requests.exceptions.Timeout:
                if attempt == self.retry_attempts:
                    return LinkVerificationResult(
                        url=url,
                        link_status=LinkStatus.UNREACHABLE,
                        http_status=0,
                        last_verified=now_str,
                    )
            except requests.exceptions.RequestException:
                if attempt == self.retry_attempts:
                    return LinkVerificationResult(
                        url=url,
                        link_status=LinkStatus.UNREACHABLE,
                        http_status=0,
                        last_verified=now_str,
                    )

            time.sleep(self.rate_limit_delay)

        return LinkVerificationResult(
            url=url,
            link_status=LinkStatus.UNKNOWN,
            http_status=0,
            last_verified=now_str,
        )

    def verify_url(self, url: str) -> LinkVerificationResult:
        """Verify a single URL, using cache if valid."""
        if not url:
            return LinkVerificationResult(
                url="",
                link_status=LinkStatus.BROKEN,
                http_status=0,
                last_verified=datetime.now(timezone.utc).isoformat(),
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

    def _find_canonical_url(self, paper_info: ExtractedPaperInfo) -> Optional[str]:
        """Construct canonical DOI URL if available."""
        if paper_info.doi:
            clean_doi = paper_info.doi.strip()
            if not clean_doi.startswith("http"):
                return f"https://doi.org/{clean_doi}"
            return clean_doi
        return None

    def _recover_broken_link(self, url: str, metadata: Dict) -> Optional[str]:
        """Attempt to recover broken link using metadata (DOI or arXiv)."""
        doi = metadata.get("doi")
        if doi:
            canonical_doi = f"https://doi.org/{doi}"
            res = self.verify_url(canonical_doi)
            if res.link_status in [LinkStatus.VALID, LinkStatus.REDIRECTED]:
                return canonical_doi

        arxiv_id = metadata.get("arxiv_id")
        if arxiv_id:
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            res = self.verify_url(arxiv_url)
            if res.link_status in [LinkStatus.VALID, LinkStatus.REDIRECTED]:
                return arxiv_url

        return None

    def verify_all_links(
        self,
        papers: List[ExtractedPaperInfo],
        problems: List[ResearchProblem],
        supervisors: List[SupervisorMatch],
    ) -> Dict[str, LinkVerificationResult]:
        """Verify all external links across papers, problems, and supervisors."""
        all_urls = set()

        for paper in papers:
            if paper.url:
                all_urls.add(paper.url)
            if paper.doi:
                all_urls.add(f"https://doi.org/{paper.doi}")

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
