"""Weekly study focus and action plan generator."""

from typing import List, Dict, Any, Optional
from src.models import ResearchItem, ItemType
from src.utils.config_loader import ConfigManager


class StudyGuideGenerator:
    """Generates an actionable weekly study plan tailored to the user's PhD preparation."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()

    def generate_focus_plan(
        self,
        top_papers: List[ResearchItem],
        conferences: List[ResearchItem],
        opportunities: List[ResearchItem]
    ) -> Dict[str, Any]:
        """Synthesizes weekly focus: Concept, Paper, Practical Exercise, Research Question, Opportunity."""
        learning_stage = self.config.learning_stage
        current_topics = learning_stage.get("current_topics", ["Edge AI", "Computation Offloading"])
        focus_topic = current_topics[0] if current_topics else "Edge Computing"

        # Select best matching paper
        featured_paper = top_papers[0] if top_papers else None
        paper_title = featured_paper.title if featured_paper else "Foundational Survey on Edge Computing & MEC"
        paper_url = featured_paper.url if featured_paper else "https://arxiv.org/abs/cs/edge"

        # Formulate concept, practical exercise, and research question based on topic
        if "Offloading" in focus_topic or "Computation" in focus_topic:
            concept = "Lyapunov Optimization & Task Offloading in Multi-Access Edge Computing"
            exercise = "Implement a simple 2-node edge/cloud offloading simulator with variable network latency in Python."
            research_question = "How can task offloading algorithms maintain strict sub-10ms latency SLAs under stochastic wireless channel fading?"
        elif "Federated" in focus_topic or "Intelligence" in focus_topic or "Edge AI" in focus_topic:
            concept = "Communication-Efficient Federated Learning & Model Quantization at the Edge"
            exercise = "Train a lightweight CNN with PyTorch/TensorFlow Lite and measure latency on simulated constrained devices."
            research_question = "How can asynchronous edge aggregation mitigate straggler latency in non-IID edge networks?"
        elif "Distributed" in focus_topic or "Systems" in focus_topic:
            concept = "Consensus Protocols and Fault Tolerance in Geo-Distributed Edge Clusters"
            exercise = "Set up a lightweight 3-node K3s cluster and benchmark container orchestration response times."
            research_question = "What are the trade-offs between consistency and availability in edge nodes with intermittent network connectivity?"
        else:
            concept = f"Core Architecture and Protocols of {focus_topic}"
            exercise = "Benchmark network latency and resource consumption across local vs edge compute."
            research_question = f"What are the unsolved scalability bottlenecks in {focus_topic}?"

        # Upcoming opportunity or CFP
        featured_event = None
        if opportunities:
            featured_event = {
                "title": opportunities[0].title,
                "url": opportunities[0].url,
                "type": "PhD Opportunity"
            }
        elif conferences:
            featured_event = {
                "title": conferences[0].title,
                "url": conferences[0].url,
                "type": "Conference / CFP"
            }
        else:
            featured_event = {
                "title": "Explore ACM SEC & IEEE INFOCOM Workshops",
                "url": "https://acm-ieee-sec.org",
                "type": "Venue"
            }

        return {
            "focus_topic": focus_topic,
            "concept": concept,
            "paper_title": paper_title,
            "paper_url": paper_url,
            "practical_exercise": exercise,
            "research_question": research_question,
            "event_opportunity": featured_event
        }
