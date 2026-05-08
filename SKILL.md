---
name: vimax
description: "ViMax multi-agent video generation — idea-to-video pipeline for MUSE. Uses OpenRouter LLM + Google Gemini image/video gen. No yunwu, no Chinese proxies."
version: 1.1.0
category: creative
triggers:
  - generate video from idea
  - create video from concept
  - vimax
  - idea to video
  - multi-agent video
---

# ViMax — Multi-Agent Video Generation

ViMax generates narrative videos from a text idea using coordinated AI agents:
Screenwriter → Character Extractor → Portrait Generator → Storyboard Artist → Camera/Image Gen → Video Gen → Final Concatenation

## Prerequisites

- **ViMax repo**: `/home/thecamel/muse-workspace/ViMax/`
- **ViMax venv**: `/home/thecamel/muse-workspace/ViMax/.venv/`
- **API keys needed** (in `~/.hermes/profiles/muse/.env`):
  - `OPENROUTER_API_KEY` — for LLM calls (Gemini Flash via OpenRouter)
  - `GEMINI_API_KEY` — for image + video generation (Google AI Studio Tier 1 — paid)
- **Config**: `/home/thecamel/muse-workspace/ViMax/configs/fleet_hybrid.yaml`

## Setup (first time only)

If `GEMINI_API_KEY` is not set:
1. Go to https://aistudio.google.com/app/apikey
2. Create an API key and set up billing (Tier 1 required for Veo — free tier has no video gen access)
3. Add to `~/.hermes/profiles/muse/.env`: `GEMINI_API_KEY=<key>`

## Running

### Preferred: runner script (handles API key injection + config resolution)

```bash
cd /home/thecamel/muse-workspace/ViMax && source .venv/bin/activate
python <skill-dir>/scripts/run_vimax.py --idea "Your idea" --style "Realistic, cinematic" --output /mnt/c/Users/chadn/Downloads/output.mp4
```

The runner auto-loads API keys from Hermes `.env` files and resolves `${ENV_VAR}` placeholders in the config. Use `--clean` to wipe cached intermediates and start fresh.

### Manual: Idea to Video

```bash
cd /home/thecamel/muse-workspace/ViMax && source .venv/bin/activate

# Must export keys manually — ViMax doesn't read .env files
export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY ~/.hermes/.env | grep -v '^#' | head -1 | cut -d= -f2)
export GEMINI_API_KEY=$(grep GEMINI_API_KEY ~/.hermes/profiles/muse/.env 2>/dev/null | grep -v '^#' | head -1 | cut -d= -f2 || grep GEMINI_API_KEY ~/.hermes/.env | grep -v '^#' | head -1 | cut -d= -f2)

# Config must have literal API key values — ${VAR} placeholders won't resolve via main_*.py
python main_idea2video.py
```

### Manual: Script to Video (skip story generation)

```bash
cd /home/thecamel/muse-workspace/ViMax && source .venv/bin/activate
# Same key exports as above
python main_script2video.py
```

## Config Details

`fleet_hybrid.yaml` uses (Tier 1 — Paid Gemini API):
- **LLM**: `google/gemini-2.5-flash-preview-05-20` via OpenRouter (~$0.10/video for text tasks)
- **Image gen**: `ImageGeneratorNanobananaGoogleAPI` via Google API ($0.039/image, 30 RPM)
- **Video gen**: `VideoGeneratorVeoGoogleAPI` with `veo-3.1-fast-generate-preview` ($0.10/sec 720p, 4 RPM)

### Rate Limits

Image gen: 30 requests/min, 1000/day (Tier 1)
Video gen: 4 requests/min, 50/day (Tier 1 Fast)

### Cost Estimate (Tier 1 — Paid)

Per 3-scene video (~15 shots, 8 sec each):
- LLM (story + script + storyboard + character extraction): ~$0.10
- Image gen (~20 images: portraits + frames): ~$0.78 ($0.039/image)
- Video gen (15 clips × 8 sec × $0.10/sec): ~$12.00
- **Total: ~$13 per video** (Fast 720p)

| Video model | Per 8s clip | 15-clip video | Quality |
|-------------|------------|---------------|---------|
| Veo 3.1 Fast (720p) | $0.80 | ~$12 | Fast |
| Veo 3.1 Standard (720p) | $3.20 | ~$48 | Best |
| Veo 3.1 Lite (720p) | $0.40 | ~$6 | Budget |

## Architecture

```
Idea → Screenwriter → Story → CharacterExtractor → Characters
                                          ↓
                              CharacterPortraitsGenerator → Portrait images
                                          ↓
                  Story + StoryboardArtist → Shot descriptions
                                          ↓
                    CameraImageGenerator → Frame images per shot
                                          ↓
                    VideoGenerator (Veo) → Video clips per shot
                                          ↓
                              MoviePy → Final concatenated video
```

## Output

- Working directory: `/home/thecamel/muse-workspace/ViMax/.working_dir/fleet_hybrid/`
- Final video: `.working_dir/fleet_hybrid/final_video.mp4`
- Intermediate: `characters.json`, `character_portraits/`, `shots/`, `script.json`, `story.txt`

## Pitfalls

1. **GEMINI_API_KEY must be set** — pipeline will crash on image gen without it. The runner script auto-loads from Hermes `.env` files; if running `main_*.py` directly, you must export keys manually AND put literal values in the YAML config (not `${VAR}` placeholders — `yaml.safe_load()` treats those as strings).
2. **Video gen rate limit (4 RPM, 50/day on Tier 1 Fast)** — a 3-scene video with ~15 shots takes ~4 minutes for video generation. Cost: ~$12/video at Fast 720p. Switch to Standard ($0.40/sec) or Lite ($0.05/sec) in config to trade cost vs quality.
3. **Working dir caching** — ViMax caches intermediate results. If a run fails partway, re-running skips completed steps. To start fresh, delete `.working_dir/fleet_hybrid/` or use `--clean` flag with the runner.
4. **moviepy concatenation** — can be finicky with different resolutions. ViMax handles this internally.
5. **Aspect ratio** — default is 16:9 landscape. For Instagram Reels (9:16), you'd need to post-process the output or modify the config.
6. **No yunwu** — all yunwu backend files have been stripped from this installation. Do not re-add them.
7. **`size` vs `aspect_ratio` bug** — `script2video_pipeline.py` calls `image_generator.generate_single_image(size="1600x900")` but the Google backend expects `aspect_ratio="16:9"`. The `size` kwarg is silently ignored via `**kwargs`. Frames may generate at default aspect ratio instead of 16:9. See `references/setup-gotchas.md` for the fix.
8. **python3.12-venv may not be installed** — on this WSL setup, `python3.12 -m venv` fails without sudo. Use `uv venv .venv --python python3.12` instead.
9. **pyproject.toml needs package discovery** — original ViMax fails `pip install -e .` with "Multiple top-level packages discovered." Fix is in `references/setup-gotchas.md`.
10. **Tsinghua PyPI mirror removed** — original `pyproject.toml` defaults to `pypi.tuna.tsinghua.edu.cn` (Chinese mirror). Removed for data sovereignty. Don't re-add.

## Scripts

- `scripts/run_vimax.py` — CLI runner: handles API key loading from Hermes `.env`, `${ENV_VAR}` config resolution, clean restarts, and output copying. Preferred way to invoke the pipeline.

## References

- `references/setup-gotchas.md` — installation issues (setuptools flat-layout, Tsinghua mirror, venv creation, `size`/`aspect_ratio` mismatch, security audit summary)

## Security Audit

- Performed 2026-05-07. 16 findings, all MEDIUM/LOW.
- Only concern was yunwu.ai (Chinese API proxy) — all 4 yunwu backend files removed.
- No malware, no data exfiltration, no RCE, no credential harvesting found.
- Base64 usage in `utils/image.py` is benign (PIL image serialization).
