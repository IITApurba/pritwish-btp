# Solution — How the Interaction Checker Works

## 1. The problem
Given a **human protein**, answer:
- Does it interact with any influenza A RNP protein (**PB1, PB2, PA, NP**)? If yes, which ones?
- Is it part of the **human interactome** dataset (**DDX3X** partners)?
- If neither: say clearly that it is not interacting.

## 2. The approach we use: exact lookup in curated datasets
The app does **not predict** interactions. It **looks them up** in five experimentally derived datasets that were
provided for the project. Every answer is a direct fact from one of these files:

| Dataset | File | Unique human proteins |
|---|---|---|
| PB1 interactors | `PB1_Human_Interactions_Unique_List.xlsx` | 20 |
| PB2 interactors | `PB2_Human_Interactions_Unique_List.xlsx` | 261 |
| PA interactors | `PA_human_interactions_unique_list_15-58.xlsx` | 30 |
| NP interactors | `NP_Human_Interactions_Unique_List.xlsx` | 144 |
| DDX3X human interactome | `DDX3X_Human_Interactome_Integrated.xlsx` (BioGRID + IntAct + UniProt) | 745 |

In total: **1,095 unique human proteins**.

This is a **rule-based, deterministic** method (set membership). Because nothing is estimated, the answer is
**100% correct with respect to the data**: a protein listed in a file is always reported, and one not listed is never
reported as interacting.

### Why lookup and not machine learning?
The question "is protein X in these lists?" has an exact answer, so a lookup is the right tool. A model would only add
errors. ML is used separately, as an analysis experiment (see section 5), and never changes what the app answers.

## 3. How it works, step by step

### Step 1 — Load and unify the data (`data_loader.py`)
- Read the first sheet of each RNP workbook (the unique-partner list) and the `Integrated` sheet of the DDX3X workbook.
- The column names differ between files, so a small mapping (`RNP_FILES`) says which column holds the gene symbol, the
  UniProt ID and the protein name in each file.
- Clean every value (strip blanks, drop empty rows).

### Step 2 — Build one index
- Every protein is stored once, under its **gene symbol**, in `RECORDS`:
  `gene → {protein name, UniProt IDs, set of RNPs, in DDX3X interactome yes/no}`.
- **Aliases** (`ALIASES`) map other identifiers to the gene symbol, so the user can type any of:
  - gene symbol: `KPNA2`
  - UniProt ID: `P52292`
  - full protein name: `Importin subunit alpha-1`
- Data fix: in the NP file the "Human UniProt ID" column sometimes repeats the gene symbol. These values are not
  treated as UniProt IDs.

### Step 3 — Look up the user's input (`lookup()`)
1. Trim the input and convert it to upper case (matching is case-insensitive).
2. If the input is itself PB1/PB2/PA/NP, ask for a *human* protein instead.
3. Resolve the input through `ALIASES` to a gene symbol. The match is **exact**: no fuzzy or spelling correction, so a
   typo can never return a wrong protein.
4. Read that protein's record: which RNPs it binds, and whether it is a DDX3X interactor.

### Step 4 — Format the answer (`format_output()`)
| Case | Output |
|---|---|
| One RNP | `RNP: NP` |
| Several RNPs | `RNP: (PB1, PB2, PA, NP)` |
| Human interactome | `Human interactome: (DDX3X)` |
| Both | `RNP: PB2 \| Human interactome: (DDX3X)` |
| Not found | `No, it is not interacting with any of PB1, PB2, PA, NP or the human interactome.` |

### Step 5 — Web interface (`app.py`, `templates/`, `static/`)
- `/` — search page with a text box.
- `/api/lookup?protein=…` — returns the answer as JSON (gene, protein name, UniProt IDs, RNPs, interactome, message).
- `/api/suggest?q=…` — prefix autocomplete over gene symbols, to help the user type a valid name.
- `/analysis` — shows the data-analysis plots and results.
- Each entity has a fixed colour everywhere: PB1 blue, PB2 orange, PA aqua, NP violet, DDX3X grey.

```
 user input ─► normalise ─► ALIASES ─► gene symbol ─► RECORDS ─► format_output ─► answer
 (gene / UniProt / name)    (exact)                   (RNPs + DDX3X flag)
```

## 4. Example
Input `KPNA2` → alias resolves to gene `KPNA2` → record says it is in the PB1, PB2, PA and NP lists, not in DDX3X →
output `RNP: (PB1, PB2, PA, NP)`.

## 5. Data analysis and ML (supporting work, not part of the answer)
`analysis.py` studies the datasets themselves and writes plots to `static/plots/` and numbers to `results/`:
- interactors per dataset (bar chart);
- overlap between datasets (heatmap) and Jaccard similarity (dendrogram);
- proteins that bind 3 or more RNPs.

Key findings:
- Every PB1 interactor (20/20) is also a PA interactor (PB1–PA Jaccard = 0.67); other overlaps are small.
- The importin-α family (KPNA1/2/3/6) and POLR2A bind all four RNPs.
- 47 of the 397 RNP-binding proteins are also DDX3X interactors.

**ML experiment:** can a protein's RNP membership (4 yes/no features) predict whether it is a DDX3X interactor?
Logistic regression and a decision tree with 5-fold cross-validation give **ROC-AUC ≈ 0.54**, which is about chance.
This is reported as an honest negative result: four binary features carry too little information. The model is kept
for analysis only and is **not** used to answer user queries, because a prediction could be wrong and the lookup cannot.

## 6. Limitations
- "Not interacting" means "**not found in these datasets**". It does not prove the proteins never interact, because
  the datasets only contain what has been tested and reported.
- Exact matching only. Old or alternative gene names work only if they appear in the files.
- The DDX3X file has no UniProt IDs, so a UniProt search only finds proteins that are also in an RNP file.
- `DDX3X` itself appears in the DDX3X interactome list (as in the source file), so it is reported as part of it.

## 7. Possible extension (keeps the answers exact)
To cover more proteins without guessing, add more **experimentally verified** sources as extra datasets, for example
BioGRID, IntAct, VirHostNet or HPIDB records for influenza A PB1/PB2/PA/NP. They plug into the same loader
(`RNP_FILES`), and each answer could also show its source. This widens coverage while keeping every answer traceable
to a published experiment.

## 8. Lookup vs ML: when would ML make sense?

### Lookup does not get harder as the data grows
The index is a dictionary (hash table), so finding a protein takes about the same time whether there are 1,000
records or 1 billion. Large biological databases (UniProt, BioGRID, STRING) hold gigabytes to terabytes and still
answer "is X recorded?" by indexed lookup, not by ML. A big dataset is a storage and engineering issue, not a reason
to switch to ML.

### What decides the method is the question being asked
| Question | Right tool | Accuracy |
|---|---|---|
| "Is this interaction **already recorded** in our data?" | Lookup | Exact, at any data size |
| "Will this protein interact with PB2, even though **nobody has tested it**?" | ML (prediction) | Never 100% |

A lookup can only repeat what is in the data. ML is useful for answers **beyond** the data: protein pairs that have
never been tested. Large data matters there too, but differently: more training data and richer features (sequence,
structure, GO terms) make a model **more accurate**, never perfect.

### What "100% accurate" means here
The lookup is 100% **faithful to the datasets**, not 100% correct about biology. If a real interaction is missing
from the files, the app answers "not interacting". The accurate phrase is "100% faithful to the data".

### Summary
We use an exact lookup because the question is whether an interaction is recorded in our datasets. A lookup answers
that exactly, and indexing keeps it fast even for very large datasets. ML would suit a different question:
predicting interactions that have not been tested experimentally. It can never be 100% accurate, and it needs far
more training data and richer features than we have. Our ML experiment (ROC-AUC ≈ 0.54, section 5) confirms that
the current features are not enough for that.
