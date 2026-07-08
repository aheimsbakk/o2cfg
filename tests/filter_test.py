"""Tests for o2cfg Model Filter."""

import pytest
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
