import shutil
import socket
import urllib.error
from datetime import datetime
from pathlib import Path

import pandas as pd
from Bio import Entrez, SeqIO

from main_utils import get_query_accession


def my_efetch(accession, strand, seq_start, seq_stop):
    """Fetch sequence from NCBI with timeout protection."""
    handle = Entrez.efetch(
        db="nucleotide",
        rettype="gb",
        retmode="text",
        id=accession,
        strand=strand,
        seq_start=seq_start,
        seq_stop=seq_stop,
    )
    print(f"Extended start: {seq_start}, ", end="")
    print(f"Extended end: {seq_stop}, ", end="")
    print(f"Strand: {strand}")
    return handle


def parse_gb_record(handle, accession):
    """Parse GenBank record with timeout protection."""
    print(f"Parsing GenBank record for {accession}...")
    record = SeqIO.read(handle, "gb")
    print(f"Successfully parsed record for {accession}")
    return record


def filter_duplicate_key(wd, file):
    tmp_file = Path(wd) / Path("tmp_" + file)
    if (Path(wd) / Path(file)).stat().st_size > 0:
        shutil.copy2(Path(wd) / Path(file), tmp_file)
    key_list = []
    with open(Path(wd) / Path(file), "w") as fw:
        for record in SeqIO.parse(tmp_file, "fasta"):
            if record.description not in key_list:
                fw.write(">" + record.description + "\n")
                fw.write(str(record.seq) + "\n")
                key_list.append(record.description)
            else:
                print(f"Filtered duplicate sequence: {record.description}")
    tmp_file.unlink(missing_ok=True)


def normalize_allowed_taxa(allowed_taxa):
    """Normalize allowed taxonomy list, raise ValueError if empty."""
    if allowed_taxa is None:
        raise ValueError("allowed_taxa is required and must not be empty")
    taxa = [str(x).strip() for x in allowed_taxa if str(x).strip()]
    if not taxa:
        raise ValueError("allowed_taxa is required and must not be empty")
    return taxa


def check_taxonomy(record, allowed_taxa):
    """Check if record taxonomy matches allowed taxa (exact set intersection)."""
    taxa = normalize_allowed_taxa(allowed_taxa)
    lineage = {x.lower() for x in record.annotations.get("taxonomy", []) if x}
    organism = record.annotations.get("organism", "")
    if organism:
        lineage.add(organism.lower())
    allowed = {x.lower() for x in taxa}
    return bool(lineage & allowed)


def check_annotation(feature_list, key_annotations, exclude_sources):
    for exclude_source in exclude_sources:
        for feature in feature_list:
            if feature.find(exclude_source) >= 0:
                return False
    if not key_annotations:
        return True
    for key_annotation in key_annotations:
        for feature in feature_list:
            if feature.find(key_annotation) >= 0:
                return True
    return False


def write_seq_info(record, start, end, strand, wd, file):
    # todo: bould
    accession = record.id
    length = str(record.seq).lower().count("a")
    length += str(record.seq).lower().count("t")
    length += str(record.seq).lower().count("c")
    length += str(record.seq).lower().count("g")
    date = record.annotations["date"]
    description = record.description
    source = record.annotations["source"]
    organism = record.annotations["organism"]
    taxonomy = record.annotations["taxonomy"]
    taxonomy_str = ""
    for x in taxonomy:
        taxonomy_str += x + "|"
    taxonomy_str += organism
    if "references" in record.annotations.keys():
        reference = record.annotations["references"][0]
        title = reference.title
        authors = reference.authors
        journal = reference.journal
    else:
        title = "unknown"
        authors = "unknown"
        journal = "unknown"

    feature = record.features[0]

    if "organelle" in feature.qualifiers.keys():
        organelle = str(feature.qualifiers["organelle"][0])
    else:
        organelle = "unknown"

    if "mol_type" in feature.qualifiers.keys():
        mol_type = str(feature.qualifiers["mol_type"][0])
    else:
        mol_type = "unknown"

    # todo: the gb file may contain two db_xref, taxon and bold
    if "db_xref" in feature.qualifiers.keys():
        db_xref = "|".join(feature.qualifiers["db_xref"])
    else:
        db_xref = "unknown"

    if "specimen_voucher" in feature.qualifiers.keys():
        specimen_voucher = str(feature.qualifiers["specimen_voucher"][0])
    else:
        specimen_voucher = "unknown"

    if "country" in feature.qualifiers.keys():
        country = str(feature.qualifiers["country"][0])
    else:
        country = "unknown"

    if "lat_lon" in feature.qualifiers.keys():
        lat_lon = str(feature.qualifiers["lat_lon"][0])
    else:
        lat_lon = "unknown"

    if "collection_date" in feature.qualifiers.keys():
        collection_date = str(feature.qualifiers["collection_date"][0])
    else:
        collection_date = "unknown"

    if "collected_by" in feature.qualifiers.keys():
        collected_by = str(feature.qualifiers["collected_by"][0])
    else:
        collected_by = "unknown"

    if "identified_by" in feature.qualifiers.keys():
        identified_by = str(feature.qualifiers["identified_by"][0])
    else:
        identified_by = "unknown"

    with open(Path(wd) / Path(file), "a") as fw:
        fw.write(
            accession
            + "\t"
            + str(start)
            + "\t"
            + str(end)
            + "\t"
            + str(strand)
            + "\t"
            + str(length)
            + "\t"
            + date
            + "\t"
        )
        fw.write(
            description + "\t" + source + "\t" + organism + "\t" + taxonomy_str + "\t"
        )
        fw.write(
            title
            + "\t"
            + authors
            + "\t"
            + journal
            + "\t"
            + organelle
            + "\t"
            + mol_type
            + "\t"
            + db_xref
            + "\t"
        )
        fw.write(specimen_voucher + "\t" + country + "\t" + lat_lon + "\t")
        fw.write(collection_date + "\t" + collected_by + "\t" + identified_by + "\n")


def write_fas_file(record, start, end, strand, wd, file):
    description = record.description
    organism = record.annotations["organism"].replace(" ", "_")
    if start <= 0:
        start = 1
    end = len(record.seq) + start - 1
    if strand == 1:
        # if start <= 0:
        #     start = 1
        # end = len(record.seq) + start - 1
        fas_description = f">{record.id}:{start}-{end}|{organism}|{description}"
        fas_seq = str(record.seq)
    else:
        # if end <= 0:
        #     end = 1
        # start = len(record.seq) + end - 1
        # fas_description = f">{record.id}:{end}-{start}_reverse_complement|{organism}|{description}"
        fas_description = (
            f">{record.id}:{start}-{end}_reverse_complement|{organism}|{description}"
        )
        fas_seq = str(record.seq)  # 659
    with open(Path(wd) / Path(file), "a") as fw:
        fw.write(fas_description + "\n")
        fw.write(fas_seq + "\n")
    write_seq_info(
        record, start, end, strand, wd, file=Path(file).stem + "_seq_info.txt"
    )


def seq_check_download(
    wd,
    acc_file,
    out_file,
    key_annotations,
    exclude_sources,
    entrez_email,
    allowed_taxa,
    stop_flag=None,
):
    """download fasta files from Genbank according to given accessions"""
    # todo: use user provided email
    Entrez.email = entrez_email
    socket.setdefaulttimeout(180)  # cover my_efetch + parse_gb_record (network reads)
    acc_list = list(acc_file.index)
    max_retries = 3
    retry_count = {}
    print(f"Taxonomy whitelist: {allowed_taxa}")
    while len(acc_list) != 0:
        if stop_flag and stop_flag.is_set():
            print("Download stopped by user.")
            return
        accession = acc_list[0]
        if accession not in retry_count:
            retry_count[accession] = 0
        try:
            t0 = datetime.now()
            seq_start = int(acc_file.loc[accession, "start"])
            seq_stop = int(acc_file.loc[accession, "end"])
            strand = int(acc_file.loc[accession, "strand"])
            if strand == 2:
                seq_start, seq_stop = (seq_stop, seq_start)
            # print(f"start: {start}")
            # print(f"end: {end}")
            handle = my_efetch(
                accession=accession,
                strand=strand,
                seq_start=seq_start,
                seq_stop=seq_stop,
            )
            try:
                record = parse_gb_record(handle, accession)
            finally:
                handle.close()
            print(f"Actual sequence length: {len(record.seq)}")
            feature_list = []
            for feature in record.features:
                feature_list.extend(feature.qualifiers.values())
                # print(feature.qualifiers.values())
            feature_list = [x[0].replace(" ", "").lower() for x in feature_list]
            key_annotations = [x.replace(" ", "").lower() for x in key_annotations]
            exclude_sources = [x.replace(" ", "").lower() for x in exclude_sources]
            anno_ok = check_annotation(feature_list, key_annotations, exclude_sources)
            tax_ok = check_taxonomy(record, allowed_taxa)
            if anno_ok and tax_ok:
                write_fas_file(record, seq_start, seq_stop, strand, wd, file=out_file)
            else:
                reasons = []
                if not anno_ok:
                    reasons.append("annotation filter failed")
                if not tax_ok:
                    organism = record.annotations.get("organism", "unknown")
                    taxonomy = (
                        "; ".join(record.annotations.get("taxonomy", [])) or "unknown"
                    )
                    reasons.append(
                        f"taxonomy not in whitelist (organism={organism}; taxonomy={taxonomy})"
                    )
                print(f"{accession} rejected: {'; '.join(reasons)}")
                if not (
                    Path(wd) / f"erroneous_{Path(out_file).stem}_seq_info.txt"
                ).exists():
                    with (
                        Path(wd) / f"erroneous_{Path(out_file).stem}_seq_info.txt"
                    ).open("w") as fw:
                        fw.write(
                            "accession\tstart\tend\tstrand\tlength\tdate\tdescription\tsource\torganism\ttaxonomy\t"
                        )
                        fw.write(
                            "title\tauthors\tjournal\torganelle\tmol_type\tdb_xref\t"
                        )
                        fw.write("specimen_voucher\tcountry\tlat_lon\t")
                        fw.write("collection_date\tcollected_by\tidentified_by\n")
                write_fas_file(
                    record,
                    seq_start,
                    seq_stop,
                    strand,
                    wd,
                    file="erroneous_" + out_file,
                )
            t1 = datetime.now()
            elapsed = (t1 - t0).total_seconds()
            print(f"{accession} downloaded in {elapsed:.2f} seconds.\n")
            acc_list.pop(0)
        except ValueError as e:  # features location no correct or SeqIO parsing error
            acc_list.pop(0)
            with open(Path(wd) / Path("value_error_list.txt"), "a") as fw:
                fw.write(accession + "\n")
            print(f"ValueError: {e}, skip {accession}")
        except urllib.error.HTTPError:  # HTTP Error 400, wrongly parsed accession
            acc_list.pop(0)
            with open(Path(wd) / Path("bad_request_list.txt"), "a") as fw:
                fw.write(accession + "\n")
            print(f"Bad request: {accession}. Move on to the next sequence.")
        except (socket.timeout, TimeoutError):
            retry_count[accession] += 1
            if retry_count[accession] < max_retries:
                print(
                    f"Time out, retrying {accession} "
                    f"({retry_count[accession]}/{max_retries})..."
                )
            else:
                acc_list.pop(0)
                print(f"Time out, skipped {accession} after {max_retries} attempts.")
                with open(Path(wd) / Path("bad_request_list.txt"), "a") as fw:
                    fw.write(accession + "\n")
        except Exception as result:
            retry_count[accession] += 1
            if retry_count[accession] < max_retries:
                print(
                    f"Error: {result}, retrying {accession} "
                    f"({retry_count[accession]}/{max_retries})..."
                )
            else:
                acc_list.pop(0)
                print(
                    f"Error: {result}, skipped {accession} after {max_retries} attempts."
                )
                with open(Path(wd) / Path("bad_request_list.txt"), "a") as fw:
                    fw.write(accession + "\n")


def seq_check_download_main(
    wd,
    acc_file,
    out_file,
    key_annotations,
    exclude_sources,
    entrez_email,
    allowed_taxa,
    extend=False,
    stop_flag=None,
):
    print("Downloading sequences...")
    df = pd.read_table(Path(wd) / Path(acc_file), sep="\t", engine="python")
    # drop duplicate
    df.index = df["subject_acc.ver"]
    file_list = [f.name for f in Path(wd).iterdir()]

    # def get_accession(record):
    #     accession = record.description.split(" ")[0].split("|")[0].split(":")[0]
    #     return accession

    index_list = list(df.index)
    if out_file in file_list:
        filter_duplicate_key(wd, out_file)
        seq_dict = SeqIO.to_dict(
            SeqIO.parse(Path(wd) / Path(out_file), "fasta"),
            key_function=get_query_accession,
        )
        print(f"Correct sequences already downloaded: {len(seq_dict.keys())}")
        index_list = list(set(index_list) - set(seq_dict.keys()))
    if "erroneous_" + out_file in file_list:
        filter_duplicate_key(wd, "erroneous_" + out_file)
        seq_dict = SeqIO.to_dict(
            SeqIO.parse(Path(wd) / Path("erroneous_" + out_file), "fasta"),
            key_function=get_query_accession,
        )
        print(f"Erroneous sequences already downloaded: {len(seq_dict.keys())}")
        index_list = list(set(index_list) - set(seq_dict.keys()))
    if Path(out_file).stem + "_seq_info.txt" not in file_list:
        with open(Path(wd) / Path(Path(out_file).stem + "_seq_info.txt"), "w") as fw:
            fw.write(
                "accession\tstart\tend\tstrand\tlength\tdate\tdescription\tsource\torganism\ttaxonomy\t"
            )
            fw.write("title\tauthors\tjournal\torganelle\tmol_type\tdb_xref\t")
            fw.write("specimen_voucher\tcountry\tlat_lon\t")
            fw.write("collection_date\tcollected_by\tidentified_by\n")
    else:
        seq_info_path = Path(wd) / Path(Path(out_file).stem + "_seq_info.txt")
        try:
            seq_info = pd.read_table(seq_info_path, sep="\t", engine="python")
            seq_info.drop_duplicates(subset=["accession"], keep="first", inplace=True)
            seq_info.to_csv(seq_info_path, sep="\t", index=False)
        except PermissionError:
            print(
                f"WARNING: Permission denied when updating {seq_info_path.name}. "
                "Close the file if it is open in another program, then retry. "
                "Download aborted."
            )
            return
        except Exception as e:
            print(
                f"WARNING: Failed to deduplicate {seq_info_path.name}: {e}. "
                "Download aborted."
            )
            return

    index_list.sort()
    print(f"Sequences to download: {len(index_list)}")
    if not extend:
        df1 = df.loc[index_list][["s_start", "s_end", "s_strand"]].copy()
    else:
        df1 = df.loc[index_list][["s_extstart", "s_extend", "s_strand"]].copy()
    df1.columns = ["start", "end", "strand"]
    df1["strand"] = df1["strand"].map({True: 1, False: 2}).astype(int)

    fw = open(Path(wd) / Path("value_error_list.txt"), "w")
    fw.close()
    fw = open(Path(wd) / Path("bad_request_list.txt"), "w")
    fw.close()

    seq_check_download(
        wd=wd,
        acc_file=df1,
        out_file=out_file,
        key_annotations=key_annotations,
        exclude_sources=exclude_sources,
        entrez_email=entrez_email,
        allowed_taxa=allowed_taxa,
        stop_flag=stop_flag,
    )

    with open(Path(wd) / Path("value_error_list.txt"), "r") as fw:
        value_error_list = fw.read().splitlines()
        if len(value_error_list) > 0:
            print(
                f"{len(value_error_list)} value errors, "
                "the accession numbers were save in value_error_list.txt"
            )
    with open(Path(wd) / Path("bad_request_list.txt"), "r") as fw:
        bad_request_list = fw.read().splitlines()
        if len(bad_request_list) > 0:
            print(
                f"{len(bad_request_list)} bad requests, "
                "the accession numbers were save in bad_request_list.txt"
            )

    print("All sequences successfully downloaded!")
    print(f"Correct sequences were saved in {out_file}.")
    print(f"Erroneous sequences were saved in erroneous_{out_file}")
