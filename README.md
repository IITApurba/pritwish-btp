# Influenza A – Protein Interaction Checker

A small web app for a college assignment. Enter a **human protein** and it tells you whether it interacts with the
influenza A RNP proteins (**PB1, PB2, PA, NP**) and/or the **human interactome** (DDX3X dataset).

## Output examples
| Input | Output |
|---|---|
| `FBL` | `RNP: NP` |
| `KPNA2` | `RNP: (PB1, PB2, PA, NP)` |
| `NCL` | `RNP: PB2 \| Human interactome: (DDX3X)` |
| `XYZ123` | `No, it is not interacting with any of PB1, PB2, PA, NP or the human interactome.` |

You can type a gene symbol (`KPNA2`), a UniProt ID (`O43707`) or the full protein name; matching is case-insensitive.

## Quick start (Python 3 required)
Download or clone the project, then use the scripts for your system. Run setup once, then run whenever you want to start the app.

| | Setup (once) | Run |
|---|---|---|
| **Windows** | double-click `windows\setup.bat` | double-click `windows\run.bat` |
| **macOS** | double-click `macos/setup.command` | double-click `macos/run.command` |

The run script starts the app and opens http://127.0.0.1:5001 in your browser. Press `Ctrl+C` in the window to stop it.
On macOS, if double-clicking is blocked, right-click the file → Open, or run `bash macos/setup.command` in Terminal.

## Manual setup
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python analysis.py                 # creates the plots + results (optional, needed for the Data analysis page)
python app.py                      # open http://127.0.0.1:5001
```
Keep the five `.xlsx` files in the project folder.

## Project structure
```
app.py            Flask routes
data_loader.py    reads the Excel files, builds the lookup, formats the answer
analysis.py       data analysis + small ML experiment
windows/          setup.bat, run.bat
macos/            setup.command, run.command
templates/        HTML pages (search, analysis)
static/           CSS, JS, generated plots
results/          analysis_summary.json, protein_membership_table.csv
plan.md           project plan and findings
CLAUDE.md         notes for Claude Code
```

## How it works
1. `data_loader.py` reads the first sheet of each RNP workbook plus the `Integrated` sheet of the DDX3X workbook.
2. Every protein is stored under its gene symbol; UniProt IDs and protein names are aliases for that symbol.
3. `lookup()` finds the protein, collects the RNPs it appears in and whether it is in the DDX3X list, and formats the answer.

## Data analysis and machine learning (backend)
`python analysis.py` produces:
- interactors per dataset (bar chart),
- overlap between datasets (heatmap) and Jaccard similarity (dendrogram),
- proteins that bind 3 or more RNPs,
- a small ML experiment: *can the RNP membership of a protein predict whether it is a DDX3X interactor?*
  (logistic regression and decision tree, 5-fold cross-validation).

**Result:** ROC-AUC ≈ 0.54, i.e. about chance. The only features are four yes/no flags, so this is expected. Report it as an honest negative result.

### Ideas to improve the ML (suggestions)
- Add richer features: protein sequence length, amino-acid composition, GO terms, subcellular location (from UniProt).
- Predict "which RNP will this protein bind?" as a multi-label classification on those features.
- Link prediction on the interaction network (e.g. common-neighbour or node2vec) to suggest *new* candidate interactors.
- GO/pathway enrichment per RNP (what biological processes do PB2 partners share?).

## Limitations
- The answer is only as complete as the provided datasets; "not interacting" means "not found in these files".
- Exact match only (no spelling correction). Aliases/old gene names (e.g. `SEC15L3`) work only if they appear in the data.
- `DDX3X` itself appears in the DDX3X interactome list (as in the source file), so it is reported as part of it.
- The DDX3X workbook has no UniProt IDs, so searching by UniProt ID only works for proteins that also appear in an RNP file.
