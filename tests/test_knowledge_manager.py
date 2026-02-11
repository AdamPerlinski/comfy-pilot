"""Tests for knowledge/manager.py - KnowledgeManager and KnowledgeFile."""

import sys

import pytest

_km_mod = sys.modules["knowledge_manager"]
KnowledgeFile = _km_mod.KnowledgeFile
KnowledgeManager = _km_mod.KnowledgeManager
CONTEXT_BUDGETS = _km_mod.CONTEXT_BUDGETS
AGENT_DEFAULT_BUDGETS = _km_mod.AGENT_DEFAULT_BUDGETS


# ── KnowledgeFile ──────────────────────────────────────────────────────


class TestKnowledgeFile:
    def test_basic_construction(self, tmp_path):
        kf = KnowledgeFile(
            id="test",
            title="Test File",
            keywords=["Alpha", "Beta"],
            category="core",
            priority="high",
            content="hello world",
            path=tmp_path / "test.md",
        )
        assert kf.id == "test"
        assert kf.title == "Test File"
        assert kf.keywords == ["alpha", "beta"]  # lowercased
        assert kf.category == "core"
        assert kf.priority == "high"
        assert kf.char_count == len("hello world")

    def test_repr(self, tmp_path):
        kf = KnowledgeFile(
            id="x", title="X", keywords=[], category="c",
            priority="low", content="abc", path=tmp_path / "x.md",
        )
        assert "KnowledgeFile" in repr(kf)
        assert "3 chars" in repr(kf)

    def test_empty_keywords(self, tmp_path):
        kf = KnowledgeFile(
            id="x", title="X", keywords=[], category="c",
            priority="low", content="", path=tmp_path / "x.md",
        )
        assert kf.keywords == []
        assert kf.char_count == 0


# ── Parsing ────────────────────────────────────────────────────────────


class TestParseFile:
    def test_parse_with_frontmatter(self, tmp_knowledge_dir, sample_md_with_frontmatter):
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(sample_md_with_frontmatter)

        assert kf is not None
        assert kf.id == "core_nodes"
        assert kf.title == "Core ComfyUI Nodes"
        assert kf.category == "core"
        assert kf.priority == "high"
        assert "ksampler" in kf.keywords
        assert "checkpoint" in kf.keywords
        assert "vaedecode" in kf.keywords
        assert "Core Nodes" in kf.content
        assert "KSampler is the main" in kf.content

    def test_parse_without_frontmatter(self, tmp_knowledge_dir, sample_md_no_frontmatter):
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(sample_md_no_frontmatter)

        assert kf is not None
        assert kf.id == "user_notes"
        assert kf.category == "user"
        assert kf.priority == "low"
        assert kf.keywords == []
        assert "plain user notes" in kf.content

    def test_parse_invalid_yaml(self, tmp_knowledge_dir):
        path = tmp_knowledge_dir / "bad.md"
        path.write_text("---\n[invalid: yaml: {{{\n---\ncontent\n")
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(path)
        assert kf is None

    def test_parse_yaml_not_dict(self, tmp_knowledge_dir):
        path = tmp_knowledge_dir / "scalar.md"
        path.write_text("---\njust a string\n---\ncontent\n")
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(path)
        assert kf is None

    def test_parse_nonexistent_file(self, tmp_knowledge_dir):
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(tmp_knowledge_dir / "nonexistent.md")
        assert kf is None

    def test_parse_missing_optional_fields(self, tmp_knowledge_dir):
        path = tmp_knowledge_dir / "minimal.md"
        path.write_text("---\ntitle: Minimal\n---\nContent.\n")
        mgr = KnowledgeManager(tmp_knowledge_dir)
        kf = mgr._parse_file(path)

        assert kf is not None
        assert kf.id == "minimal"  # falls back to stem
        assert kf.title == "Minimal"
        assert kf.keywords == []
        assert kf.category == "other"
        assert kf.priority == "low"


# ── load_all ───────────────────────────────────────────────────────────


class TestLoadAll:
    def test_loads_main_and_user_dirs(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        ids = {kf.id for kf in mgr._files}
        assert "core_nodes" in ids
        assert "models" in ids
        assert "video_advanced" in ids
        assert "workflow_tuning" in ids
        assert "my_tips" in ids  # user file (no frontmatter -> id = stem)

    def test_loads_sorted(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        # main dir files should be sorted alphabetically before user files
        main_ids = [kf.id for kf in mgr._files if kf.category != "user"]
        assert main_ids == sorted(main_ids)

    def test_empty_dir(self, tmp_path):
        kdir = tmp_path / "empty"
        kdir.mkdir()
        mgr = KnowledgeManager(kdir)
        mgr.load_all()
        assert mgr._files == []
        assert mgr._loaded is True

    def test_no_user_dir(self, tmp_knowledge_dir, sample_md_with_frontmatter):
        # Remove user dir
        import shutil
        user_dir = tmp_knowledge_dir / "user"
        if user_dir.exists():
            shutil.rmtree(user_dir)

        mgr = KnowledgeManager(tmp_knowledge_dir)
        mgr.load_all()
        assert len(mgr._files) == 1  # just core_nodes


# ── select_relevant ────────────────────────────────────────────────────


class TestSelectRelevant:
    def test_high_priority_always_included(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        selected = mgr.select_relevant("hello world", context_budget=100_000)
        selected_ids = {kf.id for kf in selected}
        assert "core_nodes" in selected_ids

    def test_video_trigger_selects_video(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        selected = mgr.select_relevant("help me with video generation", context_budget=100_000)
        selected_ids = {kf.id for kf in selected}
        assert "video_advanced" in selected_ids

    def test_model_trigger_selects_models(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        selected = mgr.select_relevant("where can I download a flux model?", context_budget=100_000)
        selected_ids = {kf.id for kf in selected}
        assert "models" in selected_ids

    def test_tuning_trigger(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        selected = mgr.select_relevant("my image is blurry, how to fix?", context_budget=100_000)
        selected_ids = {kf.id for kf in selected}
        assert "workflow_tuning" in selected_ids

    def test_budget_limits_selection(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        # Very small budget - should only fit high-priority
        selected = mgr.select_relevant("video model download blurry", context_budget=100)
        selected_ids = {kf.id for kf in selected}
        # core_nodes is ~40 chars in test, so it fits
        assert "core_nodes" in selected_ids
        # large video_advanced (5000+ chars) should not fit
        assert "video_advanced" not in selected_ids

    def test_category_filter(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        # Only enable "video" category - high priority "core" should be excluded
        selected = mgr.select_relevant(
            "help with video",
            context_budget=100_000,
            categories_enabled={"video"},
        )
        selected_ids = {kf.id for kf in selected}
        assert "core_nodes" not in selected_ids  # core category not enabled
        assert "video_advanced" in selected_ids

    def test_no_matching_message(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        selected = mgr.select_relevant("something completely unrelated xyz123", context_budget=100_000)
        selected_ids = {kf.id for kf in selected}
        # Only high-priority files should be included
        assert "core_nodes" in selected_ids
        assert "models" not in selected_ids
        assert "video_advanced" not in selected_ids

    def test_auto_loads_if_not_loaded(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        assert mgr._loaded is False
        selected = mgr.select_relevant("ksampler", context_budget=100_000)
        assert mgr._loaded is True
        assert len(selected) > 0


# ── get_all_categories ─────────────────────────────────────────────────


class TestGetAllCategories:
    def test_returns_categories_with_titles(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        cats = mgr.get_all_categories()
        assert "core" in cats
        assert "models" in cats
        assert "video" in cats
        assert "tuning" in cats
        assert "user" in cats  # from the user file without frontmatter

        assert "Core Nodes" in cats["core"]
        assert "Models Guide" in cats["models"]

    def test_auto_loads(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        cats = mgr.get_all_categories()
        assert mgr._loaded is True
        assert len(cats) > 0


# ── get_context_budget ─────────────────────────────────────────────────


class TestGetContextBudget:
    def test_context_mode_override(self):
        mgr = KnowledgeManager()
        assert mgr.get_context_budget("any", "", "minimal") == CONTEXT_BUDGETS["minimal"]
        assert mgr.get_context_budget("any", "", "standard") == CONTEXT_BUDGETS["standard"]
        assert mgr.get_context_budget("any", "", "verbose") == CONTEXT_BUDGETS["verbose"]

    def test_ollama_small_model(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("ollama", "qwen2.5:7b", "unknown_mode")
        assert budget == 8000

    def test_ollama_large_model(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("ollama", "llama3.1:70b", "unknown_mode")
        assert budget == 20000

    def test_ollama_medium_model(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("ollama", "codellama:13b", "unknown_mode")
        assert budget == 12000

    def test_ollama_unknown_model(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("ollama", "some_unknown_model", "unknown_mode")
        assert budget == AGENT_DEFAULT_BUDGETS["ollama_small"]

    def test_claude_code(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("claude_code", "", "unknown_mode")
        assert budget == AGENT_DEFAULT_BUDGETS["claude_code"]

    def test_unknown_agent(self):
        mgr = KnowledgeManager()
        budget = mgr.get_context_budget("gemini", "", "unknown_mode")
        assert budget == AGENT_DEFAULT_BUDGETS["default"]

    def test_context_mode_takes_priority_over_agent(self):
        mgr = KnowledgeManager()
        # Even for ollama small, minimal mode should override
        budget = mgr.get_context_budget("ollama", "qwen:7b", "minimal")
        assert budget == CONTEXT_BUDGETS["minimal"]


# ── build_knowledge_text ───────────────────────────────────────────────


class TestBuildKnowledgeText:
    def test_returns_formatted_text(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        text = mgr.build_knowledge_text(
            message="help me with models",
            agent_name="default",
            context_mode="verbose",
        )
        assert "# Core Nodes" in text
        assert "# Models Guide" in text
        assert "---" in text  # separator between sections

    def test_returns_empty_for_no_matches_with_filter(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        text = mgr.build_knowledge_text(
            message="hello",
            agent_name="default",
            context_mode="verbose",
            categories_enabled={"nonexistent_category"},
        )
        assert text == ""

    def test_respects_budget(self, populated_knowledge_dir):
        mgr = KnowledgeManager(populated_knowledge_dir)
        mgr.load_all()

        text_minimal = mgr.build_knowledge_text(
            message="video model download",
            agent_name="default",
            context_mode="minimal",
        )
        text_verbose = mgr.build_knowledge_text(
            message="video model download",
            agent_name="default",
            context_mode="verbose",
        )
        assert len(text_minimal) <= len(text_verbose)
