# Presidential AI Challenge

A lightweight Streamlit app and supporting modules for the Presidential AI Challenge project.

## Overview

This repository contains a Streamlit-based demo application and helper modules for building, testing, and experimenting with AI-driven prompts and retrieval-augmented generation (RAG). It also includes an emotion classifier and safety utilities.

## Features

- Simple Streamlit UI in `app.py` for interactive demos
- Emotion classification helper in `emotion_classifier.py`
- Prompt generation utilities in `prompt.py`
- Retrieval-augmented generation helper in `rag.py`
- Safety checks in `safety.py`
- Basic test script `test_streamlit.py`

## Files

- `app.py`: Streamlit application entrypoint
- `emotion_classifier.py`: Emotion classifier helper
- `prompt.py`: Prompt templates and helpers
- `rag.py`: Retrieval-augmented generation utilities
- `safety.py`: Safety filter utilities
- `test_streamlit.py`: Quick test for the Streamlit app
- `requirements.txt`: Python dependencies
- `data/skillcards.json`: Example data used by the app

## Prerequisites

- Python 3.10+ recommended
- macOS or Linux (instructions use `zsh` on macOS)

## Setup

1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the app

Start the Streamlit app locally:

```bash
streamlit run app.py
```

Open the URL printed by Streamlit in your browser.

## Tests

Run the basic test script:

```bash
python3 test_streamlit.py
```

If you use `pytest`, you can also run:

```bash
pytest -q
```

## Development Notes

- Keep `requirements.txt` up to date when adding packages
- Use `data/skillcards.json` for example content and update as needed

## Contributing

Contributions are welcome. Open an issue or submit a pull request with a clear description of your change.

## License

Add your preferred license here (e.g., MIT, Apache-2.0) or remove this section if not applicable.

## Contact

Project maintainer: `varshakethireddy` (update contact details as needed)
