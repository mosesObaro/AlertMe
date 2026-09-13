"""
Research Ideas Matcher for Hong Kong PhD Supervisor Intelligence.
Bridges candidate ideas in Sheet 7 (Research Ideas) with prospective Hong Kong professors
and generates supervisor-specific extension recommendations.
"""

from typing import List, Dict, Any
from .models import ResearcherProfile

class IdeasMatcher:
    """Correlates user's research idea bank with target Hong Kong supervisors."""

    IDEA_TOPIC_ALIGNMENTS = {
        "Federated Edge Intelligence": {
            "keywords": ["federated learning", "non-iid", "client drift", "distributed ai"],
            "target_supervisors": ["polyu_guo_song", "hkust_wang_wei", "hku_wu_chuan"],
            "potential_extension": "Integrate client hardware heterogeneity profiling into adaptive local epoch tuning."
        },
        "Computation Offloading & Mobility": {
            "keywords": ["v2x", "connected autonomous vehicles", "handover", "rsu", "offloading"],
            "target_supervisors": ["cityu_wang_jianping", "cuhk_lui_john", "polyu_cao_jiannong"],
            "potential_extension": "Combine spatial-temporal trajectory forecasting with roadside server queue backlog states."
        },
        "Edge Serverless & Cold Starts": {
            "keywords": ["serverless", "faas", "cold-start", "webassembly", "wasm", "microservices"],
            "target_supervisors": ["hkust_wang_lin", "polyu_cao_jiannong", "hku_wu_chuan"],
            "potential_extension": "Evaluate sub-millisecond WebAssembly sandbox instantiation across multi-tenant edge nodes."
        },
        "Green & Sustainable Edge Computing": {
            "keywords": ["energy harvesting", "solar", "early-exit", "green edge", "carbon-aware"],
            "target_supervisors": ["cuhk_chen_minghua", "polyu_guo_song"],
            "potential_extension": "Formulate dynamic early-exit neural depth scaling subject to real-time solar irradiance bounds."
        }
    }

    @classmethod
    def match_supervisors_for_idea(
        cls,
        idea_title: str,
        researchers: List[ResearcherProfile]
    ) -> List[Dict[str, Any]]:
        """
        Finds the strongest supervisor candidates for a specific research idea
        and generates tailored alignment recommendations.
        """
        matches = []
        info = cls.IDEA_TOPIC_ALIGNMENTS.get(idea_title)
        
        if not info:
            # Fallback search by keyword
            title_lower = idea_title.lower()
            for cand in researchers:
                interests_lower = " ".join(cand.research_interests).lower()
                if any(w in interests_lower for w in title_lower.split()):
                    matches.append({
                        "professor": cand.name,
                        "university": cand.university,
                        "alignment_score": cand.alignment_score,
                        "suggested_extension": f"Explore alignment with {cand.name}'s active projects ({cand.current_projects[0] if cand.current_projects else 'Edge AI'})."
                    })
            return matches

        target_ids = info["target_supervisors"]
        for cand in researchers:
            if cand.researcher_id in target_ids:
                matches.append({
                    "professor": cand.name,
                    "university": cand.university,
                    "alignment_score": cand.alignment_score,
                    "suggested_extension": info["potential_extension"],
                    "primary_paper": cand.publications[0].title if cand.publications else "Key Publication"
                })

        return matches
