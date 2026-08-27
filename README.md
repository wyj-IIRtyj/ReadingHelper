# ReadingHelper

<p align="center">
  <strong>A desktop reading companion for translation, vocabulary capture, and text-to-speech.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PySide6-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/Desktop-prototype-6f42c1?style=flat-square" alt="Desktop prototype" />
</p>

ReadingHelper is an experimental desktop app for making long-form reading less interruptive. It watches selected text, turns new selections into readable content blocks, streams translation, keeps a shared vocabulary list, and can generate and play speech for the captured text.

## What it does

- **Selection capture** — monitors newly selected text through a clipboard-based workflow.
- **Streaming translation** — adds translated content without blocking the main interface.
- **Vocabulary cards** — tracks selected words and loads reusable dictionary data.
- **Text-to-speech** — generates audio and maintains a playback queue across captured blocks.
- **Persistent reading state** — saves vocabulary and reading-related data between sessions.
- **Custom desktop UI** — uses PySide6 widgets, animated content blocks, and a dedicated bottom control bar.

## Architecture

```text
selected text
    │
    ▼
text_collection ──► content block ──► translation stream
                        │
                        ├──► vocabulary card / dictionary cache
                        │
                        └──► TTS worker ──► audio player / playlist

persistent state ◄──── data_management
```

The current codebase is split into a small set of focused modules:

```text
.
├── main.py                     # application lifecycle and orchestration
├── functions/
│   ├── text_collection.py      # selection / clipboard capture
│   ├── translate_generation.py # translation and definitions
│   ├── audio_generation.py     # TTS worker and playback
│   └── data_management.py      # local persistence
└── ui/
    └── custom_widgets.py       # PySide6 interface components
```

## Project status

This repository is a **prototype / learning project**, not a packaged end-user release. The most interesting part of the project is the interaction model: turning small reading actions into a continuous desktop workflow rather than forcing the reader to jump between separate translation, dictionary, and TTS tools.

## Tech

`Python` · `PySide6 / Qt` · threaded background work · local persistence · text-to-speech
