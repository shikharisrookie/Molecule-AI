"""Chemistry knowledge base — rule-based Q&A for molecular analysis.

Provides instant, offline answers for common chemistry questions
using pre-built knowledge. Falls back to LLM for open-ended questions.
"""
import re
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# ── Knowledge Base ────────────────────────────────────────────────

CHEMISTRY_KB: Dict[str, str] = {
    # Molecular properties
    "logp": (
        "LogP (octanol-water partition coefficient) measures how easily a molecule "
        "dissolves in fat vs water. A LogP between 0 and 5 is ideal for oral drugs — "
        "it means the molecule can cross cell membranes (lipophilic enough) but is still "
        "soluble in blood (not too greasy). Values above 5 often indicate poor absorption "
        "and increased toxicity risk."
    ),
    "molecular weight": (
        "Molecular weight (MW) is the mass of the molecule in g/mol. Lipinski's Rule of Five "
        "states that drugs generally have MW < 500 g/mol. Larger molecules often have trouble "
        "being absorbed in the gut, crossing cell membranes, and being cleared by the kidneys. "
        "However, some successful drugs (like antibiotics and immunosuppressants) exceed this limit."
    ),
    "tpsa": (
        "TPSA (Topological Polar Surface Area) is the surface area of the molecule covered by "
        "polar atoms (nitrogen, oxygen, and their hydrogens). A TPSA < 140 Å² suggests good "
        "intestinal absorption, and TPSA < 90 Å² suggests good blood-brain barrier penetration. "
        "Higher TPSA means the molecule is more polar and less likely to cross lipid membranes."
    ),
    "hbd": (
        "HBD (Hydrogen Bond Donors) are groups like -OH and -NH that can donate a hydrogen bond. "
        "Lipinski's rule says oral drugs should have ≤5 HBDs. More donors mean the molecule forms "
        "stronger interactions with water, making it harder to cross cell membranes."
    ),
    "hba": (
        "HBA (Hydrogen Bond Acceptors) are atoms with lone pairs (mainly O and N) that accept "
        "hydrogen bonds. Lipinski's rule recommends ≤10 HBAs for oral drugs. Too many acceptors "
        "can trap the molecule in aqueous environments, preventing membrane crossing."
    ),
    "qed": (
        "QED (Quantitative Estimate of Drug-likeness) is a score from 0 to 1 that measures how "
        "'drug-like' a molecule looks based on multiple properties (MW, LogP, HBD, HBA, PSA, "
        "rotatable bonds, aromatic rings, and structural alerts). Most approved drugs score > 0.3, "
        "and a score > 0.6 is considered highly drug-like. It was published by Bickerton et al. "
        "in Nature Chemistry (2012)."
    ),
    "lipinski": (
        "Lipinski's Rule of Five (Ro5) predicts if a molecule can be an effective oral drug. "
        "The rules state: MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10. If a molecule violates 2+ rules, "
        "it likely won't be absorbed well orally. About 90% of approved oral drugs follow these rules. "
        "Named after Christopher Lipinski at Pfizer (1997), all values are multiples of 5."
    ),
    "rotatable bonds": (
        "Rotatable bonds are single bonds that allow parts of the molecule to rotate freely. "
        "Fewer rotatable bonds (≤10) generally means better oral bioavailability because the "
        "molecule is more rigid and loses less entropy upon binding to its target. Very flexible "
        "molecules also tend to have poor membrane permeability."
    ),
    "aromatic rings": (
        "Aromatic rings are flat, cyclic structures with delocalized electrons (like benzene). "
        "Most drugs have 1-3 aromatic rings. They contribute to drug-target binding through "
        "π-stacking and hydrophobic interactions. However, too many aromatic rings (>4) can "
        "lead to poor solubility, metabolic issues, and increased toxicity."
    ),
    # Drug discovery concepts
    "smiles": (
        "SMILES (Simplified Molecular-Input Line-Entry System) is a way to describe chemical "
        "structures as text strings. For example: water = O, ethanol = CCO, benzene = c1ccccc1, "
        "aspirin = CC(=O)OC1=CC=CC=C1C(=O)O. Uppercase letters are aliphatic atoms, lowercase "
        "are aromatic. Branches use parentheses, rings use numbers. SMILES was invented by "
        "David Weininger in the late 1980s."
    ),
    "drug discovery": (
        "Drug discovery is the process of finding new medications. The typical pipeline: "
        "1) Target identification — find a protein involved in disease. "
        "2) Hit finding — screen thousands of compounds for activity. "
        "3) Lead optimization — improve the best hits. "
        "4) Preclinical testing — test in cells and animals. "
        "5) Clinical trials (Phase I-III) — test in humans. "
        "6) FDA approval. "
        "This process takes 10-15 years and costs $2-3 billion on average. "
        "AI can dramatically accelerate steps 2-3."
    ),
    "morgan fingerprint": (
        "Morgan fingerprints (also called ECFP — Extended Connectivity Fingerprints) encode "
        "molecular structure as a fixed-length binary vector. Each bit represents the presence "
        "of a particular circular substructure. We use 2048-bit Morgan fingerprints with radius 2, "
        "meaning we encode all atoms and their neighborhoods up to 2 bonds away. These fingerprints "
        "are the most widely used molecular representation in machine learning for drug discovery."
    ),
    "toxicity": (
        "Molecular toxicity prediction estimates whether a compound may cause harmful effects. "
        "Our platform uses the Tox21 dataset, which tests compounds against 12 biological targets "
        "related to nuclear receptor signaling and stress response pathways. Key endpoints include "
        "androgen receptor (hormone disruption), aryl hydrocarbon receptor (carcinogenicity), "
        "p53 (DNA damage), and mitochondrial membrane potential (cell death). High scores on any "
        "endpoint suggest the compound needs further safety evaluation."
    ),
    "blood brain barrier": (
        "The blood-brain barrier (BBB) is a selective membrane that separates blood from the brain. "
        "It blocks most drugs from entering the brain. For CNS drugs (antidepressants, anticonvulsants, "
        "Alzheimer's drugs), BBB penetration is essential. For other drugs, BBB penetration may cause "
        "unwanted neurological side effects. Our BBBP model predicts the probability that a molecule "
        "can cross the BBB based on its structural features."
    ),
    "solubility": (
        "Aqueous solubility (logS) measures how much of a compound dissolves in water. It's critical "
        "for drug absorption — if a drug can't dissolve, it can't be absorbed. Categories: "
        "Insoluble (logS < -6), Poorly Soluble (-6 to -4), Moderately Soluble (-4 to -2), "
        "Soluble (-2 to 0), Very Soluble (> 0). About 40% of drug candidates fail due to poor "
        "solubility. Our ESOL model predicts logS from molecular features."
    ),
    "bace": (
        "BACE-1 (β-secretase 1) is an enzyme that cleaves amyloid precursor protein, producing "
        "amyloid-β peptides that form plaques in Alzheimer's disease brains. BACE inhibitors are "
        "a major drug development target for Alzheimer's treatment. Our BACE model predicts the "
        "probability that a molecule can inhibit BACE-1 enzyme activity."
    ),
    "xgboost": (
        "XGBoost (eXtreme Gradient Boosting) is a machine learning algorithm that builds an "
        "ensemble of decision trees sequentially, where each new tree corrects errors from the "
        "previous ones. It's one of the most effective algorithms for tabular/molecular data, "
        "achieving near state-of-the-art performance on drug discovery benchmarks while being "
        "much faster than deep learning approaches. It doesn't require GPU for training or inference."
    ),
    "tanimoto": (
        "Tanimoto similarity (also called Jaccard similarity for binary data) measures how similar "
        "two molecular fingerprints are. It's calculated as: T = c / (a + b - c), where a and b are "
        "the number of bits set in each fingerprint, and c is the number of shared set bits. "
        "A Tanimoto similarity of 1.0 means identical structures, >0.85 means very similar compounds "
        "likely with similar biological activity, and <0.3 means structurally distinct."
    ),
}


# ── Pattern Matching ──────────────────────────────────────────────

def _find_kb_match(query: str) -> Optional[str]:
    """Find the best matching knowledge base entry for a query."""
    query_lower = query.lower().strip()

    # Direct keyword matching
    best_match = None
    best_score = 0

    for key, answer in CHEMISTRY_KB.items():
        key_words = key.lower().split()
        score = sum(1 for w in key_words if w in query_lower)
        if score > best_score:
            best_score = score
            best_match = answer

    if best_score > 0:
        return best_match

    # Fuzzy pattern matching for common question forms
    patterns = {
        r"what is (a |the )?(logp|log p|log-p|partition coefficient)": "logp",
        r"what is (a |the )?(molecular weight|mol\.? weight|mw)": "molecular weight",
        r"what is (a |the )?(tpsa|polar surface area)": "tpsa",
        r"what is (a |the )?(qed|drug.?likeness)": "qed",
        r"what (is|are) (a |the )?(lipinski|rule of five|ro5)": "lipinski",
        r"what (is|are) (a |the )?(smiles|molecular notation)": "smiles",
        r"what is (a |the )?(morgan|fingerprint|ecfp)": "morgan fingerprint",
        r"(toxicity|toxic|tox21|safety)": "toxicity",
        r"(blood.?brain|bbb)": "blood brain barrier",
        r"(solubility|soluble|logs|dissolve)": "solubility",
        r"(bace|alzheimer|amyloid|secretase)": "bace",
        r"(xgboost|gradient boost|machine learning model)": "xgboost",
        r"(tanimoto|similarity|similar)": "tanimoto",
        r"(drug discovery|drug development|how.*drug.*made)": "drug discovery",
        r"(hbd|hydrogen bond donor)": "hbd",
        r"(hba|hydrogen bond acceptor)": "hba",
        r"(rotatable|flexible bond)": "rotatable bonds",
        r"(aromatic|ring|benzene)": "aromatic rings",
    }

    for pattern, kb_key in patterns.items():
        if re.search(pattern, query_lower):
            return CHEMISTRY_KB.get(kb_key)

    return None


def answer_chemistry_question(
    query: str,
    molecule_context: Optional[dict] = None,
) -> tuple:
    """Answer a chemistry question using the knowledge base.

    Returns:
        (answer, sources) where sources indicates what was used
    """
    # First try rule-based KB
    kb_answer = _find_kb_match(query)

    if kb_answer:
        # Enrich with molecule context if available
        if molecule_context:
            context_note = _build_context_note(query, molecule_context)
            if context_note:
                kb_answer = f"{kb_answer}\n\n**For your molecule:** {context_note}"

        return kb_answer, ["MoleculeAI Knowledge Base"]

    return None, []


def _build_context_note(query: str, ctx: dict) -> Optional[str]:
    """Build a molecule-specific note based on the query and context."""
    query_lower = query.lower()

    if "logp" in query_lower and "logp" in ctx:
        v = ctx["logp"]
        if v > 5:
            return f"Your molecule's LogP is {v}, which exceeds the ideal range (0-5). This may limit oral absorption."
        elif v < 0:
            return f"Your molecule's LogP is {v}, meaning it's highly hydrophilic — good solubility but may not cross cell membranes well."
        else:
            return f"Your molecule's LogP is {v}, which is within the ideal range for oral drug absorption."

    if "weight" in query_lower and "molecular_weight" in ctx:
        v = ctx["molecular_weight"]
        if v > 500:
            return f"At {v:.1f} g/mol, your molecule exceeds the 500 g/mol Lipinski threshold."
        else:
            return f"At {v:.1f} g/mol, your molecule is within the ideal weight range for oral drugs."

    if "qed" in query_lower and "qed_score" in ctx:
        v = ctx["qed_score"]
        return f"Your molecule's QED score is {v:.3f} (scale 0-1). {'This indicates good drug-likeness.' if v >= 0.5 else 'This is below average drug-likeness.'}"

    return None
