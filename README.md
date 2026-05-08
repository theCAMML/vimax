# ViMax 🎬

**Multi-agent idea-to-video pipeline for OpenClaw/MUSE.**

Takes a text idea → outputs a full narrative video using coordinated AI agents.

## Stack

- **LLM**: Google Gemini Flash via OpenRouter
- **Image gen**: Google Gemini NanoBanana (Tier 1 paid)
- **Video gen**: Google Veo 3.1 Fast ($0.10/sec, 720p)
- **No yunwu. No Chinese proxies.**

## Pipeline

```
Idea → Screenwriter → CharacterExtractor → PortraitGenerator
                                        ↓
               StoryboardArtist → CameraImageGenerator → VideoGenerator (Veo)
                                        ↓
                              MoviePy → Final video
```

## Cost

~$13/video (3 scenes, 15 shots, 8s each, Fast 720p)

| Model | Per 8s clip | 15-clip video |
|-------|-------------|---------------|
| Veo 3.1 Fast | $0.80 | ~$12 |
| Veo 3.1 Standard | $3.20 | ~$48 |
| Veo 3.1 Lite | $0.40 | ~$6 |

## Usage

```bash
cd /path/to/ViMax && source .venv/bin/activate
python scripts/run_vimax.py --idea "Your idea here" --style "Cinematic" --output ~/output.mp4
```

See `SKILL.md` for full setup, pitfalls, and config details.
See `references/setup-gotchas.md` for installation issues.

## Files

- `SKILL.md` — Full skill doc (OpenClaw compatible)
- `scripts/run_vimax.py` — CLI runner with API key injection
- `references/setup-gotchas.md` — Install fixes and security audit
