# Architecture Overview

The pyo stack is organized into small packages under `src/pyo/`:

- `core`: glue components for scheduling, playback, and configuration.
- `io`: interfaces with MIDI devices and future audio engines.
- `ui`: rendering and didactic overlays (console placeholders for now).
- `learning`: lesson models and adaptive logic.

Future documents can expand on:
- Audio synthesis pipeline selection (JUCE bridge, pygame, pedalboard, etc.).
- Visualization strategy for the didactic display.
- Lesson authoring DSL and content pipeline.
