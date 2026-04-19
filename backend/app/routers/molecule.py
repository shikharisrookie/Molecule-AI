"""Molecule info router — /molecule-info endpoint."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import MoleculeInput, MoleculeInfoResponse, MolecularProperties
from app.services.chemistry import (
    parse_smiles, get_canonical_smiles, get_molecular_properties,
    get_mol_block_3d, generate_2d_svg, get_molecular_formula,
    get_inchi, get_property_explanations
)

router = APIRouter(prefix="/molecule-info", tags=["Molecule Information"])


@router.post("", response_model=MoleculeInfoResponse, summary="Get detailed molecule information")
async def get_molecule_info(input_data: MoleculeInput):
    """
    Get comprehensive information about a molecule including:
    - Physicochemical properties
    - 3D molecular structure (SDF format for 3Dmol.js)
    - 2D SVG depiction
    - Molecular formula, InChI, InChIKey
    - Plain-language property explanations
    """
    mol = parse_smiles(input_data.smiles)
    if mol is None:
        return MoleculeInfoResponse(
            success=False,
            error=f"Invalid SMILES string: {input_data.smiles}"
        )

    try:
        canonical = get_canonical_smiles(mol)
        props = get_molecular_properties(mol)
        mol_block = get_mol_block_3d(mol)
        svg = generate_2d_svg(mol)
        formula = get_molecular_formula(mol)
        inchi, inchi_key = get_inchi(mol)
        explanations = get_property_explanations()

        return MoleculeInfoResponse(
            success=True,
            smiles=input_data.smiles,
            canonical_smiles=canonical,
            molecular_properties=MolecularProperties(**props),
            mol_block_3d=mol_block,
            svg_2d=svg,
            formula=formula,
            inchi=inchi,
            inchi_key=inchi_key,
            property_explanations=explanations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing molecule: {str(e)}")
