# Blueprint: o2cfg

**Purpose:** A CLI tool that connects to an OpenAI-compatible API endpoint, discovers all available models via `/v1/models`, and outputs the resulting opencode provider configuration to stdout (or writes it to a file with `--output`).

---

## 1. System Goals

- Fetch the complete list of models from any OpenAI-compatible server endpoint.
- Generate valid opencode provider config containing connection information and discovered models.
- Require minimal user input: only a base URL. The API key is optional and used for authenticated endpoints. Endpoints that do not require authentication work without a key.
- Output goes to stdout by default so it can be viewed or piped to a file (`> opencode.json`). Use `--output <path>` to write directly to disk. Discovery failure produces a warning but the tool still emits valid config with an empty models map.

---

## 2. Component Hierarchy

```
CLI Layer (argparse entry point)
  |
  v
Config Resolver (--args + environment variables -> resolved settings)
  |
  v
OpenAI Client (HTTP client with timeout, auth header, error handling)
  |
  |-- GET /v1/models --> raw model list payload
   |
   v
  Model Filter (apply denylist first, then allowlist to narrow the set; patterns use fnmatch glob syntax; no-op when both absent or empty)
  |
  v
Model Mapper (transform filtered API model objects into opencode schema format)
  |
  v
Output Writer (serialize resolved config to stdout or file path)
```

---

## 3. Data Flow

1. **User invokes CLI** with arguments (flags, environment variables).
2. **Argparse parses** flags, applies defaults, sets verbosity level.
3. **Config Resolver** merges CLI args and environment variables into a single settings object:
    - Required: `base_url`
    - Optional (auto-resolved if unset): `provider_name`, `provider_npm`, `model_default_limits`
     - When `--output` is omitted, `output_file_path` is null — the formatted JSON is written to stdout and no file is created on disk. No environment variable controls this behavior; only the CLI flag.

4. **OpenAI Client** sends `GET /v1/models?timeout=<t>`:
   - If `api_key` is provided, sets `Authorization: Bearer <key>` header.
   - If `api_key` is not provided, sends the request with no Authorization header. Many OpenAI-compatible endpoints (self-hosted on private networks) accept unauthenticated calls to the models list endpoint. The discovery attempt is best-effort; network or auth failures produce a warning and do not abort the run.
5. **Response is parsed:** a JSON object containing `"data": [{ "id", "object", ... }]`.
6. **Model Filter** applies denylist first, then allowlist, to the parsed model set. Each entry is treated as a glob pattern matched against model IDs using Unix shell-style wildcards (``*``, ``?``, ``[seq]``, ``[!seq]``). Strings without wildcards are exact matches. When neither flag is given all discovered models pass through unchanged. An empty allowlist results in zero models included (the output file has `"models": {}`).
7. **Model Mapper** iterates each model and builds the opencode-per-model structure, extracting available context/output limit metadata if present (otherwise storing `null` for discovery via environment).
8. **Output Writer** serializes the config document:
    - When `output_file_path` is null, write JSON to stdout directly (fd 1). No warnings are ever written to stdout — they go to stderr only so the two streams never mix.
    - When `output_file_path` is set, serialize the config at that path. Write atomically: temporary file in the same directory, then rename. Existing files are overwritten without confirmation.

#### Provider Name Resolution

If `--provider-name` is not given, the config resolver applies this fallback chain:

1. URL derivation — parse `base_url`, extract the hostname (strip scheme and port), take the second-to-last label (the domain name before the TLD), lowercase it, replace `-` or `_` with spaces for readability:
    - `http://localhost:8080/v1` → `"localhost"`
    - `https://api.anthropic.com/v1/` → `"anthropic"`
    - `http://vllm.internal:8000/v1` → `"vllm"`
2. Hardcoded default — if the hostname is empty or unparseable: `"OpenAI-compatible"`.

---

## 4. CLI Interface (Contracts)

### Entry Point

Single positional command (subcommand-free). The program is invoked directly with options:

```
o2cfg [options]
```

### Arguments

| Short | Long                    | Type | Required | Default         | Description                                      |
|-------|-------------------------|------|----------|-----------------|--------------------------------------------------|
| `-h`  | `--help`                | flag | N        | (auto)          | Show help message and exit.                      |
| `-V`  | `--version`             | flag | N        | (auto)          | Print version and exit.                          |
| `-v, -vv, -vvv` | `--verbosity`   | level| N        | `error`         | Set verbosity: no flag (error), -v (warning), -vv (info), -vvv (debug). |
| `-u`  | `--url [URL]`           | url  | Y*       | env `OPENAI_BASE_URL` | Base URL of the OpenAI-compatible endpoint (e.g. `http://localhost:8080/v1`). The program appends `/v1/models` automatically. If the supplied URL already ends with `/v1`, it is used as-is. |
| `-k`  | `--api-key [KEY]`       | str  | N        | env `OPENAI_API_KEY` | Bearer token for authenticated endpoints. Discovery always runs — if no key is given, request goes to the API without an Authorization header (many self-hosted servers do not require auth for model listing). Written to `.provider.<name>.options.apiKey` in the output when provided. |
| `-o`  | `--output [FILE]`       | path | N        | stdout         | File path to write the generated config. When omitted, the formatted JSON is printed to stdout so it can be viewed or piped. Omitting this flag means no file is written to disk. |
| `-n`  | `--provider-name [NAME]`| str  | N        | auto-resolved    | Display name for the provider entry in the output. When omitted, resolved by fallback chain: CLI flag > URL hostname derivation > hardcoded `"OpenAI-compatible"`. |
| `-p`  | `--provider-provider [PKG]` | str | N       | `@ai-sdk/openai-compatible` | npm package name for the provider adapter. |
| `-t`  | `--timeout [SECONDS]`              | int   | N        | `30`                   | HTTP request timeout in seconds (1-300).                                           |
| `-C`  | `--model-context-limit [TOKENS]`   | int   | N        | null                   | Global override for context token limit when API returns no value.               |
| `-O`  | `--model-output-limit [TOKENS]`    | int   | N        | null                   | Global override for output token limit when API returns no value.                |
| `-a`  | `--allowlist [ID1,ID2,...]` | list  | N        | (all discovered)       | After discovery, keep only models whose IDs match any comma-separated glob pattern (``*``, ``?``, ``[seq]``, ``[!seq]``).  For example, ``gpt-*`` matches ``gpt-4o`` and ``gpt-3.5-turbo``.    |
| `-d`  | `--denylist [ID1,ID2,...]`  | list  | N        | (none)                 | After discovery, remove models whose IDs match any comma-separated glob pattern.  Strings without wildcards are treated as exact matches.    |

\* Required unless the corresponding environment variable (`OPENAI_BASE_URL`) is set.

### Verbosity Levels

| Flag  | Level   | Output                                    |
|-------|---------|-------------------------------------------|
| (none)    | error    | Errors only                                |
| `-v`      | warning  | Warnings and errors only                   |
| `-vv`     | info     | Warnings, errors, and operational progress |
| `-vvv`    | debug    | Full request/response logging              |

---

## 5. Payload Schema: OpenAI API `/v1/models` Response

The program expects the standard OpenAI models endpoint response structure from the upstream spec:

```jsonc
{
  "object": "list",
  "data": [
    {
      "id": string,                  // model identifier (required)
      "object": string,              // always "model"
      "created": number,             // unix timestamp
      "owned_by": string,            // owner name
      "permission": [...],           // optional; varies by server implementation
      ...                            // other fields as returned by the server (ignored)
    }
  ]
}
```

**Field usage rules:**

- `"id"` is the only mandatory field per model. It becomes the opencode model key and name.
- Context/output limits, if present in custom or extended model objects from compatible servers, are extracted and mapped. Missing values fall back to CLI overrides or `null` placeholders.
- Unused/unsupported fields are silently ignored (auto-discovery of as much metadata as possible, best-effort).

---

## 6. Payload Schema: Output `opencode.json`

Models are populated by discovery on every run (unless the API call fails). The only structural difference is whether an `apiKey` appears inside `options`:

### With no API key

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "<provider-name>": {
      "name": "<display-name>",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "<resolved-base-url>"
      },
      "models": {
        "<model-id>": {
          "name": "<model-id>",
          "limit": {
            "context": <integer-or-null>,
            "output": <integer-or-null>
          }
        }
      }
    }
  }
}
```

The `limit` field is optional. It is omitted when both `context` and `output` are `null` and no CLI override (`--model-context-limit`, `--model-output-limit`) is set. If at least one value is non-null, the `limit` field is included with only the non-null values present.

### With API key

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "<provider-name>": {
      "name": "<display-name>",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "<resolved-base-url>",
        "apiKey": "<api-key-value>"
      },
      "models": {
        "<model-id>": {
          "name": "<model-id>",
          "limit": {
            "context": <integer-or-null>,
            "output": <integer-or-null>
          }
        }
      }
    }
  }
}
```

The `limit` field follows the same omission rule: omitted when both values are `null` and no CLI override is set. Only non-null values are included in the `limit` object.

`allowlist` and `denylist` are NOT written into the output. They are applied as filters during discovery to narrow which discovered models appear in the `models` map.

---

## 7. Environment Variables

| Variable            | Required | Description                                   |
|---------------------|----------|-----------------------------------------------|
| `OPENAI_BASE_URL`   | N        | Base URL when `--url` flag is omitted.        |
| `OPENAI_API_KEY`    | N        | API key when `--api-key` flag is omitted.     |

When neither `--url` nor `OPENAI_BASE_URL` is set, the tool prints a usage hint to stderr and exits with code 2. The API key is optional — discovery always runs regardless of whether authentication data is provided.

---

## 8. State Management

The application runs stateless, single-invocation. No persistent state is maintained between runs. All mutable state flows through the request lifecycle:

```
settings object (in-memory) ---> HTTP client instance (per-invocation) --> config document (in-memory) --> stdout or file write --> exit
```

---

## 9. Persistence

### Input: None

No databases, caches, or local state reads before discovery.

### Output: stdout or file

When `--output` is omitted:
- JSON config is printed to stdout as pretty-printed text with indent 2 and a trailing newline. Nothing else is written to stdout.
- Warnings and errors still go to stderr so they cannot be confused with the JSON payload.

When `--output <path>` is provided:
- Written atomically if the platform supports it (`tempfile` approach: write to a temp file in the same directory, then rename).
- The output directory must exist; missing parent directories cause a clear error instead of a traceback.
- Existing files at the destination are overwritten without confirmation.

---

## 10. Error Boundaries & Handling

| Failure Mode                     | Behavior                                                             | Exit Code |
|----------------------------------|----------------------------------------------------------------------|-----------|
| No base URL (flag + env both set)| Print usage hint for missing `--url` to stderr.                       | `2`       |
| API call fails (no key or bad key)            | Log the network error; include an empty models map in the output.                               | `0`       |
| Network unreachable / timeout | Log error message with the failed URL; suggest checking connectivity | `1` |
| Non-200 HTTP response         | Log status code and body (if available, redacted).    | `1`       |
| Invalid JSON from API         | Log parsing error with context                        | `1`       |
| Write permission denied       | Log the filesystem path that could not be written.    | `1`       |
| Fatal internal error          | Print stack trace only at debug level; plain message otherwise | `1` |

Empty catch blocks are forbidden. All caught errors must either be handled with a user-facing fallback or re-thrown wrapped in a context-specific exception type.

---

## 11. Network & Resilience

- HTTP requests to the upstream API carry a configurable timeout (default 30 seconds).
- No retries by default; the user can re-run the command. Retries are out of scope for v1.
- The authorization header uses the Bearer scheme and is never logged at any verbosity level below debug. At debug level, only the URL and status code are logged; the API key itself is redacted (`Bearer sk-****`).

---

## 12. Security Constraints

- `OPENAI_API_KEY` / `--api-key`: kept in memory during the invocation and written verbatim into `.provider.<name>.options.apiKey` in the output file when provided. Never logged at any verbosity level.
- Input validation: `base_url` must be a valid URI with scheme `http` or `https`. Other schemes cause a hard error.
- Path traversal guard: the output file path is resolved and a parent-directory check prevents writes outside the requested location.

---

## 13. Auto-Discovery Behavior

From the OpenAI-compatible API response, the program extracts the following per model (best-effort):

| Mapped Field     | Source on API Side                              | Fallback                  |
|------------------|------------------------------------------------|---------------------------|
| `models.<id>` key | `"id"` field                                  | (required; error if missing) |
| `name`           | `"id"` field                                   | same as key                |
| `limit.context`  | `"max_input_tokens"`, `"context_length"`, or other known custom fields | CLI override, then `null` |
| `limit.output`   | `"max_output_tokens"` or other known custom fields | CLI override, then `null` |

Any additional top-level fields in the model object not mapped above are ignored. The design favors extensibility: field-mapping rules live in a single isolated module so future API changes require updates in only one place.
