# CLAUDE.md

College project: a small web interface to check whether a human protein interacts with influenza A
RNP proteins (PB1, PB2, PA, NP) or the human interactome (DDX3X). Keep it simple — base-level solution, no heavy tooling.

## Commands
- Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Run app: `.venv/bin/python app.py` → http://127.0.0.1:5001 (port 5000 is taken by macOS AirPlay Receiver)
- Run analysis/ML (regenerates `static/plots/` and `results/`): `.venv/bin/python analysis.py`

## Layout
- `data_loader.py` — reads the 5 `.xlsx` files in the project root, builds `RECORDS` (gene → RNPs/interactome flag) and `ALIASES` (UniProt ID / protein name → gene); `lookup()` and `format_output()` produce the answer.
- `app.py` — Flask routes: `/`, `/api/lookup`, `/api/suggest`, `/analysis`.
- `analysis.py` — counts, overlap heatmap, Jaccard dendrogram, small logistic-regression/decision-tree experiment.
- `templates/`, `static/` — front end (plain HTML/CSS/JS, no build step).
- `plan.md` — project plan; `README.md` — user-facing docs.

## Data notes
- Only the first sheet of each RNP workbook is used (unique partner lists). DDX3X file uses sheet `Integrated`.
- Column names differ per file; the mapping lives in `RNP_FILES` in `data_loader.py`. Add new datasets there.
- In the NP file the "Human UniProt ID" column sometimes repeats the gene symbol — handled in the loader.
- Output format: one RNP → `NP`; several → `(PB1, PB2)`; interactome → `(DDX3X)`; none → "No, it is not interacting…".
- Gene symbols are matched case-insensitively. Input matching is exact (no fuzzy match); `/api/suggest` gives prefix autocomplete.

## Conventions
- Fixed colour per entity everywhere (PB1 blue, PB2 orange, PA aqua, NP violet, DDX3X grey).
- Don't edit the source `.xlsx` files.
