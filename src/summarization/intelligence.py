"""Paper intelligence and structured research analysis engine."""

import os
import re
import json
from typing import Optional, Dict, Any
from src.models import ResearchItem, PaperIntelligence
from src.utils.logger import logger
from src.utils.rate_limiter import PoliteRequester


class IntelligenceEngine:
    """Generates structured academic analysis for high-priority papers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ai_enabled = self.config.get("enabled", False)
        self.ai_provider = self.config.get("provider", "gemini")
        self.api_key_env = self.config.get("api_key_env", "LLM_API_KEY")
        self.api_key = os.environ.get(self.api_key_env) or os.environ.get("GEMINI_API_KEY")
        self.requester = PoliteRequester()

    def analyze(self, item: ResearchItem) -> PaperIntelligence:
        """Analyzes a research item, using AI if configured and available, or deterministic rules."""
        if self.ai_enabled and self.api_key:
            try:
                ai_intel = self._analyze_with_ai(item)
                if ai_intel:
                    return ai_intel
            except Exception as e:
                logger.warning(f"AI summarization failed for '{item.title}': {e}. Falling back to deterministic analysis.")

        return self._analyze_deterministic(item)

    def _analyze_deterministic(self, item: ResearchItem) -> PaperIntelligence:
        """Extracts structured research intelligence using deterministic NLP heuristics."""
        abstract = item.abstract or ""
        title = item.title

        if not abstract:
            return PaperIntelligence(
                why_it_matters=f"Addresses key paradigms in {', '.join(item.topics[:2]) if item.topics else 'Edge Computing'}.",
                research_problem="Not determinable from available metadata.",
                methodology="Not determinable from available metadata.",
                key_contribution=f"Published in {item.venue or item.source}.",
                potential_gap="Potential research direction — requires validation through deeper literature review.",
                relevance_to_phd=f"{item.score.final_score if item.score else 8.0}/10",
                is_ai_generated=False
            )

        sentences = [s.strip() for s in re.split(r'\. |\.\n', abstract) if s.strip()]

        # 1. Research Problem Heuristic
        problem = "Not determinable from available metadata."
        problem_patterns = [
            r'(however|challenge|problem|limitation|bottleneck|issue|trade-off|drawback)',
            r'(how to|difficult to|lack of|insufficient)'
        ]
        for s in sentences:
            if any(re.search(pat, s, re.IGNORECASE) for pat in problem_patterns):
                problem = s
                break

        # 2. Methodology Heuristic
        methodology = "Not determinable from available metadata."
        method_patterns = [
            r'(we propose|we design|we introduce|we develop|we present|we formulate|algorithm|framework|architecture|model)',
            r'(reinforcement learning|deep learning|optimization|heuristic|game theory|lyapunov|federated)'
        ]
        for s in sentences:
            if any(re.search(pat, s, re.IGNORECASE) for pat in method_patterns):
                methodology = s
                break

        # 3. Key Contribution Heuristic
        contribution = "Not determinable from available metadata."
        contrib_patterns = [
            r'(experimental results|simulation results|show that|demonstrates|outperforms|achieves|reduces|improves|evaluation)',
            r'(compared to|superior to|findings indicate)'
        ]
        for s in sentences:
            if any(re.search(pat, s, re.IGNORECASE) for pat in contrib_patterns):
                contribution = s
                break
        if contribution == "Not determinable from available metadata." and len(sentences) > 0:
            contribution = sentences[-1]

        # 4. Why this matters
        why_it_matters = (
            f"This work investigates {' and '.join(item.topics[:2]) if item.topics else 'Edge Intelligence architecture'}. "
            f"It targets key performance dimensions relevant to Edge Computing PhD preparation."
        )

        # 5. Potential Gap Heuristic
        potential_gap = (
            "Potential research direction — requires validation through deeper literature review: "
            "Examine whether the proposed methodology scales under heterogeneous, resource-constrained edge devices "
            "and dynamic wireless channel conditions."
        )

        rating = f"{item.score.final_score if item.score else 8.5}/10"

        return PaperIntelligence(
            why_it_matters=why_it_matters,
            research_problem=problem,
            methodology=methodology,
            key_contribution=contribution,
            potential_gap=potential_gap,
            relevance_to_phd=rating,
            is_ai_generated=False
        )

    def _analyze_with_ai(self, item: ResearchItem) -> Optional[PaperIntelligence]:
        """Calls Google Gemini API or compatible LLM endpoint for structured paper analysis."""
        prompt = f"""You are an expert academic research assistant preparing for a PhD in Edge Computing & Distributed Systems.
Analyze this academic publication metadata and return a strict JSON object.

Title: {item.title}
Venue: {item.venue}
Abstract: {item.abstract}

JSON Schema:
{{
  "why_it_matters": "1-2 sentences on why this paper is critical for Edge Computing / Edge AI research.",
  "research_problem": "Precise research problem or bottleneck being addressed.",
  "methodology": "The technical approach, algorithm, or system architecture used.",
  "key_contribution": "The main theoretical or empirical contribution and performance result.",
  "potential_gap": "Potential research direction — requires validation through deeper literature review: [Identify realistic limitation or unexplored extension in heterogeneous real-world edge settings].",
  "relevance_to_phd": "{item.score.final_score if item.score else 8.5}/10"
}}

Respond ONLY with valid JSON."""

        if self.ai_provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            res = self.requester.session.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return PaperIntelligence(
                    why_it_matters=parsed.get("why_it_matters", ""),
                    research_problem=parsed.get("research_problem", ""),
                    methodology=parsed.get("methodology", ""),
                    key_contribution=parsed.get("key_contribution", ""),
                    potential_gap=parsed.get("potential_gap", ""),
                    relevance_to_phd=parsed.get("relevance_to_phd", "9/10"),
                    is_ai_generated=True
                )

        return None
