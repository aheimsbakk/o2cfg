# o2cfg

Auto-discover models from OpenAI-compatible API endpoints and generate opencode provider configurations.

## What it does

- Connects to an `/v1/models` endpoint and lists all available models
- Writes a valid `opencode.json` provider block with your connection settings plus discovered models
- Sends output to stdout by default so you can review or pipe it to a file

## Quick start

Run o2cfg directly from the repository with `uvx` — no installation needed:

```bash
uvx --from git+https://github.com/aheimsbakk/o2cfg.git o2cfg --url http://localhost:8080/v1 -o opencode.json
```

This downloads the repo and runs the tool in an isolated environment. The result appears in `opencode.json`.

## Install from source

Clone the repository and install with uv:

```bash
git clone https://github.com/aheimsbakk/o2cfg.git
cd o2cfg
uv venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
uv pip install -e ".[test]"
```

## Run it

Basic usage — provide your API endpoint URL. The tool prints configuration to stdout. You can save the output to a file using the `--output` flag or shell redirection:

### Generate config to stdout

```bash
o2cfg --url http://localhost:8080/v1
```

Output goes to your terminal. Pipe it to a file to skip the flag:

```bash
o2cfg --url http://localhost:8080/v1 > opencode.json
```

### Generate config to a file directly

```bash
o2cfg --url http://localhost:8080/v1 --api-key my-key -o opencode.json
```

The tool writes the JSON straight to disk.

### Connect to an API that requires authentication

```bash
o2cfg --url https://api.example.com/v1 --api-key sk-prod-abc123
```

Discovery runs regardless. The only difference is that your key gets written into the configuration so opencode can use authenticated API calls later.

### Set environment variables instead of flags

```bash
export OPENAI_BASE_URL=https://api.example.com/v1
o2cfg  # reads URL from env var, writes to stdout
```

You can also set `OPENAI_API_KEY` if you need authentication but prefer not to pass flags.

## Filtering models

Use filters to narrow the discovered model list:

### Only include specific models

```bash
o2cfg --url http://localhost:8080/v1 -a gpt-4o,o1,phi-3
```

Only models with IDs `gpt-4o`, `o1`, or `phi-3` appear in the output.

### Exclude specific models

```bash
o2cfg --url http://localhost:8080/v1 -d text-davinci-001,whisper-1
```

The listed models are removed from the result.

### Combine both

```bash
o2cfg --url http://localhost:8080/v1 -a gpt-4o,o1,gpt-3.5-turbo -d gpt-3.5-turbo
```

First removes anything in the deny list, then keeps only models in the allow list.

## Configuration options

All flags are listed below. When a flag has environment variable support, that is the fallback if you omit it on the command line:

| Flag                             | Short  | Required       | Description                                      |
|----------------------------------|--------|----------------|--------------------------------------------------|
| `--url <URL>`                    | `-u`   | Yes*           | API endpoint URL (e.g. `http://localhost:8080/v1`). Appends `/v1/models` automatically. |
| `--api-key <KEY>`                | `-k`   | No             | Bearer token for authenticated endpoints. Discovery runs regardless — if no key is present, o2cfg calls `/v1/models` without an Authorization header. Written to `.options.apiKey` in the output when provided. |
| `--output <PATH>`                | `-o`   | No             | File path to write the result. If omitted, the JSON is sent to stdout so you can view it or pipe it. |
| `--provider-name <NAME>`         | `-n`   | No             | Display name for the provider section. If omitted, o2cfg derives it from the URL hostname. |
| `--provider-provider <PKG>`      | `-p`   | No             | npm package name for the provider adapter. Default: `@ai-sdk/openai-compatible`. |
| `--timeout <SECONDS>`            | `-t`   | No             | Request timeout in seconds (1–300). Defaults to 30. |
| `--model-context-limit <TOKENS>` | `-C`   | No             | Global override for context token limit when the API returns no value. |
| `--model-output-limit <TOKENS>`  | `-O`   | No             | Global override for output token limit when the API returns no value. |
| `--allowlist <MODELS>`           | `-a`   | No             | Comma-separated list of model IDs to keep. Discovered models not in this list are excluded from the result. |
| `--denylist <MODELS>`            | `-d`   | No             | Comma-separated list of model IDs to exclude, even if they were discovered. |
| `-v, -vv, -vvv`                  |        | No             | Verbosity: no flag (error), `-v` (warning), `-vv` (info), `-vvv` (debug). Default: error. |
| `-V`                             |        | No             | Print version and exit. |

\* `--url` can be replaced by the `OPENAI_BASE_URL` environment variable.

### Environment variables

You can set these instead of using command-line flags:

| Variable              | Required | Description                                |
|-----------------------|----------|--------------------------------------------|
| `OPENAI_BASE_URL`     | Yes*     | Falls back when `--url` is omitted.        |
| `OPENAI_API_KEY`      | No       | Falls back when `--api-key` is omitted.    |

\* When neither flag nor environment variable supplies a URL, the tool prints an error message and exits with code 2.

## Output format

Example output with an API key:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "my-provider": {
      "name": "My Provider",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "sk-prod-abc123",
        "baseURL": "https://api.example.com/v1"
      },
      "models": {
        "gpt-4o": {
          "name": "gpt-4o",
          "limit": {
            "context": 128000,
            "output": 4096
          }
        }
      }
    }
  }
}
```

## What happens when the API call fails

The tool does not treat a failed discovery call as fatal. If anything goes wrong while fetching models (network timeout, invalid key, server returns an error), o2cfg prints a warning to stderr and still writes your configuration. The `models` section will be empty in that case, but you can always re-run later when the API is available.

This design lets you set up your opencode provider block first, then add models later without rerunning everything.

## What does not happen by default (safety notes)

- When `--url` is missing and no environment variable supplies it, the tool exits with an error message to stderr.
- Discovery always runs regardless of `--api-key`. A failed call produces a warning and leaves `models` empty; it never aborts the run.
- No files are written unless you use `--output`, `-o` or shell redirection (`> file.json`). Output goes to stdout by default.

## Development

After cloning the repository:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
pytest  # run all tests
```

The project uses only Python standard library modules plus `pytest` for testing. No external runtime dependencies are required.

> [!NOTE]
>
> Architecture (BLUEPRINT.md): Qwen 3.6 35B A3B
> - temp = 1.0, top-p = 0.95, top-k = 20, min-p = 0.0, presence-penalty = 1.5,
repeat-penalty = 1.0
>
> Code: Qwen 3.6 35B A3B
> - temp = 0.6, top-p = 0.95, top-k = 20, min-p = 0.0, presence-penalty = 0.0, repeat-penalty = 1.0
