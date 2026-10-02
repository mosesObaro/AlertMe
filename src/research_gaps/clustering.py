"""Clusters related research problems into research gap clusters."""

import difflib
import re
from typing import List, Dict, Set
from collections import Counter
from datetime import datetime

from src.research_gaps.models import ResearchProblem, ResearchGapCluster, ExtractedPaperInfo
from src.utils.logger import logger


class ProblemClusterer:
    """Clusters related research problems into research gap clusters."""

    def __init__(self, similarity_threshold: float = 0.55, min_cluster_size: int = 2):
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size

    def _compute_similarity(self, p1: ResearchProblem, p2: ResearchProblem) -> float:
        """Compute similarity using keyword overlap combined with problem statement text similarity."""
        def get_tokens(p: ResearchProblem) -> Set[str]:
            tokens = set()
            if p.supervisor_keywords:
                for kw in p.supervisor_keywords:
                    tokens.update(re.findall(r'\w+', kw.lower()))
            if p.research_area:
                tokens.update(re.findall(r'\w+', p.research_area.lower()))
            return tokens

        t1 = get_tokens(p1)
        t2 = get_tokens(p2)

        jaccard = 0.0
        if t1 or t2:
            intersection = len(t1.intersection(t2))
            union = len(t1.union(t2))
            jaccard = intersection / union if union > 0 else 0.0

        seq_match = 0.0
        if p1.problem_statement and p2.problem_statement:
            seq_match = difflib.SequenceMatcher(None, p1.problem_statement.lower(), p2.problem_statement.lower()).ratio()

        # Weighted combination: 40% keywords/area, 60% problem statement text
        return (jaccard * 0.4) + (seq_match * 0.6)

    def _assign_cluster_name(self, problems: List[ResearchProblem]) -> str:
        """Generate cluster name from most common keywords."""
        words = []
        for p in problems:
            if p.supervisor_keywords:
                words.extend([kw.lower() for kw in p.supervisor_keywords])
            if p.research_area:
                words.extend(re.findall(r'\w+', p.research_area.lower()))

        # Filter out common stop words
        stop_words = {'and', 'the', 'of', 'in', 'for', 'with', 'a', 'an', 'to', 'on', 'at', 'by', 'is'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        if not filtered_words:
            return "General Research Gap"

        counts = Counter(filtered_words)
        top_words = [word.capitalize() for word, _ in counts.most_common(2)]
        return " & ".join(top_words) if len(top_words) > 1 else top_words[0]

    def _identify_recurring_limitations(self, problems: List[ResearchProblem]) -> List[str]:
        """Aggregate known_limitations from grouped problems, return unique items sorted by frequency."""
        all_limitations = []
        for p in problems:
            all_limitations.extend(p.known_limitations)

        counts = Counter(all_limitations)
        return [lim for lim, _ in counts.most_common()]

    def _identify_open_questions(self, problems: List[ResearchProblem]) -> List[str]:
        """Aggregate unresolved_questions from grouped problems, return unique items sorted by frequency."""
        all_questions = []
        for p in problems:
            all_questions.extend(p.unresolved_questions)

        counts = Counter(all_questions)
        return [q for q, _ in counts.most_common()]

    def _build_cluster(self, group: List[ResearchProblem], papers: List[ExtractedPaperInfo]) -> ResearchGapCluster:
        """Construct a ResearchGapCluster from a group of related problems."""
        name = self._assign_cluster_name(group)
        area_counts = Counter(p.research_area for p in group if p.research_area)
        research_area = area_counts.most_common(1)[0][0] if area_counts else "Edge Computing"

        description = f"Cluster of research gaps around {name} in {research_area}."

        paper_ids = set()
        for p in group:
            paper_ids.update(p.supporting_papers)
        supporting_papers = sorted(list(paper_ids))
        supporting_problems = [p.id for p in group if p.id]

        recurring_limitations = self._identify_recurring_limitations(group)
        open_questions = self._identify_open_questions(group)

        frequency = sum(p.frequency for p in group)
        now = datetime.now().isoformat()

        return ResearchGapCluster(
            name=name,
            description=description,
            research_area=research_area,
            supporting_papers=supporting_papers,
            supporting_problems=supporting_problems,
            recurring_limitations=recurring_limitations,
            open_questions=open_questions,
            frequency=frequency,
            first_seen=now,
            last_seen=now,
        )

    def cluster_problems(self, problems: List[ResearchProblem], papers: List[ExtractedPaperInfo]) -> List[ResearchGapCluster]:
        """Cluster problems using agglomerative union-find approach."""
        n = len(problems)
        parent = list(range(n))

        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_j] = root_i

        for i in range(n):
            for j in range(i + 1, n):
                sim = self._compute_similarity(problems[i], problems[j])
                if sim >= self.similarity_threshold:
                    union(i, j)

        groups: Dict[int, List[ResearchProblem]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(problems[i])

        clusters = []
        for root, group in groups.items():
            if len(group) >= self.min_cluster_size:
                cluster = self._build_cluster(group, papers)
                clusters.append(cluster)

        return clusters

    def update_clusters(self, existing_clusters: List[ResearchGapCluster], new_clusters: List[ResearchGapCluster]) -> List[ResearchGapCluster]:
        """Merge new clusters into existing, updating frequency, last_seen, and supporting data."""
        merged_clusters = []
        used_new = set()

        for existing in existing_clusters:
            for j, new_c in enumerate(new_clusters):
                if j in used_new:
                    continue

                # Match by cluster_id, exact name, or text similarity
                is_match = (
                    (existing.cluster_id and existing.cluster_id == new_c.cluster_id)
                    or (existing.name and existing.name.lower() == new_c.name.lower())
                )
                if not is_match and existing.description and new_c.description:
                    sim = difflib.SequenceMatcher(None, existing.description.lower(), new_c.description.lower()).ratio()
                    is_match = sim >= self.similarity_threshold

                if is_match:
                    existing.frequency += new_c.frequency
                    existing.last_seen = new_c.last_seen
                    existing.supporting_papers = list(set(existing.supporting_papers + new_c.supporting_papers))
                    existing.supporting_problems = list(set(existing.supporting_problems + new_c.supporting_problems))
                    
                    def _str_list(lst):
                        out = []
                        for item in lst:
                            if isinstance(item, (list, tuple)):
                                out.append(str(item[0]))
                            else:
                                out.append(str(item))
                        return list(dict.fromkeys(out))

                    existing.recurring_limitations = _str_list(existing.recurring_limitations + new_c.recurring_limitations)
                    existing.open_questions = _str_list(existing.open_questions + new_c.open_questions)
                    used_new.add(j)

            merged_clusters.append(existing)

        for j, new_c in enumerate(new_clusters):
            if j not in used_new:
                merged_clusters.append(new_c)

        return merged_clusters
