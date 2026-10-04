"""Gemini REST API client for research problem formulation and IEEE statement writing."""

import os
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

import requests

from src.research_gaps.models import (
    IEEEResearchStatement,
    IEEESentence,
    Citation,
    EvidenceBundle,
    EvidenceWork,
    UnsolvedProblemCluster,
    PhDQualificationResult,
)
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/"


class GeminiFormulator:
    """Formulates PhD research problems and IEEE statements via Gemini REST API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        llm_cfg = self.config.get("llm", {})
        self.enabled = llm_cfg.get("enabled", True)
        self.model_id = llm_cfg.get("model_id", "gemini-2.5-flash")
        if "gemini-1.5" in self.model_id:
            raise ValueError(f"Prohibited Gemini model '{self.model_id}'. Never use gemini-1.5-* models.")
        self.temperature = float(llm_cfg.get("temperature", 0.2))
        self.max_calls = int(llm_cfg.get("max_calls_per_run", 15))
        self.cache_dir = DATA_DIR / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.call_count = 0
        self.quota_exhausted = False

        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")

    def _hash_input(self, cluster: UnsolvedProblemCluster, bundle: EvidenceBundle) -> str:
        keys_str = ",".join(sorted(w.ref_key for w in bundle.works))
        seed = f"{cluster.cluster_id}|{cluster.title}|{keys_str}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def _load_cached(self, cache_hash: str) -> Optional[IEEEResearchStatement]:
        cache_file = self.cache_dir / f"{cache_hash}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return IEEEResearchStatement.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed loading LLM cache {cache_hash}: {e}")
        return None

    def _save_cached(self, cache_hash: str, stmt: IEEEResearchStatement) -> None:
        cache_file = self.cache_dir / f"{cache_hash}.json"
        try:
            _atomic_write_json(cache_file, stmt.to_dict())
        except Exception as e:
            logger.warning(f"Failed saving LLM cache {cache_hash}: {e}")

    def _call_gemini_api(self, prompt: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Makes direct REST API call to Gemini using requests."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY / LLM_API_KEY not present in environment.")
            return None

        if self.quota_exhausted or self.call_count >= self.max_calls:
            logger.warning(f"LLM stage limit reached (call_count={self.call_count}, quota_exhausted={self.quota_exhausted}). Queueing for next run.")
            return None

        url = f"{GEMINI_API_URL}{self.model_id}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }

        retries = 2
        for attempt in range(retries):
            try:
                self.call_count += 1
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return json.loads(text)
                elif resp.status_code == 404:
                    raise RuntimeError(f"Config Error: Gemini model '{self.model_id}' returned 404 Not Found.")
                elif resp.status_code == 429:
                    logger.warning(f"Gemini API 429 Rate Limit hit (attempt {attempt+1}/{retries}).")
                    time.sleep(2 ** (attempt + 1))
                    if attempt == retries - 1:
                        self.quota_exhausted = True
                        return None
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Gemini REST request error: {e}")
                time.sleep(1)

        return None

    def _validate_response(
        self,
        data: Dict[str, Any],
        bundle: EvidenceBundle,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate Gemini structured JSON output against constraints."""
        errors: List[str] = []
        valid_keys = {w.ref_key for w in bundle.works}

        title = data.get("title", "")
        questions = data.get("research_questions", [])
        sections_dict = data.get("sections", {})

        if not title:
            errors.append("Missing title.")

        # Check research questions end with ?
        formatted_questions = []
        for q in questions:
            q_str = str(q).strip()
            if q_str:
                if not q_str.endswith("?"):
                    q_str += "?"
                formatted_questions.append(q_str)

        # Check cited keys exist in bundle
        cited_keys_total: Set[str] = set()
        section_citation_counts: Dict[str, int] = {}

        expected_sections = [
            "Section I: Introduction & Background",
            "Section II: Problem Statement & Unsolved Gap",
            "Section III: Proposed Research Direction & Methodology",
            "Section IV: Expected Contributions & Impact",
            "Section V: Experimental Strategy & Evaluation Metrics",
            "Section VI: Related Work & Comparative Analysis",
            "Section VII: Conclusion & Next Steps",
        ]

        parsed_sections: Dict[str, List[IEEESentence]] = {}

        for sec_name in expected_sections:
            sec_text = sections_dict.get(sec_name, "")
            if isinstance(sec_text, list):
                sec_text = " ".join(str(s) for s in sec_text)

            # Find all [R1], [R2] citations in section
            found_keys = re.findall(r'\[(R\d+)\]', str(sec_text))
            invalid_keys = [k for k in found_keys if k not in valid_keys]
            if invalid_keys:
                errors.append(f"Invalid reference keys cited in '{sec_name}': {invalid_keys}. Must exist in Evidence Bundle.")

            for k in found_keys:
                if k in valid_keys:
                    cited_keys_total.add(k)

            section_citation_counts[sec_name] = len(set(found_keys) & valid_keys)

            # Format sentences
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', str(sec_text)) if s.strip()]
            ieee_sentences = []
            for s in sentences:
                s_keys = re.findall(r'\[R(\d+)\]', s)
                nums = [int(k) for k in s_keys]
                ieee_sentences.append(IEEESentence(text=s, tag="llm", citation_numbers=nums))
            parsed_sections[sec_name] = ieee_sentences

        # Minimum section citation thresholds
        sec_min_map = {
            "Section I: Introduction & Background": 3,
            "Section II: Problem Statement & Unsolved Gap": 8,
            "Section III: Proposed Research Direction & Methodology": 3,
            "Section V: Experimental Strategy & Evaluation Metrics": 3,
            "Section VI: Related Work & Comparative Analysis": 2,
        }

        under_referenced = False
        if len(cited_keys_total) < 20:
            under_referenced = True

        for sec, min_c in sec_min_map.items():
            if section_citation_counts.get(sec, 0) < min_c:
                under_referenced = True

        validated_payload = {
            "title": title,
            "abstract": data.get("abstract", ""),
            "research_questions": formatted_questions,
            "sections": parsed_sections,
            "cited_keys": sorted(list(cited_keys_total), key=lambda x: int(x[1:]) if x[1:].isdigit() else 999),
            "under_referenced": under_referenced,
        }

        return len(errors) == 0, errors, validated_payload

    def generate_statement(
        self,
        cluster: UnsolvedProblemCluster,
        qualification: PhDQualificationResult,
        bundle: EvidenceBundle,
    ) -> Optional[IEEEResearchStatement]:
        """Generates IEEE research statement using Gemini REST API."""
        if not self.enabled or not self.api_key:
            return None

        cache_hash = self._hash_input(cluster, bundle)
        cached = self._load_cached(cache_hash)
        if cached:
            return cached

        # Prepare bundle reference text for prompt
        bundle_text_lines = []
        for w in bundle.works:
            bundle_text_lines.append(f"[{w.ref_key}] {w.to_citation().format()} (Role: {w.role})")
        bundle_text = "\n".join(bundle_text_lines)

        claims_text = "\n".join([f"- {c.claim_text} (from {c.paper_id})" for c in cluster.quoted_claims])

        prompt = f"""You are an expert computer science research professor writing a formal IEEE research statement for a PhD topic proposal.

RESEARCH PROBLEM CLUSTER:
Title: {cluster.title}
Key Phrases: {', '.join(cluster.key_phrases)}
Supporting Claims / Limitations:
{claims_text}

EVIDENCE BUNDLE (AVAILABLE REFERENCES):
{bundle_text}

INSTRUCTIONS & RULES:
1. Write a rigorous IEEE research statement for this PhD topic proposal.
2. DO NOT write DOIs, URLs, or reference entries. Use citation keys like [R1], [R2] matching the provided Evidence Bundle ONLY.
3. Every research question MUST end with '?'.
4. Cite liberally across all sections using keys from the Evidence Bundle.
5. Provide content for all 7 required IEEE sections:
   - Section I: Introduction & Background (min 3 references)
   - Section II: Problem Statement & Unsolved Gap (min 8 references)
   - Section III: Proposed Research Direction & Methodology (min 3 references)
   - Section IV: Expected Contributions & Impact
   - Section V: Experimental Strategy & Evaluation Metrics (min 3 references)
   - Section VI: Related Work & Comparative Analysis (min 2 references)
   - Section VII: Conclusion & Next Steps
"""

        schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "abstract": {"type": "STRING"},
                "research_questions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "sections": {
                    "type": "OBJECT",
                    "properties": {
                        "Section I: Introduction & Background": {"type": "STRING"},
                        "Section II: Problem Statement & Unsolved Gap": {"type": "STRING"},
                        "Section III: Proposed Research Direction & Methodology": {"type": "STRING"},
                        "Section IV: Expected Contributions & Impact": {"type": "STRING"},
                        "Section V: Experimental Strategy & Evaluation Metrics": {"type": "STRING"},
                        "Section VI: Related Work & Comparative Analysis": {"type": "STRING"},
                        "Section VII: Conclusion & Next Steps": {"type": "STRING"},
                    },
                    "required": [
                        "Section I: Introduction & Background",
                        "Section II: Problem Statement & Unsolved Gap",
                        "Section III: Proposed Research Direction & Methodology",
                        "Section IV: Expected Contributions & Impact",
                        "Section V: Experimental Strategy & Evaluation Metrics",
                        "Section VI: Related Work & Comparative Analysis",
                        "Section VII: Conclusion & Next Steps",
                    ],
                },
            },
            "required": ["title", "abstract", "research_questions", "sections"],
        }

        # Attempt 1
        raw_resp = self._call_gemini_api(prompt, schema)
        if not raw_resp:
            return None

        is_valid, errors, val_data = self._validate_response(raw_resp, bundle)

        # Attempt 2 (One Retry with Errors Fed Back)
        if not is_valid:
            logger.warning(f"LLM output failed validation: {errors}. Retrying with feedback...")
            retry_prompt = prompt + f"\n\nPREVIOUS OUTPUT HAD ERRORS:\n" + "\n".join(errors) + "\nPlease fix these errors and adhere strictly to the rules."
            raw_resp = self._call_gemini_api(retry_prompt, schema)
            if not raw_resp:
                return None
            is_valid, errors, val_data = self._validate_response(raw_resp, bundle)
            if not is_valid:
                logger.warning(f"LLM output failed validation on retry: {errors}.")
                return None

        # Render reference list deterministically from Evidence Bundle
        cited_keys = val_data["cited_keys"]
        references = []
        for k in cited_keys:
            w = bundle.get_by_key(k)
            if w:
                references.append(w.to_citation().to_dict())

        # Markdown representation
        md_parts = [
            f"# {val_data['title']}\n",
            f"**Abstract:** {val_data['abstract']}\n",
            "## Research Questions",
        ]
        for q in val_data["research_questions"]:
            md_parts.append(f"- {q}")
        md_parts.append("\n")

        for sec_name, sentences in val_data["sections"].items():
            md_parts.append(f"## {sec_name}")
            sec_text = " ".join(s.text for s in sentences)
            md_parts.append(f"{sec_text}\n")

        md_parts.append("## References")
        for k in cited_keys:
            w = bundle.get_by_key(k)
            if w:
                cit = w.to_citation()
                link_str = f" [{cit.link}]({cit.link})" if cit.link else ""
                md_parts.append(f"- [{k}] {cit.format()}{link_str}")

        markdown_content = "\n".join(md_parts)
        word_count = len(markdown_content.split())

        stmt = IEEEResearchStatement(
            problem_id=cluster.cluster_id,
            title=val_data["title"],
            abstract=val_data["abstract"],
            index_terms=cluster.key_phrases,
            sections=val_data["sections"],
            research_questions=val_data["research_questions"],
            references=references,
            word_count=word_count,
            markdown_content=markdown_content,
            generation_method=self.model_id,
            under_referenced=val_data["under_referenced"],
        )

        self._save_cached(cache_hash, stmt)
        return stmt
