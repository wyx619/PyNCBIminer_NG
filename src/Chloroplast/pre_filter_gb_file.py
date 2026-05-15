from pathlib import Path
import shutil

import pandas as pd
from Bio import SeqIO

from Chloroplast.PPA_80_CDS import PPA_80_CDS


def extract_meta(gb_file_path, species_level=False):
    gb_file_path = Path(gb_file_path)
    accession = None
    organism = None
    taxon = None
    reject_reason = None

    with open(gb_file_path, "r") as f:
        for line in f:
            if line.startswith("ACCESSION") and accession is None:
                accession = line.strip().split()[1]
            elif line.startswith("KEYWORDS"):
                if "UNVERIFIED" in line:
                    reject_reason = "UNVERIFIED"
                    break
            elif line.startswith("  ORGANISM") and organism is None:
                organism = line.strip().split(None, 1)[1]
                if " sp." in organism:
                    reject_reason = f"ambiguous: {organism}"
                    break
                if " x " in organism:
                    reject_reason = f"hybrid: {organism}"
                    break                
                if species_level:
                    taxon = " ".join(organism.split()[:2])
                else:
                    taxon = organism
            if accession and organism and taxon is not None:
                break

    if reject_reason:
        gb_file_path.replace(gb_file_path.with_suffix(".unusable"))
        return accession, organism, taxon, True

    return accession, organism, taxon, False


def scan_gb_folder(in_path, species_level=False):
    in_path = Path(in_path)
    gb_files = sorted(in_path.glob("*.gb"))
    results = []
    for f in gb_files:
        acc, org, taxon, rejected = extract_meta(f, species_level)
        results.append({
            "filename": f.stem,
            "accession": acc,
            "organism": org,
            "taxon": taxon,
            "reject": rejected,
        })
    return results


def extract_gb_details(gb_file_path):
    rec = SeqIO.read(gb_file_path, "genbank")
    accession = rec.annotations.get("accessions", [""])[0]
    date = rec.annotations.get("date", "")
    journals = [
        ref.journal for ref in rec.annotations.get("references", [])
        if "Unpublished" not in ref.journal
    ]
    length = len(rec.seq)
    cds_genes = set()
    for feature in rec.features:
        if feature.type == "CDS":
            gene = feature.qualifiers.get("gene", [""])[0]
            std_name = PPA_80_CDS.get(gene)
            if std_name is not None:
                cds_genes.add(std_name)
    return {
        "accession": accession,
        "date": date,
        "journals": "|".join(journals),
        "length": length,
        "cds_count": len(cds_genes),
    }


def pre_filter(in_path, out_path=None, keep_latest=3, species_level=False):
    in_path = Path(in_path)
    records = scan_gb_folder(in_path, species_level)

    all_details = []
    for r in records:
        if r["reject"]:
            all_details.append({
                "accession": r["accession"],
                "date": "",
                "journals": "",
                "length": 0,
                "cds_count": 0,
                "filename": r["filename"],
                "organism": r["organism"],
                "taxon": r["taxon"],
                "reject": True,
            })
        else:
            gb_file = in_path / f"{r['filename']}.gb"
            details = extract_gb_details(gb_file)
            details["filename"] = r["filename"]
            details["organism"] = r["organism"]
            details["taxon"] = r["taxon"]
            details["reject"] = False
            all_details.append(details)

    df = pd.DataFrame(all_details)
    df["parsed_date"] = pd.to_datetime(df["date"], format="%d-%b-%Y", errors="coerce")
    df["has_journals"] = df["journals"].astype(bool)

    df["keep"] = False

    for taxon, group in df[~df["reject"]].groupby("taxon"):
        group_sorted = group.sort_values(
            ["has_journals", "cds_count", "length", "parsed_date"],
            ascending=[False, False, False, False],
        )
        kept = []
        seen_dates = set()
        for idx in group_sorted.index:
            dt = group_sorted.loc[idx, "parsed_date"]
            if dt in seen_dates:
                continue
            seen_dates.add(dt)
            kept.append(idx)
            if len(kept) >= keep_latest:
                break
        for idx in kept:
            df.loc[idx, "keep"] = True

    if out_path is not None:
        out_path = Path(out_path)
        out_path.mkdir(parents=True, exist_ok=True)
        for stale in out_path.glob("*.gb"):
            stale.unlink()
        for _, row in df[df["keep"]].iterrows():
            src = in_path / f"{row['filename']}.gb"
            dst = out_path / f"{row['filename']}.gb"
            shutil.copy2(src, dst)
        df.to_csv(out_path / "pre_filter.csv", index=False)

    return df


if __name__ == "__main__":
    print("=== species_level=False (varieties separate) ===")
    df=pre_filter( in_path=r'tests\Geum_rupestre_ori_seq',
    out_path=r'tests\Geum_rupestre_ori_seq\filtered', 
    keep_latest=3, 
    species_level=True)

