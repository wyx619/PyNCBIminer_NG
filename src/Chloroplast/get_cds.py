from pathlib import Path
from Bio import SeqIO
from datetime import datetime
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

import warnings
warnings.filterwarnings("ignore")



_cds_list = None
_alternative_name = None


def init_worker(cds_list, alternative_name):
    global _cds_list, _alternative_name
    _cds_list = cds_list
    _alternative_name = alternative_name


def extract_gene_name(feature):
    if "gene" in feature.qualifiers:
        gene_name = feature.qualifiers["gene"][0]
        return _alternative_name.get(gene_name, gene_name)
    
    if "product" in feature.qualifiers:
        product_name = feature.qualifiers["product"][0]
        return _alternative_name.get(product_name, "unknown")
    
    return "unknown"


def extract_sequence(seq_record, feature):

    seq = seq_record.seq
    parts = feature.location.parts if hasattr(feature.location, 'parts') else [feature.location]
    seq_parts = []
    for part in parts:
        if part is None: 
            continue
        if part.strand is None:
            part.strand = 1
        if part.strand == -1:
            seq_parts.append(str(seq[part.start:part.end].reverse_complement()))
        else:
            seq_parts.append(str(seq[part.start:part.end]))
    fas_seq = "".join(seq_parts)
    return fas_seq


def process_feature(seq_record, feature, df0_row, df1_row, sequences):
    gene_name = extract_gene_name(feature)
    if gene_name not in _cds_list:
        return
    
    fas_seq = extract_sequence(seq_record, feature)
    fas_description = f">{seq_record.id}|{feature.location}"
    
    if df0_row[gene_name] == 0:
        df0_row["cds_num"] += 1
        df1_row[gene_name] = str(feature.location)
    else:
        df1_row[gene_name] += f"|{feature.location}"
    
    df0_row[gene_name] += 1
    sequences.setdefault(gene_name, []).append((fas_description, fas_seq))


def process_gb_file(args):
    gb_file_name, in_path, out_path = args
    
    df0_row = {gene: 0 for gene in _cds_list}
    df0_row['cds_num'] = 0
    df1_row = {gene: "" for gene in _cds_list}
    df1_row['cds_num'] = ""
    sequences = {}
    
    try:
        seq_record = SeqIO.read(Path(in_path) / gb_file_name, "gb")
        from Bio.Seq import UndefinedSequenceError
        try:
            str(seq_record.seq)
        except UndefinedSequenceError:
            return df0_row, df1_row, sequences
        for feature in seq_record.features:
            if feature.type not in ("CDS", "rRNA"):
                continue
            process_feature(seq_record, feature, df0_row, df1_row, sequences)
    except Exception as e:
        print(f"Error extracting: {e} - {gb_file_name}\n")
    
    df1_row["cds_num"] = str(df0_row["cds_num"])
    return df0_row, df1_row, sequences


def get_cds(in_path, out_path, threads=3):
    global _cds_list, _alternative_name
    
    in_path = Path(in_path)
    out_path = Path(out_path)
    
    out_path.mkdir(parents=True, exist_ok=True)
    
    _cds_list = ['accD', 'atpA', 'atpB', 'atpE', 'atpF', 'atpH', 'atpI', 'ccsA', 'cemA',
                 'clpP', 'infA', 'matK', 'ndhA', 'ndhB', 'ndhC', 'ndhD', 'ndhE', 'ndhF', 'ndhG', 'ndhH', 'ndhI',
                 'ndhJ', 'ndhK', 'petA', 'petB', 'petD', 'petG', 'petL', 'petN', 'psaA', 'psaB', 'psaC', 'psaI',
                 'psaJ', 'psbA', 'psbB', 'psbC', 'psbD', 'psbE', 'psbF', 'psbH', 'psbI', 'psbJ', 'psbK', 'psbL',
                 'psbM', 'psbN', 'psbT', 'psbZ', 'rbcL', 'rpl14', 'rpl16', 'rpl2', 'rpl20', 'rpl22', 'rpl23',
                 'rpl32', 'rpl33', 'rpl36', 'rpoA', 'rpoB', 'rpoC1', 'rpoC2', 'rps11', 'rps12', 'rps14', 'rps15',
                 'rps16', 'rps18', 'rps19', 'rps2', 'rps3', 'rps4', 'rps7', 'rps8', 'rrn16', 'rrn23', 'rrn4.5',
                 'rrn5', 'ycf1', 'ycf15', 'ycf2', 'ycf3', 'ycf4', 'ycf68']

    _alternative_name = {'16S ribosomal RNA': 'rrn16', '23S ribosomal RNA': 'rrn23',
                        '4.5S ribosomal RNA': 'rrn4.5', '5S ribosomal RNA': 'rrn5',
                        'rrn16S': 'rrn16', 'rrn23S': 'rrn23',
                        'rrn4.5S': 'rrn4.5', 'rrn5S': 'rrn5'}
    
    for cds in _cds_list:
        (out_path / f"{cds}.fasta").touch()
    
    gb_file_list = [f.name for f in in_path.iterdir() if f.suffix.lower() in {".gb", ".gbf", ".gbk"}]
    
    print(f"Start extracting CDS in {len(gb_file_list)} gb files...")
    
    df0 = pd.DataFrame(0, index=[Path(x).stem for x in gb_file_list], columns=_cds_list+['cds_num'], dtype=int)
    df1 = pd.DataFrame("", index=[Path(x).stem for x in gb_file_list], columns=_cds_list+['cds_num'], dtype=str)
    
    threads = max(1, min(threads or multiprocessing.cpu_count(), len(gb_file_list)))

    
    task_args = [(gb_name, str(in_path), str(out_path)) for gb_name in gb_file_list]
    all_sequences = {gene: [] for gene in _cds_list}
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(process_gb_file, arg): Path(arg[0]).stem for arg in task_args}
        
        for future in as_completed(futures):
            gb_name = futures[future]
            #print(gb_name)
            try:
                df0_row, df1_row, sequences = future.result()
                df0.loc[gb_name] = pd.Series(df0_row)
                df1.loc[gb_name] = pd.Series(df1_row)
                for gene, seq_list in sequences.items():
                    all_sequences[gene].extend(seq_list)
            except Exception as e:
                print(f"Error collecting results for {gb_name}: {e}\n")
    

    for gene, seq_list in all_sequences.items():
        if seq_list:
            from Bio.Seq import Seq
            id_seq_dict = {}
            for desc, seq in seq_list:
                if not seq:
                    continue
                header = desc.lstrip('>')
                if header in id_seq_dict:
                    if len(seq) > len(id_seq_dict[header]):
                        id_seq_dict[header] = seq
                else:
                    id_seq_dict[header] = seq
            records = []
            for header, seq in id_seq_dict.items():
                record = SeqIO.SeqRecord(
                    seq=Seq(seq),
                    id=header,
                    description='',
                )
                records.append(record)
            if records:
                SeqIO.write(records, out_path / f"{gene}.fasta", "fasta")
    

    df_info = pd.read_csv(in_path / "gb_info.csv", usecols=['filename', 'organism'])
    df0 = pd.merge(df_info, df0, left_on='filename', right_index=True, how='right')
    df0.to_csv(out_path / "cds_num.csv", index=False, sep=",")
    df1.to_csv(out_path / "cds_loc.txt", index=True, sep="\t")
    print("Summary of cds number written in cds_num.csv")
    print("Summary of cds location written in cds_loc.txt")
    
    deleted_files = []
    for file_path in out_path.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size == 0:
            try:
                file_path.unlink()
                deleted_files.append(str(file_path))
                print(f"Deleted empty file: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
    
    print(f"\nOperation completed, deleted {len(deleted_files)} empty files")


class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """
        Function: Coding sequences (CDSs) are extracted from all GenBank files (.gb extension) within the input gb_folder_path.Each CDS gene is subsequently written to an individual FASTA file, where the filename corresponds to the standardized gene
        nomenclature. These segmented sequence files are systematically stored within the designated cds_folder_path.
        Author: Ruijing Cheng
        Organization: 
        GitHub Site:
        Usage Example:
          添加示例
        """
        return f"{description}\n\n{help_text}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument("-i", "--input_dir", help="Input directory path of gb file.", required=True)
    parser.add_argument("-o", "--output_dir", help="Output directory for CDS sequence(.fasta)", required=True)
    parser.add_argument("-t", "--threads", type=int, default=3, help="Number of processes to use %(default)s", required=False)
    args = parser.parse_args()


    print(f"Input directory:     {args.input_dir}")
    print(f"Output directory:    {args.output_dir}")
    print(f"Processing processes: {args.threads}")


    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    threads = args.threads

    time0 = datetime.now()
    get_cds(input_dir, output_dir, threads)
    time1 = datetime.now()
    print("Total running time: %s seconds" % (time1 - time0))
