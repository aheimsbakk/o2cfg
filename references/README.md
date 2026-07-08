# References

OpenAI specification: https://raw.githubusercontent.com/openai/openai-openapi/refs/heads/main/openapi.yaml
Opencode config specification: https://opencode.ai/config.json

## Example opencode.json

````json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "llama-cpp": {
      "name": "Llama.cpp",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://openai.compatible.foo:8080/v1"
      },
      "models": {
        "qwen-3.6-think-coding": {
          "name": "qwen-3.6-think-coding",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        },
        "qwen-3.6-think-general": {
          "name": "qwen-3.6-think-general",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        },
        "qwen-3.6-think-coding-mtp": {
          "name": "qwen-3.6-think-coding-mtp",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        },
        "qwen-3.6-think-general-mtp": {
          "name": "qwen-3.6-think-general-mtp",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        },
        "gemma-4": {
          "name": "gemma-4",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        },
        "gemma-4-qat-mtp": {
          "name": "gemma-4-qat-mtp",
          "limit": {
            "context": 256000,
            "output": 64000
          }
        }
      }
    }
  }
}
````
