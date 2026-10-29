"""Load the influenza A datasets and build one lookup table.

Every human protein is stored under its gene symbol. UniProt IDs and protein
names are kept as aliases, so a user can type any of the three.
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent

# RNP name -> (file, gene-symbol column, UniProt column, protein-name column)
RNP_FILES = {
    "PB1": ("PB1_Human_Interactions_Unique_List.xlsx", "Human gene", "Human UniProt ID", "Human protein"),
    "PB2": ("PB2_Human_Interactions_Unique_List.xlsx", "Human Protein", "Human UniProt ID", "Protein Name"),
    "NP": ("NP_Human_Interactions_Unique_List.xlsx", "Human Protein", "Human UniProt ID", "Protein Name"),
    "PA": ("PA_human_interactions_unique_list_15-58.xlsx", "Human gene", "Human UniProt ID", "Human protein"),
}
INTERACTOME_FILE = "DDX3X_Human_Interactome_Integrated.xlsx"
INTERACTOME_NAME = "DDX3X"
RNP_ORDER = ["PB1", "PB2", "PA", "NP"]


def _clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_tables():
    """Return {RNP: DataFrame(gene, uniprot, name)} and the interactome DataFrame(gene, source)."""
    rnp = {}
    for name, (fname, gene_col, uni_col, prot_col) in RNP_FILES.items():
        df = pd.read_excel(DATA_DIR / fname, sheet_name=0)
        out = pd.DataFrame({
            "gene": df[gene_col].map(_clean),
            "uniprot": df[uni_col].map(_clean),
            "name": df[prot_col].map(_clean),
        })
        rnp[name] = out[out["gene"] != ""]

    ddx = pd.read_excel(DATA_DIR / INTERACTOME_FILE, sheet_name="Integrated")
    ddx = pd.DataFrame({
        "gene": ddx.iloc[:, 0].map(_clean),
        "source": ddx.iloc[:, 1].map(_clean),
    })
    return rnp, ddx[ddx["gene"] != ""]


def build_index():
    """Return (records, aliases).

    records: gene symbol (upper) -> {gene, name, uniprot, rnps, interactome}
    aliases: any upper-cased gene / UniProt ID / protein name -> gene symbol (upper)
    """
    rnp_tables, ddx = load_tables()
    records, aliases = {}, {}

    def record(gene):
        key = gene.upper()
        if key not in records:
            records[key] = {"gene": gene, "name": "", "uniprot": set(), "rnps": set(), "interactome": False}
            aliases[key] = key
        return records[key]

    for rnp_name, df in rnp_tables.items():
        for row in df.itertuples(index=False):
            rec = record(row.gene)
            rec["rnps"].add(rnp_name)
            if row.name and not rec["name"]:
                rec["name"] = row.name
            # In the NP file the "UniProt" column sometimes just repeats the gene symbol.
            if row.uniprot and row.uniprot.upper() != row.gene.upper():
                rec["uniprot"].add(row.uniprot)
                aliases[row.uniprot.upper()] = row.gene.upper()
            if row.name:
                aliases.setdefault(row.name.upper(), row.gene.upper())

    for row in ddx.itertuples(index=False):
        record(row.gene)["interactome"] = True

    return records, aliases


RECORDS, ALIASES = build_index()


def lookup(query):
    """Classify one protein. Returns a dict the API/front end can show directly."""
    q = query.strip()
    result = {"query": q, "found": False, "rnps": [], "interactome": [], "message": ""}
    if not q:
        result["message"] = "Please enter a protein name."
        return result

    if q.upper() in RNP_ORDER:
        result["message"] = f"{q.upper()} is an influenza RNP protein. Please enter a human protein (e.g. KPNA2, DDX3X)."
        return result

    gene_key = ALIASES.get(q.upper())
    if gene_key is None:
        result["message"] = "No, it is not interacting with any of PB1, PB2, PA, NP or the human interactome."
        return result

    rec = RECORDS[gene_key]
    rnps = [r for r in RNP_ORDER if r in rec["rnps"]]
    result.update({
        "found": True,
        "gene": rec["gene"],
        "protein_name": rec["name"],
        "uniprot": sorted(rec["uniprot"]),
        "rnps": rnps,
        "interactome": [INTERACTOME_NAME] if rec["interactome"] else [],
    })
    result["message"] = format_output(rnps, result["interactome"])
    return result


def format_output(rnps, interactome):
    """One RNP -> 'NP'. Several -> '(PB1, PB2)'. Human interactome is always in brackets."""
    if not rnps and not interactome:
        return "No, it is not interacting with any of PB1, PB2, PA, NP or the human interactome."
    parts = []
    if len(rnps) == 1:
        parts.append(f"RNP: {rnps[0]}")
    elif len(rnps) > 1:
        parts.append(f"RNP: ({', '.join(rnps)})")
    if interactome:
        parts.append(f"Human interactome: ({', '.join(interactome)})")
    return " | ".join(parts)


def suggest(prefix, limit=10):
    p = prefix.strip().upper()
    if not p:
        return []
    genes = sorted(r["gene"] for k, r in RECORDS.items() if k.startswith(p))
    return genes[:limit]
