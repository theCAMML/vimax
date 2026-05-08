# ViMax Setup Gotchas

Non-obvious issues encountered during installation and configuration.

## pyproject.toml — setuptools flat-layout error

Original ViMax `pyproject.toml` has no `[tool.setuptools.packages.find]` section. With multiple top-level directories (`agents/`, `assets/`, `configs/`, `interfaces/`, `pipelines/`, `tools/`, `utils/`), `pip install -e .` fails:

```
error: Multiple top-level packages discovered in a flat-layout
```

**Fix**: Add explicit package discovery:
```toml
[tool.setuptools.packages.find]
include = ["agents*", "interfaces*", "pipelines*", "tools*", "utils*"]
```

Exclude `assets/` and `configs/` — they're data, not importable packages.

## Tsinghua PyPI mirror

Original `pyproject.toml` includes:
```toml
[[index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

This is a Chinese mirror (Tsinghua University). Must be removed — CAMML flags Chinese API proxies/services as a data sovereignty risk. Same category as yunwu.ai.

## python3.12-venv not available without sudo

`python3.12 -m venv .venv` fails with "ensurepip is not available" on this WSL setup. `sudo apt install python3.12-venv` requires a password.

**Fix**: Use `uv` instead — ViMax already uses it natively:
```bash
uv venv .venv --python python3.12
uv pip install -e .
```

## Config `${ENV_VAR}` placeholders

The `fleet_hybrid.yaml` config uses `${OPENROUTER_API_KEY}` and `${GEMINI_API_KEY}` placeholder syntax. This is NOT standard YAML — `yaml.safe_load()` reads these as literal strings, not env var references.

**Fix**: The `run_vimax.py` runner script resolves these at runtime by:
1. Loading keys from Hermes `.env` files into `os.environ`
2. Scanning config `init_args` for `${...}` patterns
3. Replacing with actual values from `os.environ`
4. Writing a `_resolved.yaml` temp config for the pipeline

ViMax's own `main_idea2video.py` doesn't handle this — it expects literal API key values in the YAML.

## `size` vs `aspect_ratio` parameter mismatch

The `Script2VideoPipeline` calls `image_generator.generate_single_image()` with `size="1600x900"`, but the Google API backend (`ImageGeneratorNanobananaGoogleAPI`) accepts `aspect_ratio` (e.g. `"16:9"`), not `size`. The `size` kwarg is silently consumed by `**kwargs` and ignored.

**Impact**: Frames generated via `script2video_pipeline.py` use default aspect ratio instead of 16:9. The `idea2video_pipeline.py` doesn't call `generate_single_image` directly (it delegates to agents), so this mainly affects the script-to-video path.

**Fix needed**: Patch `script2video_pipeline.py` to pass `aspect_ratio="16:9"` instead of `size="1600x900"`, or add `size` → `aspect_ratio` conversion in the Google backend.

## Security audit summary (2026-05-07)

16 findings across the ViMax codebase, all MEDIUM/LOW severity:

- **4 yunwu backend files** (`image_generator_doubao_seedream_yunwu_api.py`, `image_generator_nanobanana_yunwu_api.py`, `video_generator_doubao_seedance_yunwu_api.py`, `video_generator_veo_yunwu_api.py`) — Chinese API proxy routing. **All removed.**
- **External URLs** to `yunwu.ai`, `minimax.io`, `openrouter.ai` — API calls only, no data exfiltration.
- **Base64 in `utils/image.py`** — benign PIL image serialization for API transport.
- No malware, RCE, credential harvesting, or data exfiltration patterns found.
