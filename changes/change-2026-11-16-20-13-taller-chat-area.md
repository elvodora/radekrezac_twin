# Change 2026-11-16 20:13 - Taller chat area

## Summary

The chat message area now scales with the window height instead of Gradio's fixed 400px default.

## Root cause

- Measured in a 1440x900 browser: the message area (`.bubble-wrap`) was 398px, which is Gradio's `gr.Chatbot` default `height=400`.
- The existing CSS rule `.chatbot { min-height: 460px }` in `src/styles.py` matches no element in Gradio 6.32. There is no `.chatbot` class, so CSS cannot set this height.

## Files

- `src/app.py`: `gr.Chatbot(show_label=False, height="70vh", min_height=460)`.
- `AGENTS.md`: notes that the chat height is set on the component, not in CSS.

## Verification

- Same 1440x900 browser: the message area is now 628px (70% of 900), up from 398px. Checked with a screenshot.
- On a 900px-tall window the page is now 1126px, so the input box sits about 225px below the fold and the page scrolls.
