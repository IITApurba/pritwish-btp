"""Base-level data analysis + a small ML model on the influenza A interaction data.

Run:  python analysis.py
Writes charts to static/plots/ and numbers to results/analysis_summary.json
"""
import json
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.tree import DecisionTreeClassifier

from data_loader import INTERACTOME_NAME, RECORDS, RNP_ORDER

ROOT = Path(__file__).parent
PLOT_DIR = ROOT / "static" / "plots"
RESULT_DIR = ROOT / "results"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

# Fixed colour per entity (blue, orange, aqua, violet from the reference palette; grey for the interactome).
COLORS = {"PB1": "#2a78d6", "PB2": "#eb6834", "PA": "#1baf7a", "NP": "#6250d6", INTERACTOME_NAME: "#52514e"}
INK, MUTED = "#0b0b0b", "#52514e"
SETS = RNP_ORDER + [INTERACTOME_NAME]

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
})


def feature_table():
    """Protein x set membership (0/1)."""
    rows = []
    for rec in RECORDS.values():
        row = {"gene": rec["gene"]}
        for r in RNP_ORDER:
            row[r] = int(r in rec["rnps"])
        row[INTERACTOME_NAME] = int(rec["interactome"])
        rows.append(row)
    return pd.DataFrame(rows).set_index("gene")


def plot_counts(df):
    counts = df[SETS].sum()
    fig, ax = plt.subplots(figsize=(5.4, 4.6))  # same size as the overlap heatmap so the cards line up
    bars = ax.bar(counts.index, counts.values, color=[COLORS[s] for s in counts.index], width=0.6)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v + counts.max() * 0.015, int(v), ha="center", fontsize=10)
    ax.set_ylabel("Human interacting proteins")
    ax.set_title("Interactors per dataset", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "counts.png", dpi=150)
    plt.close(fig)
    return counts.astype(int).to_dict()


def plot_overlap(df):
    n = len(SETS)
    inter = np.zeros((n, n), dtype=int)
    for i, a in enumerate(SETS):
        for j, b in enumerate(SETS):
            inter[i, j] = int((df[a] & df[b]).sum())
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0e2f5a"])
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    # Diagonal (a dataset's own size) would swamp the colour scale, so it is left grey.
    off_diag = np.ma.masked_where(np.eye(n, dtype=bool), inter)
    cmap.set_bad("#e8e7e3")
    ax.imshow(off_diag, cmap=cmap)
    ax.set_xticks(range(n), SETS)
    ax.set_yticks(range(n), SETS)
    top = off_diag.max()
    for i in range(n):
        for j in range(n):
            dark = i != j and inter[i, j] > top * 0.6
            ax.text(j, i, inter[i, j], ha="center", va="center", color="white" if dark else INK, fontsize=10)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Shared interactors (grey diagonal = dataset size)", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "overlap.png", dpi=150)
    plt.close(fig)
    return pd.DataFrame(inter, index=SETS, columns=SETS)


def plot_similarity(df):
    """Jaccard similarity between datasets + a small dendrogram."""
    jac = {}
    for a, b in combinations(SETS, 2):
        both, either = (df[a] & df[b]).sum(), (df[a] | df[b]).sum()
        jac[f"{a}-{b}"] = round(float(both / either), 3)
    dist = np.array([[1 - (df[a] & df[b]).sum() / (df[a] | df[b]).sum() for b in SETS] for a in SETS])
    # condensed distance vector for linkage
    cond = dist[np.triu_indices(len(SETS), k=1)]
    fig, ax = plt.subplots(figsize=(10.8, 3.8))  # shown full-width (two cards wide) on the analysis page
    dendrogram(linkage(cond, "average"), labels=SETS, ax=ax, color_threshold=0, above_threshold_color=MUTED)
    ax.set_ylabel("1 - Jaccard similarity")
    ax.set_title("Which datasets share the most interactors?", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "clusters.png", dpi=150)
    plt.close(fig)
    return jac


def top_shared(df, k=15):
    n_rnp = df[RNP_ORDER].sum(axis=1)
    top = df[n_rnp >= 3].copy()
    top["n_rnp"] = n_rnp[top.index]
    top = top.sort_values(["n_rnp", INTERACTOME_NAME], ascending=False)
    return top.head(k)


def ml_experiment(df):
    """Does knowing which RNPs a protein binds help predict whether it is a DDX3X interactor?

    Only proteins that bind at least one RNP are used, so the 'no' class is
    'binds an RNP but is not in the DDX3X list'. 5-fold cross-validated.
    """
    sub = df[df[RNP_ORDER].sum(axis=1) > 0]
    X, y = sub[RNP_ORDER].values, sub[INTERACTOME_NAME].values
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    out = {"n_proteins": int(len(sub)), "n_positive": int(y.sum()), "baseline_accuracy": round(1 - y.mean(), 3)}
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=42),
    }
    for name, model in models.items():
        prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
        out[name] = {"roc_auc": round(float(roc_auc_score(y, prob)), 3)}
    lr = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X, y)
    out["logistic_coefficients"] = {r: round(float(c), 3) for r, c in zip(RNP_ORDER, lr.coef_[0])}
    return out


def main():
    df = feature_table()
    summary = {
        "total_unique_human_proteins": int(len(df)),
        "interactors_per_dataset": plot_counts(df),
        "proteins_by_number_of_rnps": df[RNP_ORDER].sum(axis=1).value_counts().sort_index().astype(int).to_dict(),
        "jaccard_similarity": plot_similarity(df),
        "ml_experiment": ml_experiment(df),
    }
    overlap = plot_overlap(df)
    summary["overlap_matrix"] = overlap.to_dict()
    shared = top_shared(df)
    summary["proteins_binding_3_or_more_rnps"] = shared.reset_index().to_dict(orient="records")

    (RESULT_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
    df.to_csv(RESULT_DIR / "protein_membership_table.csv")
    print(json.dumps({k: v for k, v in summary.items() if k != "proteins_binding_3_or_more_rnps"}, indent=2))
    print("Plots ->", PLOT_DIR)


if __name__ == "__main__":
    main()
