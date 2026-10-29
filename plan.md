# Project Plan — Influenza A Protein Interaction Checker

## Goal
A web interface where the user enters a human protein and gets back:
- which influenza A RNP protein(s) it interacts with (PB1, PB2, PA, NP),
- whether it is in the human interactome dataset (DDX3X),
- or "No, it is not interacting with any of them".

Output rules: one RNP → `NP`; several → `(PB1, PB2)`; interactome → `(DDX3X)`.

## Datasets (provided)
| File | Content | Unique human proteins |
|---|---|---|
| `PB1_Human_Interactions_Unique_List.xlsx` | PB1 – human interactors | 20 |
| `PB2_Human_Interactions_Unique_List.xlsx` | PB2 – human interactors | 261 |
| `PA_human_interactions_unique_list_15-58.xlsx` | PA – human interactors | 30 |
| `NP_Human_Interactions_Unique_List.xlsx` | NP – human interactors | 144 |
| `DDX3X_Human_Interactome_Integrated.xlsx` | DDX3X partners (BioGRID + IntAct + UniProt) | 745 |

## Steps
1. [x] Inspect the Excel files; note that column names differ per file.
2. [x] `data_loader.py`: read all files, unify on gene symbol, keep UniProt ID / protein name as aliases.
3. [x] Lookup + output formatting (single RNP / bracketed list / interactome / none).
4. [x] Flask backend (`app.py`) with `/api/lookup` and `/api/suggest`.
5. [x] Front end: search box with autocomplete, colour badges, result text.
6. [x] `analysis.py`: counts, overlap heatmap, Jaccard similarity + dendrogram, proteins binding ≥3 RNPs.
7. [x] Small ML experiment (logistic regression + decision tree, 5-fold CV).
8. [x] `/analysis` page showing the plots and results.
9. [ ] (Student) Write the report: methods, screenshots, discussion of the results.
10. [ ] (Optional) Extensions below.

## Findings so far
- Overlap is small: every PB1 interactor (20/20) is also a PA interactor, and the importin-α family (KPNA1/2/3/6) plus POLR2A bind all four RNPs.
- 47 of 397 RNP-binding proteins are also DDX3X interactors.
- ML: RNP membership alone predicts DDX3X membership at ROC-AUC ≈ 0.54 (≈ chance). This is a valid negative result — the features are too few.

## Optional extensions (if time allows)
- Add UniProt sequence-based features (length, amino-acid composition) and retry the classifier.
- GO / pathway enrichment of each RNP's partners (g:Profiler or `gseapy`) — "what do PB2 partners do?"
- Network view of RNP–human proteins with `networkx` / `pyvis`.
- Show evidence (detection method, publication) per interaction from the other sheets of each workbook.
- Fuzzy search for typos.

## Run
See `README.md`.
