# *-* coding:utf-8 *-*
"""Replace fragment genes with chloroplast-genome genes for shared taxa."""

from pathlib import Path

from Bio import SeqIO


FASTA_SUFFIXES = {".fa", ".fas", ".fasta"}


def _is_fasta(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in FASTA_SUFFIXES


def _species_name(description: str) -> str:
    """Extract Species_name from FASTA description (2nd pipe-delimited field)."""
    parts = description.strip().split("|")
    if len(parts) >= 2 and parts[1].strip():
        return parts[1].strip()
    return description.strip()


def run_replacement(cp_file, frag_file, out_dir, emit_log=print):
    """
    Merge chloroplast and fragment gene FASTA by Species_name.

    - Keep all sequences from chloroplast genome file.
    - Keep fragment sequences only when Species_name is absent in chloroplast file.
    - Output: {cp_stem}_replaced.fasta under out_dir.
    """
    cp_path = Path(cp_file)
    frag_path = Path(frag_file)
    out_path = Path(out_dir)

    if not _is_fasta(cp_path):
        emit_log(f"Invalid chloroplast gene file: {cp_path}", "WARNING")
        return False
    if not _is_fasta(frag_path):
        emit_log(f"Invalid fragment gene file: {frag_path}", "WARNING")
        return False

    out_path.mkdir(parents=True, exist_ok=True)
    out_file = out_path / f"{cp_path.stem}_replaced.fasta"

    cp_records = list(SeqIO.parse(str(cp_path), "fasta"))
    frag_records = list(SeqIO.parse(str(frag_path), "fasta"))

    cp_species = set()
    for rec in cp_records:
        cp_species.add(_species_name(rec.description))

    kept_frag = []
    replaced = 0
    for rec in frag_records:
        sp = _species_name(rec.description)
        if sp in cp_species:
            replaced += 1
            continue
        kept_frag.append(rec)

    merged = list(cp_records) + kept_frag
    written = SeqIO.write(merged, str(out_file), "fasta")

    emit_log(
        f"Replacement done: kept CP={len(cp_records)}, "
        f"removed FRAG={replaced}, kept FRAG={len(kept_frag)}, "
        f"total={written} → {out_file}",
        "SUCCESS",
    )
    return True
