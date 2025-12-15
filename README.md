# 3-Minute Video Automation Tool

## Quick Start for Antigravity (AI Agent)

If you are opening this repository for the first time in Antigravity (or another AI agent), copy and paste the following prompt to get started immediately:

```text
Initialize the 3-minute video automation environment:

1. Run `chmod +x setup.sh && ./setup.sh` to install all dependencies (Python, ImageMagick, etc.).
2. Read `agent_operation_manual.md` to understand the workflow and your core directives.
3. Read `prompt_3min.md` to understand the strict script generation rules.

Once completed, report that you are ready to create a video using `python3 main.py new [ProjectName]`.
```

## Manual Usage

1. **Setup**: Run `./setup.sh`
2. **Create Project**: `python3 main.py new [ProjectName] --url [YouTubeURL]`
3. **Generate Script**: Use `prompt_3min.md` with an LLM.
4. **Run Pipeline**: `python3 main.py run [ProjectName]`
5. **Cleanup**: Delete the `projects/[ProjectName]` folder when done.
