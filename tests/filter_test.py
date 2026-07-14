"""Tests for o2cfg Model Filter."""

from o2cfg.filter import filter_models


SAMPLE_MODELS = [
    {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
    {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
    {"id": "claude-3-opus", "object": "model", "owned_by": "anthropic"},
    {"id": "llama-3", "object": "model", "owned_by": "meta"},
]


class TestFilterModels:
    """Test model filtering by denylist and allowlist."""

    def test_no_filters_returns_all(self):
        result = filter_models(SAMPLE_MODELS)
        assert len(result) == 4

    def test_denylist_removes_models(self):
        result = filter_models(SAMPLE_MODELS, denylist=["gpt-4o", "claude-3-opus"])
        assert len(result) == 2
        ids = {m["id"] for m in result}
        assert ids == {"gpt-3.5-turbo", "llama-3"}

    def test_allowlist_keeps_only_specified(self):
        result = filter_models(SAMPLE_MODELS, allowlist=["gpt-4o", "llama-3"])
        assert len(result) == 2
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "llama-3"}

    def test_denylist_applied_before_allowlist(self):
        # Denylist removes claude-3-opus, allowlist keeps only gpt-4o
        result = filter_models(
            SAMPLE_MODELS,
            denylist=["claude-3-opus"],
            allowlist=["gpt-4o", "claude-3-opus"],
        )
        assert len(result) == 1
        assert result[0]["id"] == "gpt-4o"

    def test_empty_allowlist_results_in_zero_models(self):
        result = filter_models(SAMPLE_MODELS, allowlist=[])
        assert result == []

    def test_empty_denylist_is_noop(self):
        result = filter_models(SAMPLE_MODELS, denylist=[])
        assert len(result) == 4

    def test_denylist_none_is_noop(self):
        result = filter_models(SAMPLE_MODELS, denylist=None)
        assert len(result) == 4

    def test_allowlist_none_is_noop(self):
        result = filter_models(SAMPLE_MODELS, allowlist=None)
        assert len(result) == 4

    def test_both_none_returns_all(self):
        result = filter_models(SAMPLE_MODELS, denylist=None, allowlist=None)
        assert len(result) == 4

    def test_denylist_nonexistent_ids_is_noop(self):
        result = filter_models(SAMPLE_MODELS, denylist=["nonexistent-model"])
        assert len(result) == 4

    def test_allowlist_nonexistent_ids_results_in_empty(self):
        result = filter_models(SAMPLE_MODELS, allowlist=["nonexistent-model"])
        assert result == []

    def test_empty_model_list(self):
        result = filter_models([], denylist=["gpt-4o"], allowlist=["gpt-4o"])
        assert result == []

    def test_models_without_id_field(self):
        models = [{"object": "model"}, {"id": "gpt-4o"}]
        result = filter_models(models, denylist=["gpt-4o"])
        assert len(result) == 1
        assert "id" not in result[0]

    # Glob pattern tests

    def test_denylist_glob_star_prefix(self):
        result = filter_models(SAMPLE_MODELS, denylist=["gpt-*"])
        ids = {m["id"] for m in result}
        assert ids == {"claude-3-opus", "llama-3"}

    def test_denylist_glob_star_suffix(self):
        result = filter_models(SAMPLE_MODELS, denylist=["*-opus"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "gpt-3.5-turbo", "llama-3"}

    def test_denylist_glob_star_both_sides(self):
        result = filter_models(SAMPLE_MODELS, denylist=["*3*"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o"}

    def test_denylist_glob_question_mark(self):
        result = filter_models(SAMPLE_MODELS, denylist=["gpt-4?"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-3.5-turbo", "claude-3-opus", "llama-3"}

    def test_denylist_glob_char_class(self):
        result = filter_models(SAMPLE_MODELS, denylist=["llama-[0-9]"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "gpt-3.5-turbo", "claude-3-opus"}

    def test_allowlist_glob_star_prefix(self):
        result = filter_models(SAMPLE_MODELS, allowlist=["gpt-*"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "gpt-3.5-turbo"}

    def test_allowlist_multiple_glob_patterns(self):
        result = filter_models(SAMPLE_MODELS, allowlist=["gpt-*", "llama-*"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "gpt-3.5-turbo", "llama-3"}

    def test_allowlist_glob_no_match(self):
        result = filter_models(SAMPLE_MODELS, allowlist=["mistral-*"])
        assert result == []

    def test_denylist_glob_then_allowlist_glob(self):
        # Remove claude-*, then keep only gpt-*
        result = filter_models(
            SAMPLE_MODELS,
            denylist=["claude-*"],
            allowlist=["gpt-*"],
        )
        ids = {m["id"] for m in result}
        assert ids == {"gpt-4o", "gpt-3.5-turbo"}

    def test_exact_match_glob_still_works(self):
        # fnmatch treats strings without wildcards as literals
        result = filter_models(SAMPLE_MODELS, denylist=["gpt-4o"])
        ids = {m["id"] for m in result}
        assert ids == {"gpt-3.5-turbo", "claude-3-opus", "llama-3"}
