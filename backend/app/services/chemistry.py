"""RDKit-based chemistry service for molecular processing."""
from rdkit import Chem
from rdkit.Chem import (
    Descriptors, rdMolDescriptors, AllChem, Draw,
    QED, Lipinski, rdDepictor
)
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.inchi import MolToInchi, InchiToInchiKey
from rdkit import RDLogger
import numpy as np
from typing import Optional, Dict, Tuple

# Suppress RDKit warnings in production
RDLogger.logger().setLevel(RDLogger.ERROR)


def parse_smiles(smiles: str) -> Optional[Chem.Mol]:
    """Parse and validate a SMILES string, returns RDKit Mol object or None."""
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is not None:
            Chem.SanitizeMol(mol)
        return mol
    except Exception:
        return None


def get_canonical_smiles(mol: Chem.Mol) -> str:
    """Get canonical SMILES from an RDKit Mol object."""
    return Chem.MolToSmiles(mol)


def get_molecular_formula(mol: Chem.Mol) -> str:
    """Get molecular formula."""
    return rdMolDescriptors.CalcMolFormula(mol)


def get_inchi(mol: Chem.Mol) -> Tuple[str, str]:
    """Get InChI and InChIKey."""
    inchi = MolToInchi(mol) or ""
    inchi_key = InchiToInchiKey(inchi) if inchi else ""
    return inchi, inchi_key


def get_molecular_properties(mol: Chem.Mol) -> Dict:
    """Calculate physicochemical properties of a molecule."""
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    aromatic = rdMolDescriptors.CalcNumAromaticRings(mol)

    # Lipinski violations
    violations = 0
    if mw > 500:
        violations += 1
    if logp > 5:
        violations += 1
    if hbd > 5:
        violations += 1
    if hba > 10:
        violations += 1

    # QED score
    qed_score = QED.qed(mol)

    return {
        "molecular_weight": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 2),
        "rotatable_bonds": rotatable,
        "aromatic_rings": aromatic,
        "lipinski_violations": violations,
        "qed_score": round(qed_score, 4),
    }


def get_morgan_fingerprint(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """Generate Morgan fingerprint (ECFP) as a numpy array."""
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros(n_bits, dtype=np.int8)
    Chem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def get_mol_block_3d(mol: Chem.Mol) -> str:
    """Generate 3D coordinates and return mol block for 3D visualization."""
    try:
        mol_3d = Chem.AddHs(mol)
        result = AllChem.EmbedMolecule(mol_3d, AllChem.ETKDG())
        if result == -1:
            # Fallback: try random coordinates
            AllChem.EmbedMolecule(mol_3d, randomSeed=42)
        AllChem.MMFFOptimizeMolecule(mol_3d, maxIters=200)
        return Chem.MolToMolBlock(mol_3d)
    except Exception:
        # Fallback: 2D coordinates
        try:
            rdDepictor.Compute2DCoords(mol)
            return Chem.MolToMolBlock(mol)
        except Exception:
            return ""


def generate_2d_svg(mol: Chem.Mol, width: int = 400, height: int = 300) -> str:
    """Generate a 2D SVG depiction of the molecule."""
    try:
        rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        drawer.drawOptions().addStereoAnnotation = True
        drawer.drawOptions().addAtomIndices = False
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception:
        return ""


def get_property_explanations() -> Dict[str, str]:
    """Return plain-language explanations for molecular properties."""
    return {
        "molecular_weight": "The mass of the molecule. Most successful drugs weigh less than 500 g/mol.",
        "logp": "How easily the molecule dissolves in fat vs water. A value between 0-5 is ideal for drugs that need to cross cell membranes.",
        "hbd": "Parts of the molecule that can donate hydrogen bonds. Fewer donors (≤5) usually means better absorption.",
        "hba": "Parts of the molecule that can accept hydrogen bonds. Fewer acceptors (≤10) is generally preferred.",
        "tpsa": "The surface area of the molecule that can form polar interactions. Lower values suggest better membrane penetration.",
        "rotatable_bonds": "Flexible connections in the molecule. Fewer rotatable bonds (≤10) often means better bioavailability.",
        "aromatic_rings": "Ring-shaped structures with special stability. Most drugs have 1-3 aromatic rings.",
        "lipinski_violations": "Number of Lipinski's Rule of Five violations. Zero violations suggest the molecule could work as an oral drug.",
        "qed_score": "An overall 'drug-likeness' score from 0 to 1. Higher is better — most approved drugs score above 0.3.",
    }
