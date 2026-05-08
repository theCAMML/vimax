#!/usr/bin/env python3
"""ViMax runner script for Hermes fleet.

Usage:
    python run_vimax.py --idea "Your idea here" [--requirement "Constraints"] [--style "Style"] [--output /path/to/output.mp4] [--clean]

This script:
1. Loads API keys from Hermes .env files
2. Sets up the ViMax environment
3. Runs the idea2video pipeline
4. Copies the final video to the specified output path
"""

import argparse
import asyncio
import json
import os
import shutil
import sys

VIMAX_DIR = "/home/thecamel/muse-workspace/ViMax"
VIMAX_VENV = os.path.join(VIMAX_DIR, ".venv")
CONFIG_PATH = os.path.join(VIMAX_DIR, "configs", "fleet_hybrid.yaml")
HERMES_ENV = os.path.expanduser("~/.hermes/.env")
MUSE_ENV = os.path.expanduser("~/.hermes/profiles/muse/.env")


def load_env(path):
    """Load .env file key=value pairs into a dict (skipping comments)."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env


def setup_keys():
    """Load API keys from Hermes env files into os.environ."""
    # Merge: MUSE env overrides main env
    env = {**load_env(HERMES_ENV), **load_env(MUSE_ENV)}

    for key in ["OPENROUTER_API_KEY", "GEMINI_API_KEY"]:
        if key in env and env[key] and key not in os.environ:
            os.environ[key] = env[key]

    missing = []
    for key in ["OPENROUTER_API_KEY", "GEMINI_API_KEY"]:
        if not os.environ.get(key):
            missing.append(key)

    if missing:
        print(f"❌ Missing API keys: {', '.join(missing)}")
        print(f"   Add them to {MUSE_ENV}")
        sys.exit(1)

    print(f"✅ API keys loaded")


async def run_pipeline(idea, requirement, style, clean):
    # Add ViMax to path
    sys.path.insert(0, VIMAX_DIR)
    os.chdir(VIMAX_DIR)

    if clean:
        workdir = os.path.join(VIMAX_DIR, ".working_dir", "fleet_hybrid")
        if os.path.exists(workdir):
            shutil.rmtree(workdir)
            print(f"🧹 Cleaned working directory: {workdir}")

    # Patch config to use env var values
    import yaml

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    # Resolve ${ENV_VAR} placeholders in config
    for section_key in ["chat_model", "image_generator", "video_generator"]:
        section = config.get(section_key, {})
        init_args = section.get("init_args", {})
        for k, v in list(init_args.items()):
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_key = v[2:-1]
                env_val = os.environ.get(env_key, "")
                if env_val:
                    init_args[k] = env_val
                else:
                    print(f"❌ Config references ${{{env_key}}} but it's not set")
                    sys.exit(1)

    # Write resolved config to temp file
    tmp_config = os.path.join(VIMAX_DIR, "configs", "_resolved.yaml")
    with open(tmp_config, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    from pipelines.idea2video_pipeline import Idea2VideoPipeline

    print(f"🚀 Starting ViMax pipeline...")
    print(f"   Idea: {idea[:80]}...")
    print(f"   Requirement: {requirement}")
    print(f"   Style: {style}")

    pipeline = Idea2VideoPipeline.init_from_config(tmp_config)
    result = await pipeline(
        idea=idea,
        user_requirement=requirement,
        style=style,
    )

    print(f"\n🎬 Final video: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description="ViMax idea-to-video runner")
    parser.add_argument("--idea", required=True, help="Video idea/concept")
    parser.add_argument("--requirement", default="3 scenes max, each scene no more than 5 shots", help="User requirements/constraints")
    parser.add_argument("--style", default="Realistic, cinematic", help="Visual style")
    parser.add_argument("--output", help="Copy final video to this path")
    parser.add_argument("--clean", action="store_true", help="Delete cached working directory before running")

    args = parser.parse_args()

    setup_keys()
    result = asyncio.run(run_pipeline(args.idea, args.requirement, args.style, args.clean))

    if args.output and result and os.path.exists(result):
        shutil.copy2(result, args.output)
        print(f"📋 Copied to: {args.output}")


if __name__ == "__main__":
    main()
