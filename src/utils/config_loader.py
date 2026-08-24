"""Configuration loader with environment variable interpolation and validation."""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def _env_var_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    """Custom YAML constructor to resolve ${VAR_NAME:-default} or ${VAR_NAME} syntax."""
    value = loader.construct_scalar(node)
    pattern = re.compile(r'\$\{([^}^{:]+)(?::-(.*?))?\}')
    
    def replace_fn(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(env_var, default_val)
        
    return pattern.sub(replace_fn, value)


def get_yaml_loader():
    """Returns a SafeLoader that expands environment variables in strings."""
    loader = yaml.SafeLoader
    loader.add_implicit_resolver('!env_var', re.compile(r'.*\$\{[^}^{]+(?:;-[^}]*)?\}.*'), None)
    loader.add_constructor('!env_var', _env_var_constructor)
    return loader


def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Loads and parses a YAML file with environment variable substitution."""
    if not filepath.exists():
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pre-substitute ${VAR} strings before parsing
    pattern = re.compile(r'\$\{([^}^{:]+)(?::-(.*?))?\}')
    def replace_fn(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(env_var, default_val)
        
    expanded_content = pattern.sub(replace_fn, content)
    data = yaml.safe_load(expanded_content)
    return data if isinstance(data, dict) else {}


class ConfigManager:
    """Central configuration manager for all yaml configuration files."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Default to config/ directory relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.config_dir = base_dir / "config"
        else:
            self.config_dir = Path(config_dir)

        self.topics = load_yaml_file(self.config_dir / "topics.yaml")
        self.sources = load_yaml_file(self.config_dir / "sources.yaml")
        self.conferences = load_yaml_file(self.config_dir / "conferences.yaml")
        self.research_groups = load_yaml_file(self.config_dir / "research_groups.yaml")
        self.profile = load_yaml_file(self.config_dir / "profile.yaml")

    def reload(self):
        """Reloads all configuration files."""
        self.topics = load_yaml_file(self.config_dir / "topics.yaml")
        self.sources = load_yaml_file(self.config_dir / "sources.yaml")
        self.conferences = load_yaml_file(self.config_dir / "conferences.yaml")
        self.research_groups = load_yaml_file(self.config_dir / "research_groups.yaml")
        self.profile = load_yaml_file(self.config_dir / "profile.yaml")

    @property
    def primary_topics(self) -> list:
        return self.topics.get("primary_topics", [])

    @property
    def secondary_topics(self) -> list:
        return self.topics.get("secondary_topics", [])

    @property
    def research_topics(self) -> list:
        return self.topics.get("research_topics", [])

    @property
    def negative_keywords(self) -> list:
        return self.topics.get("negative_keywords", [])

    @property
    def alert_thresholds(self) -> dict:
        return self.profile.get("alert_thresholds", {
            "minimum_score": 6.5,
            "daily_digest_min_score": 7.5,
            "weekly_digest_min_score": 6.8,
            "urgent_alert_min_score": 9.0,
            "daily_limit": 10,
            "weekly_limit": 20
        })

    @property
    def email_config(self) -> dict:
        return self.profile.get("email_preferences", {
            "provider": "console",
            "sender_email": "research-alert@resend.dev",
            "recipient_email": os.environ.get("EMAIL_RECIPIENT", "user@example.com"),
            "daily_digest": True,
            "weekly_digest": True,
            "urgent_alerts": True
        })

    @property
    def learning_stage(self) -> dict:
        return self.profile.get("learning_stage", {
            "current_level": 3,
            "current_topics": ["Edge AI", "Computation Offloading"],
            "stage_boost_multiplier": 1.25
        })

    @property
    def phd_target(self) -> dict:
        return self.profile.get("phd_target", {
            "field": "Edge Computing",
            "target_application_period": "2027-01-01"
        })
