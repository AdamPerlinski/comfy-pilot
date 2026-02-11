"""Knowledge manager for intelligent context selection.

Loads markdown knowledge files, parses YAML frontmatter,
and selects relevant knowledge based on user message and budget.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml


class KnowledgeFile:
    """Represents a parsed markdown knowledge file."""

    __slots__ = ("id", "title", "keywords", "category", "priority", "content", "path", "char_count")

    def __init__(
        self,
        id: str,
        title: str,
        keywords: List[str],
        category: str,
        priority: str,
        content: str,
        path: Path,
    ):
        self.id = id
        self.title = title
        self.keywords = [k.lower() for k in keywords]
        self.category = category
        self.priority = priority
        self.content = content
        self.path = path
        self.char_count = len(content)

    def __repr__(self) -> str:
        return f"KnowledgeFile({self.id!r}, {self.char_count} chars)"


# Trigger phrases that map to specific knowledge categories
_TRIGGER_PHRASES: Dict[str, List[str]] = {
    "video": ["video", "wan", "hunyuan", "animatediff", "frames", "motion", "animate", "mochi", "cogvideo", "ltx", "svi", "interpolat"],
    "models": ["model", "download", "checkpoint", "lora", "civitai", "huggingface", "pony", "flux", "sdxl", "nsfw", "vae"],
    "tuning": ["blurry", "artifact", "denoise", "cfg", "steps", "sampler", "flickering", "quality", "fix", "issue", "problem", "wrong", "bad", "improve", "better"],
    "custom_nodes": ["custom node", "install", "manager", "impact pack", "ipadapter", "controlnet", "reactor", "detailer"],
    "patterns": ["workflow", "template", "pattern", "txt2img", "img2img", "upscale", "controlnet"],
}

# Context budgets by agent type
CONTEXT_BUDGETS = {
    "minimal": 5_000,
    "standard": 15_000,
    "verbose": 30_000,
}

AGENT_DEFAULT_BUDGETS = {
    "ollama_small": 8_000,    # <13B models
    "ollama_large": 15_000,   # 32B+ models
    "claude_code": 30_000,    # 200k context
    "default": 15_000,
}


class KnowledgeManager:
    """Manages knowledge files and selects relevant context for agents."""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).parent
        self.knowledge_dir = knowledge_dir
        self.user_dir = knowledge_dir / "user"
        self._files: List[KnowledgeFile] = []
        self._loaded = False

    def load_all(self) -> None:
        """Scan .md files in knowledge dir and user dir, parse frontmatter."""
        self._files = []

        # Load from main knowledge dir
        for md_file in sorted(self.knowledge_dir.glob("*.md")):
            kf = self._parse_file(md_file)
            if kf:
                self._files.append(kf)

        # Load from user dir
        if self.user_dir.exists():
            for md_file in sorted(self.user_dir.glob("*.md")):
                kf = self._parse_file(md_file)
                if kf:
                    self._files.append(kf)

        self._loaded = True

    def _parse_file(self, path: Path) -> Optional[KnowledgeFile]:
        """Parse a markdown file with YAML frontmatter."""
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Extract YAML frontmatter between --- markers
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        if not match:
            # No frontmatter - treat as plain content with defaults
            return KnowledgeFile(
                id=path.stem,
                title=path.stem.replace("_", " ").title(),
                keywords=[],
                category="user",
                priority="low",
                content=text.strip(),
                path=path,
            )

        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return None

        if not isinstance(meta, dict):
            return None

        return KnowledgeFile(
            id=meta.get("id", path.stem),
            title=meta.get("title", path.stem),
            keywords=meta.get("keywords", []),
            category=meta.get("category", "other"),
            priority=meta.get("priority", "low"),
            content=match.group(2).strip(),
            path=path,
        )

    def select_relevant(
        self,
        message: str,
        context_budget: int = 15_000,
        categories_enabled: Optional[Set[str]] = None,
    ) -> List[KnowledgeFile]:
        """Select relevant knowledge files based on message and budget.

        Algorithm:
        1. Always include priority=high files
        2. Score remaining by keyword matches + trigger phrases
        3. Fill until context_budget reached
        4. Respect categories_enabled filter
        """
        if not self._loaded:
            self.load_all()

        msg_lower = message.lower()
        selected: List[KnowledgeFile] = []
        remaining: List[tuple] = []  # (score, file)
        budget_used = 0

        for kf in self._files:
            # Skip disabled categories
            if categories_enabled is not None and kf.category not in categories_enabled:
                continue

            if kf.priority == "high":
                selected.append(kf)
                budget_used += kf.char_count
                continue

            # Score by keyword matches
            score = 0
            for keyword in kf.keywords:
                if keyword in msg_lower:
                    score += 2

            # Score by trigger phrases
            for category, phrases in _TRIGGER_PHRASES.items():
                if category == kf.category:
                    for phrase in phrases:
                        if phrase in msg_lower:
                            score += 3

            if score > 0:
                remaining.append((score, kf))

        # Sort by score descending
        remaining.sort(key=lambda x: x[0], reverse=True)

        # Fill until budget
        for score, kf in remaining:
            if budget_used + kf.char_count <= context_budget:
                selected.append(kf)
                budget_used += kf.char_count

        return selected

    def get_all_categories(self) -> Dict[str, List[str]]:
        """Get all available categories with their file titles (for UI checkboxes)."""
        if not self._loaded:
            self.load_all()

        categories: Dict[str, List[str]] = {}
        for kf in self._files:
            if kf.category not in categories:
                categories[kf.category] = []
            categories[kf.category].append(kf.title)
        return categories

    def get_context_budget(self, agent_name: str, model_name: str = "", context_mode: str = "standard") -> int:
        """Determine context budget based on agent and mode.

        Args:
            agent_name: Name of the agent backend
            model_name: Specific model being used
            context_mode: User-selected mode (minimal/standard/verbose)
        """
        # User override takes priority
        if context_mode in CONTEXT_BUDGETS:
            return CONTEXT_BUDGETS[context_mode]

        # Agent-specific defaults
        if agent_name == "ollama":
            # Estimate model size from name (check longest patterns first to
            # avoid "3b" matching inside "13b")
            size_indicators = {"70b": 20000, "32b": 15000, "14b": 12000, "13b": 12000,
                             "8b": 8000, "7b": 8000, "3b": 8000, "1b": 8000}
            model_lower = model_name.lower()
            for indicator, budget in size_indicators.items():
                if indicator in model_lower:
                    return budget
            return AGENT_DEFAULT_BUDGETS["ollama_small"]

        if agent_name == "claude_code":
            return AGENT_DEFAULT_BUDGETS["claude_code"]

        return AGENT_DEFAULT_BUDGETS["default"]

    def build_knowledge_text(
        self,
        message: str,
        agent_name: str = "default",
        model_name: str = "",
        context_mode: str = "standard",
        categories_enabled: Optional[Set[str]] = None,
    ) -> str:
        """Build the complete knowledge text for a system prompt.

        This is the main entry point used by the controller.
        """
        budget = self.get_context_budget(agent_name, model_name, context_mode)
        files = self.select_relevant(message, budget, categories_enabled)

        if not files:
            return ""

        parts = []
        for kf in files:
            parts.append(f"# {kf.title}\n\n{kf.content}")

        return "\n\n---\n\n".join(parts)
