"""Integration tests for o2cfg.__main__ (run function and output writer)."""



from o2cfg.config import Settings
from o2cfg.output import build_config_document


class TestBuildConfigDocument:
    """Test config document construction."""

    def test_without_api_key(self):
        settings = Settings(
            base_url="http://localhost:8080/v1",
            provider_name="localhost",
            provider_npm="@ai-sdk/openai-compatible",
        )
        models_map = {
            "gpt-4o": {
                "name": "gpt-4o",
                "limit": {"context": 128000, "output": 4096},
            }
        }
        doc = build_config_document(settings, models_map)
        assert doc["$schema"] == "https://opencode.ai/config.json"
        assert "provider" in doc
        provider = doc["provider"]["localhost"]
        assert provider["name"] == "localhost"
        assert provider["npm"] == "@ai-sdk/openai-compatible"
        assert provider["options"]["baseURL"] == "http://localhost:8080/v1"
        assert "apiKey" not in provider["options"]
        assert "gpt-4o" in provider["models"]

    def test_with_api_key(self):
        settings = Settings(
            base_url="https://api.example.com/v1",
            api_key="sk-test-123",
            provider_name="my-provider",
            provider_npm="custom-npm",
        )
        models_map = {}
        doc = build_config_document(settings, models_map)
        assert "provider" in doc
        provider = doc["provider"]["my-provider"]
        assert provider["options"]["apiKey"] == "sk-test-123"
        assert provider["options"]["baseURL"] == "https://api.example.com/v1"

    def test_provider_name_with_spaces_becomes_key(self):
        settings = Settings(
            base_url="http://localhost:8080/v1",
            provider_name="My Provider",
        )
        doc = build_config_document(settings, {})
        assert "provider" in doc
        assert "my-provider" in doc["provider"]
        assert "My Provider" not in doc["provider"]
