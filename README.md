# Speak2Sign v2

A news bulletin plays on the left. On the right, an interpreter panel signs it in
American Sign Language from recorded clips of Deaf signers, in time with the narration.
Every sign carries a badge: validated, fingerspelled, name (already spelled once, shown as text), or not available.

**Repository:** https://github.com/sr-dotcom/speak2sign · **Live URL:** https://speak2sign.streamlit.app · **Cost:** $0/month.

University capstone; both the app and the documented process are assessed. It is a
research demonstration of retrieval-based signing and is not a substitute for a human
interpreter.

## Run locally

Windows (PowerShell):

```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m streamlit run app.py
.venv\Scripts\python -m pytest -q
```

macOS / Linux:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m streamlit run app.py
.venv/bin/python -m pytest -q
```

`app.py` puts `src/` on the path itself, so no `PYTHONPATH` is needed.

## Where things are

- `docs/00-execution-plan.md` — the plan, trade-offs, cost model
- `docs/01-requirements/prd.md` — requirements
- `docs/02-design/system-design.md` — design, with diagrams under `docs/02-design/diagrams/`
- `docs/adr/` — architecture decision records
- `contracts/timeline.schema.json` — the Python ↔ panel contract
- `NOTICE.md` — sources and licences of all media and data
