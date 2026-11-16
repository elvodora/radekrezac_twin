# Change 2026-11-16 19:55 - Full-width Gradio container

## Summary

The chat UI now uses the full browser width instead of a centered 880px column.

## Files

- `src/styles.py`: in the `.gradio-container` rule, `max-width: 880px` became `max-width: 100%`. Side padding (24px, or 14px on mobile) is unchanged.
- `AGENTS.md`: notes where the layout width is set.

## Verification

- Ran `uv run python -m src.app` locally. The served `/config` CSS contains `max-width: 100% !important` for `.gradio-container`.
- Not checked visually in a browser.
