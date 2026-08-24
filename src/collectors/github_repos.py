"""GitHub repository and benchmark collector."""

import os
from typing import List
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubRepoCollector(BaseCollector):
    """Monitors newly created/trending open source edge computing benchmarks and frameworks."""

    def __init__(
        self,
        name: str = "GitHub Edge Repos & Benchmarks",
        query: str = "edge-computing OR edge-ai OR mobile-edge-computing OR tinyml benchmark",
        max_results: int = 15,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.query = query
        self.max_results = max_results

    def fetch(self) -> List[ResearchItem]:
        headers = {}
        gh_token = os.environ.get("GITHUB_TOKEN")
        if gh_token:
            headers["Authorization"] = f"token {gh_token}"

        params = {
            "q": self.query,
            "sort": "updated",
            "order": "desc",
            "per_page": min(self.max_results, 30)
        }

        response = self.requester.get(GITHUB_SEARCH_URL, params=params, headers=headers)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch GitHub repositories. Status: {getattr(response, 'status_code', 'None')}")
            return []

        data = response.json()
        repos = data.get("items", [])
        items: List[ResearchItem] = []

        for repo in repos:
            full_name = repo.get("full_name", "")
            if not full_name:
                continue

            description = repo.get("description") or "Open source edge computing repository."
            html_url = repo.get("html_url", "")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            updated_at = (repo.get("updated_at") or "")[:10]
            owner = repo.get("owner", {}).get("login", "")

            # Topic tags
            topics = repo.get("topics", [])

            item = ResearchItem(
                title=f"[Code/Benchmark] {full_name} (★ {stars})",
                url=html_url,
                source="GitHub Open Source",
                source_tier=self.tier,
                item_type=ItemType.BENCHMARK_CODE.value,
                authors=[owner],
                publication_date=updated_at,
                abstract=f"{description} (Stars: {stars}, Forks: {forks})",
                venue="GitHub",
                topics=topics,
                raw_metadata={"stars": stars, "forks": forks}
            )
            items.append(item)

        return items
