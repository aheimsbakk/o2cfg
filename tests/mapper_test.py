"""Tests for o2cfg Model Mapper."""

import pytest
from o2cfg.mapper import map_model, map_models, _extract_limit


class TestExtractLimit:
    """Test limit extraction from model objects."""

    def test_first_matching_field(self):
        model = {"max_input_tokens": 100, "context_length": 200}
        result = _extract_limit(model, ["max_input_tokens", "context_length"], None)
        assert result == 100

    def test_skips_non_int(self):
        model = {"max_input_tokens": "not-a-number", "context_length": 200}
        result = _extract_limit(model, ["max_input_tokens", "context_length"], None)
        assert result == 200

    def test_skips_zero(self):
        model = {"max_input_tokens": 0, "context_length": 200}
        result = _extract_limit(model, ["max_input_tokens", "context_length"], None)
        assert result == 200

    def test_skips_negative(self):
        model = {"max_input_tokens": -1, "context_length": 200}
        result = _extract_limit(model, ["max_input_tokens", "context_length"], None)
        assert result == 200

    def test_returns_fallback_when_not_found(self):
        model = {"owned_by": "test"}
        result = _extract_limit(model, ["max_input_tokens"], 50000)
        assert result == 50000

    def test_returns_fallback_none(self):
        model = {"owned_by": "test"}
        result = _extract_limit(model, ["max_input_tokens"], None)
        assert result is None

    def test_no_fields_list(self):
        model = {"max_input_tokens": 100}
        result = _extract_limit(model, [], 50000)
        assert result == 50000


class TestMapModel:
    """Test single model mapping."""

    def test_minimal_model_no_limit(self):
        model = {"id": "gpt-4o", "object": "model", "owned_by": "openai"}
        result = map_model(model)
        assert result["name"] == "gpt-4o"
        assert "limit" not in result

    def test_model_with_limits(self):
        model = {
            "id": "gpt-4o",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
        }
        result = map_model(model)
        assert result["name"] == "gpt-4o"
        assert result["limit"]["context"] == 128000
        assert result["limit"]["output"] == 4096

    def test_model_with_context_length(self):
        model = {
            "id": "claude-3",
            "context_length": 200000,
            "max_output_tokens": 8192,
        }
        result = map_model(model)
        assert result["limit"]["context"] == 200000
        assert result["limit"]["output"] == 8192

    def test_global_context_override(self):
        model = {"id": "basic-model"}
        result = map_model(model, context_limit=50000, output_limit=10000)
        assert result["limit"]["context"] == 50000
        assert result["limit"]["output"] == 10000

    def test_api_value_overrides_global(self):
        model = {
            "id": "gpt-4o",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
        }
        result = map_model(model, context_limit=50000, output_limit=10000)
        assert result["limit"]["context"] == 128000
        assert result["limit"]["output"] == 4096

    def test_limit_included_when_only_context_set(self):
        model = {"id": "basic-model"}
        result = map_model(model, context_limit=50000)
        assert result["name"] == "basic-model"
        assert "limit" in result
        assert result["limit"]["context"] == 50000
        assert "output" not in result["limit"]

    def test_limit_included_when_only_output_set(self):
        model = {"id": "basic-model"}
        result = map_model(model, output_limit=10000)
        assert result["name"] == "basic-model"
        assert "limit" in result
        assert "context" not in result["limit"]
        assert result["limit"]["output"] == 10000

    def test_missing_id_raises(self):
        model = {"object": "model"}
        with pytest.raises(ValueError, match="missing required 'id' field"):
            map_model(model)

    def test_empty_id_raises(self):
        model = {"id": ""}
        with pytest.raises(ValueError, match="missing required 'id' field"):
            map_model(model)

    def test_vision_stanza_applied_on_match(self):
        model = {"id": "gpt-4o"}
        result = map_model(model, vision_patterns=["gpt-4o"])
        assert result["name"] == "gpt-4o"
        assert result["attachment"] is True
        assert result["modalities"] == {
            "input": ["text", "image"],
            "output": ["text"],
        }

    def test_vision_stanza_not_applied_on_no_match(self):
        model = {"id": "gpt-3.5-turbo"}
        result = map_model(model, vision_patterns=["gpt-4o"])
        assert result["name"] == "gpt-3.5-turbo"
        assert "attachment" not in result
        assert "modalities" not in result

    def test_vision_stanza_with_glob_pattern(self):
        model = {"id": "gpt-4o-mini"}
        result = map_model(model, vision_patterns=["gpt-4o-*"])
        assert result["attachment"] is True
        assert result["modalities"] == {
            "input": ["text", "image"],
            "output": ["text"],
        }

    def test_vision_stanza_with_multiple_patterns(self):
        model = {"id": "claude-3-opus"}
        result = map_model(model, vision_patterns=["gpt-4o", "claude-3-opus"])
        assert result["attachment"] is True

    def test_vision_stanza_none_patterns_no_effect(self):
        model = {"id": "gpt-4o"}
        result = map_model(model, vision_patterns=None)
        assert "attachment" not in result
        assert "modalities" not in result

    def test_vision_stanza_with_limits(self):
        model = {
            "id": "gpt-4o",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
        }
        result = map_model(model, vision_patterns=["gpt-4o"])
        assert result["name"] == "gpt-4o"
        assert result["limit"]["context"] == 128000
        assert result["limit"]["output"] == 4096
        assert result["attachment"] is True
        assert result["modalities"] == {
            "input": ["text", "image"],
            "output": ["text"],
        }


class TestMapModels:
    """Test bulk model mapping."""

    def test_maps_all_models(self):
        models = [
            {"id": "gpt-4o", "max_input_tokens": 128000, "max_output_tokens": 4096},
            {"id": "gpt-3.5", "max_input_tokens": 16385, "max_output_tokens": 4096},
        ]
        result = map_models(models)
        assert len(result) == 2
        assert "gpt-4o" in result
        assert "gpt-3.5" in result
        assert result["gpt-4o"]["limit"]["context"] == 128000

    def test_skips_models_without_id(self):
        models = [
            {"id": "gpt-4o"},
            {"object": "model"},  # no id
        ]
        result = map_models(models)
        assert len(result) == 1
        assert "gpt-4o" in result

    def test_empty_list(self):
        result = map_models([])
        assert result == {}

    def test_global_limits_applied(self):
        models = [
            {"id": "model-a"},
            {"id": "model-b"},
        ]
        result = map_models(models, context_limit=100000, output_limit=32000)
        assert result["model-a"]["limit"]["context"] == 100000
        assert result["model-a"]["limit"]["output"] == 32000
        assert result["model-b"]["limit"]["context"] == 100000
        assert result["model-b"]["limit"]["output"] == 32000

    def test_model_names_match_ids(self):
        models = [{"id": "custom-model-id"}]
        result = map_models(models)
        assert result["custom-model-id"]["name"] == "custom-model-id"

    def test_vision_applied_only_to_matching_models(self):
        models = [
            {"id": "gpt-4o"},
            {"id": "gpt-3.5-turbo"},
            {"id": "gpt-4o-mini"},
        ]
        result = map_models(models, vision_patterns=["gpt-4o*"])
        assert result["gpt-4o"]["attachment"] is True
        assert "attachment" not in result["gpt-3.5-turbo"]
        assert result["gpt-4o-mini"]["attachment"] is True

    def test_vision_empty_list_no_effect(self):
        models = [{"id": "gpt-4o"}]
        result = map_models(models, vision_patterns=[])
        assert "attachment" not in result["gpt-4o"]
