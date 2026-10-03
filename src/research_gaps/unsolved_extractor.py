"""Unsolved problem extractor and clusterer (Step 2).

Extracts limitation/future-work sentences with cue lexicons, cleans discourse markers,
prefixes short paper titles, clusters using TF-IDF cosine + keyphrase Jaccard,
and tests for existing solutions on OpenAlex/Semantic Scholar.
"""

import re
import math
import json
import hashlib
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from src.research_gaps.models import (
    EvidenceClaim,
    UnsolvedProblemCluster,
    ProfessorCorpus,
    CorpusPaper,
)
from src.utils.rate_limiter import PoliteRequester
from src.utils.logger import logger

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "research_gaps.yaml"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would",
    "you", "your", "yours", "yourself", "yourselves", "paper", "proposed", "present", "system", "work"
}

DISCOURSE_MARKERS_RE = re.compile(
    r'^(however|furthermore|in addition|moreover|nevertheless|consequently|therefore|thus|despite this|on the other hand|meanwhile|specifically|in particular)[,\s]+',
    re.IGNORECASE
)

UNRESOLVED_REF_RE = re.compile(
    r'^(the|this|these|our)\s+(framework|architecture|scheme|approach|system|model|method|algorithm|protocol|solution|design)',
    re.IGNORECASE
)


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase words excluding stopwords."""
    return [w for w in re.findall(r'[a-zA-Z]{3,}', text.lower()) if w not in STOP_WORDS]


def extract_key_phrases(text: str, top_k: int = 5) -> List[str]:
    """Extracts top N-gram keyphrases from text."""
    words = tokenize(text)
    if not words:
        return []
    ngrams = []
    for n in range(1, 4):
        for i in range(len(words) - n + 1):
            ngrams.append(" ".join(words[i:i+n]))
    counts = Counter(ngrams)
    return [phrase for phrase, _ in counts.most_common(top_k)]


def tfidf_cosine_similarity(text1: str, text2: str, corpus_texts: Optional[List[str]] = None) -> float:
    """Computes TF-IDF cosine similarity between two text strings."""
    words1 = tokenize(text1)
    words2 = tokenize(text2)
    if not words1 or not words2:
        return 0.0

    all_docs = corpus_texts or [text1, text2]
    n_docs = len(all_docs)
    df = Counter()
    for doc in all_docs:
        df.update(set(tokenize(doc)))

    def get_vec(words):
        tf = Counter(words)
        vec = {}
        for w, count in tf.items():
            idf = math.log((n_docs + 1) / (df.get(w, 0) + 1)) + 1.0
            vec[w] = (count / len(words)) * idf
        return vec

    vec1 = get_vec(words1)
    vec2 = get_vec(words2)

    dot_product = sum(vec1[w] * vec2[w] for w in vec1 if w in vec2)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def keyphrase_jaccard(phrases1: List[str], phrases2: List[str]) -> float:
    """Computes Jaccard similarity between two keyphrase lists."""
    set1 = set(phrases1)
    set2 = set(phrases2)
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))


def clean_sentence(sentence: str, paper_short_title: str = "") -> str:
    """Strips leading discourse markers and prefixes short title for unresolved references."""
    cleaned = DISCOURSE_MARKERS_RE.sub('', sentence.strip())
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    if paper_short_title and UNRESOLVED_REF_RE.match(cleaned):
        cleaned = f"[{paper_short_title}] {cleaned}"
    return cleaned


class UnsolvedProblemExtractor:
    """Extracts, clusters, and verifies unsolved research problems (Step 2)."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        requester: Optional[PoliteRequester] = None,
    ):
        self.config = config or self._load_config()
        self.requester = requester or PoliteRequester()

        unsolved_cfg = self.config.get("unsolved_problems", {})
        self.cues = unsolved_cfg.get("cue_lexicon", {
            "limitations": ["limitation", "drawback", "bottleneck", "shortcoming", "does not consider", "fails to", "inefficient when"],
            "future_work": ["future work", "remains open", "yet to", "unexplored", "promising direction", "further research"],
            "open_challenge": ["open challenge", "key problem", "major issue", "unresolved"],
        })
        self.section_weights = unsolved_cfg.get("section_weights", {
            "limitations": 2.0,
            "future_work": 2.0,
            "conclusion": 1.5,
            "abstract": 1.0,
        })
        self.clustering_threshold = float(unsolved_cfg.get("clustering_threshold", 0.45))
        self.solution_cues = unsolved_cfg.get("solution_cues", [
            "we propose", "we address", "we solve", "mitigate", "overcome", "present a novel"
        ])
        self.status_thresholds = unsolved_cfg.get("status_thresholds", {
            "open": 0,
            "partially_addressed": 2,
            "addressed": 3,
        })

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                import yaml
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def extract_from_corpus(
        self, corpus: ProfessorCorpus
    ) -> List[UnsolvedProblemCluster]:
        """Extracts problem claims from professor corpus, clusters them, tests solution coverage, and drops addressed ones."""
        logger.info(f"Extracting unsolved problems for professor '{corpus.professor_name}' ({len(corpus.papers)} papers)")
        raw_claims: List[Tuple[EvidenceClaim, str, float]] = []  # (claim, paper_short_title, weight)

        all_limitations_keywords = self.cues.get("limitations", []) + self.cues.get("future_work", []) + self.cues.get("open_challenge", [])

        for paper in corpus.papers:
            short_title = paper.title[:30].strip()
            # 1. Full-text sections first
            if paper.full_text_sections:
                for sec_name, sec_text in paper.full_text_sections.items():
                    weight = self.section_weights.get(sec_name, 1.5)
                    sentences = [s.strip() for s in re.split(r'\.\s+', sec_text) if s.strip()]
                    for s in sentences:
                        if any(k in s.lower() for k in all_limitations_keywords):
                            cleaned = clean_sentence(s, short_title)
                            if cleaned and len(cleaned) > 20:
                                claim = EvidenceClaim(
                                    claim_text=cleaned,
                                    paper_id=paper.paper_id,
                                    supporting_span=s,
                                )
                                raw_claims.append((claim, short_title, weight))

            # 2. Abstract fallback
            if paper.abstract:
                weight = self.section_weights.get("abstract", 1.0)
                sentences = [s.strip() for s in re.split(r'\.\s+', paper.abstract) if s.strip()]
                for s in sentences:
                    if any(k in s.lower() for k in all_limitations_keywords):
                        cleaned = clean_sentence(s, short_title)
                        if cleaned and len(cleaned) > 20:
                            claim = EvidenceClaim(
                                claim_text=cleaned,
                                paper_id=paper.paper_id,
                                supporting_span=s,
                            )
                            raw_claims.append((claim, short_title, weight))

        if not raw_claims:
            logger.info(f"No limitation/future-work claims extracted for {corpus.professor_name}")
            return []

        # Cluster raw claims using TF-IDF + keyphrase Jaccard
        clusters = self._cluster_claims(raw_claims, corpus.professor_name)

        # Test "unsolved" status against external literature (OpenAlex/Semantic Scholar)
        active_clusters: List[UnsolvedProblemCluster] = []
        for cluster in clusters:
            status, evidence = self._test_unsolved(cluster)
            cluster.solution_status = status
            cluster.solution_evidence = evidence
            # Drop addressed clusters per spec
            if status != "addressed":
                active_clusters.append(cluster)
            else:
                logger.info(f"Dropping addressed cluster '{cluster.title}' ({len(evidence)} solution works found)")

        logger.info(f"Extracted {len(active_clusters)} active (open/partially_addressed) problem clusters for {corpus.professor_name}")
        return active_clusters

    def _cluster_claims(
        self, raw_claims: List[Tuple[EvidenceClaim, str, float]], professor_name: str
    ) -> List[UnsolvedProblemCluster]:
        """Clusters claims by combined TF-IDF cosine (0.6) + key-phrase Jaccard (0.4)."""
        clusters: List[UnsolvedProblemCluster] = []
        corpus_texts = [claim.claim_text for claim, _, _ in raw_claims]

        for claim, short_title, weight in raw_claims:
            text = claim.claim_text
            phrases = extract_key_phrases(text, top_k=5)

            matched_cluster = None
            best_sim = 0.0

            for cluster in clusters:
                c_text = cluster.title
                c_phrases = cluster.key_phrases

                tfidf_sim = tfidf_cosine_similarity(text, c_text, corpus_texts)
                jaccard_sim = keyphrase_jaccard(phrases, c_phrases)
                combined_sim = (0.6 * tfidf_sim) + (0.4 * jaccard_sim)

                if combined_sim >= self.clustering_threshold and combined_sim > best_sim:
                    best_sim = combined_sim
                    matched_cluster = cluster

            if matched_cluster:
                matched_cluster.quoted_claims.append(claim)
                matched_cluster.support_count += 1
                if claim.paper_id not in matched_cluster.papers:
                    matched_cluster.papers.append(claim.paper_id)
                if professor_name not in matched_cluster.professors:
                    matched_cluster.professors.append(professor_name)
                # Update keyphrases
                all_p = set(matched_cluster.key_phrases).union(phrases)
                matched_cluster.key_phrases = list(all_p)[:7]
            else:
                cid = f"cluster_{hashlib.sha256(text.encode()).hexdigest()[:12]}"
                new_cluster = UnsolvedProblemCluster(
                    cluster_id=cid,
                    title=text,
                    key_phrases=phrases,
                    quoted_claims=[claim],
                    support_count=1,
                    papers=[claim.paper_id],
                    professors=[professor_name],
                    solution_status="open",
                    extraction_method="rules",
                )
                clusters.append(new_cluster)

        return clusters

    def _test_unsolved(
        self, cluster: UnsolvedProblemCluster
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Searches OpenAlex (2023..2026) for key phrases and counts solution matches."""
        query = " ".join(cluster.key_phrases[:3]) if cluster.key_phrases else cluster.title[:50]
        if not query:
            return "open", []

        url = f"{OPENALEX_WORKS_URL}?search={requests_quote(query)}&filter=publication_year:2023..2026&per_page=15"
        res = self.requester.get(url)

        if not res or res.status_code != 200:
            return "unclear", []

        results = res.json().get("results", [])
        solution_matches: List[Dict[str, Any]] = []

        for work in results:
            title = work.get("title") or ""
            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))
            text = f"{title} {abstract}".lower()

            if any(cue in text for cue in self.solution_cues):
                solution_matches.append({
                    "work_id": work.get("id"),
                    "title": title,
                    "doi": work.get("doi"),
                    "year": work.get("publication_year"),
                    "venue": work.get("primary_location", {}).get("source", {}).get("display_name", ""),
                    "solution_cue_found": [cue for cue in self.solution_cues if cue in text][:2],
                })

        count = len(solution_matches)
        addressed_thresh = self.status_thresholds.get("addressed", 3)
        partial_thresh = self.status_thresholds.get("partially_addressed", 2)

        if count >= addressed_thresh:
            status = "addressed"
        elif count >= 1:
            status = "partially_addressed"
        else:
            status = "open"

        return status, solution_matches

    def _reconstruct_abstract(self, inverted_index: Optional[Dict[str, List[int]]]) -> str:
        if not inverted_index:
            return ""
        try:
            position_word = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    position_word.append((pos, word))
            position_word.sort(key=lambda x: x[0])
            return " ".join([word for _, word in position_word])
        except Exception:
            return ""


def requests_quote(text: str) -> str:
    import urllib.parse
    return urllib.parse.quote(text)
