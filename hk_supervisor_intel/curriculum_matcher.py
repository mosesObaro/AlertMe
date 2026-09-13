"""
Curriculum Matcher for Hong Kong PhD Supervisor Intelligence.
Bridges Hong Kong researchers to the existing 24-Week Plan and Master Curriculum
in the Edge Computing PhD Curriculum & Tracker.
"""

from typing import List, Dict, Any
from .models import ResearcherProfile

class CurriculumMatcher:
    """Connects researchers' topics to the existing 24-Week Edge Computing curriculum."""

    CURRICULUM_TOPIC_MAP = {
        "edge_foundations": {
            "keywords": ["edge computing", "cloudlet", "fog computing", "edge-cloud"],
            "weeks": [1],
            "courses": ["Introduction to Edge Computing (LF Edge)"]
        },
        "networking": {
            "keywords": ["networking", "tcp/ip", "latency", "sdn", "openflow", "mqtt"],
            "weeks": [2, 3, 4],
            "courses": ["CS144: Intro to Computer Networking (Stanford)", "CS6250: SDN (Georgia Tech)"]
        },
        "distributed_systems": {
            "keywords": ["distributed systems", "consensus", "raft", "rpc", "fault tolerance", "crdt", "consistency"],
            "weeks": [5, 6, 7, 8],
            "courses": ["6.5840 / 6.824: Distributed Systems (MIT CSAIL)", "Distributed Systems Theory (Cambridge)"]
        },
        "cloud_native": {
            "keywords": ["kubernetes", "k3s", "container", "docker", "cgroups", "serverless", "faas", "microservices"],
            "weeks": [9, 10, 11],
            "courses": ["LFS156x: Kubernetes on Edge with K3s", "Linux Containers from Scratch (Liz Rice)"]
        },
        "edge_core_and_5g": {
            "keywords": ["5g", "6g", "mec", "multi-access edge", "network slicing", "urllc", "v2x", "cellular"],
            "weeks": [12, 13, 14],
            "courses": ["5G Network Architecture and Slicing (EURECOM)", "Multi-Access Edge Computing Standards (ETSI)"]
        },
        "optimization": {
            "keywords": ["optimization", "resource allocation", "offloading", "convex", "scheduling", "lyapunov", "reinforcement learning"],
            "weeks": [15, 16],
            "courses": ["EE364a: Convex Optimization I (Stanford)", "Reinforcement Learning Course (UCL / David Silver)"]
        },
        "edge_ai": {
            "keywords": ["edge ai", "edge intelligence", "tinyml", "quantization", "pruning", "embedded ai", "split learning"],
            "weeks": [17, 18],
            "courses": ["TinyML Specialization (CS249r / Harvard)"]
        },
        "federated_learning": {
            "keywords": ["federated learning", "fedavg", "distributed ml", "non-iid", "gradient compression"],
            "weeks": [19, 20],
            "courses": ["Federated Learning Frameworks & Systems (Flower.ai)", "CS255: Cryptography & Security (Stanford)"]
        },
        "simulation": {
            "keywords": ["simulation", "edgecloudsim", "ns-3", "testbed", "omnet++", "discrete-event"],
            "weeks": [21, 22],
            "courses": ["EdgeCloudSim Simulation Framework (Boğaziçi Univ)"]
        },
        "phd_proposal": {
            "keywords": ["writing", "proposal", "latex", "research methodology"],
            "weeks": [23, 24],
            "courses": ["Writing in the Sciences (Stanford Online)", "Overleaf LaTeX Tutorial"]
        }
    }

    @classmethod
    def match_researcher_to_curriculum(cls, researcher: ResearcherProfile) -> Dict[str, Any]:
        """
        Maps a researcher's interests, trajectory, and methods to relevant weeks
        and courses in the existing 24-Week Plan.
        """
        text = (
            " ".join(researcher.research_interests) + " " +
            researcher.research_summary + " " +
            " ".join(researcher.current_projects)
        ).lower()

        matched_weeks = set()
        matched_courses = set()
        matched_topics = []

        for topic_key, data in cls.CURRICULUM_TOPIC_MAP.items():
            for kw in data["keywords"]:
                if kw in text:
                    matched_weeks.update(data["weeks"])
                    matched_courses.update(data["courses"])
                    matched_topics.append(topic_key)
                    break

        sorted_weeks = sorted(list(matched_weeks))
        sorted_courses = sorted(list(matched_courses))

        return {
            "researcher_name": researcher.name,
            "matched_weeks": sorted_weeks,
            "matched_courses": sorted_courses,
            "matched_topic_keys": matched_topics
        }
