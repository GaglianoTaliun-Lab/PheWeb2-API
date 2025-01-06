import pysam
import os
from collections import defaultdict


class SNPFetcher:
    def __init__(self, file_base_path, window_size=200):
        self.file_base_path = file_base_path
        self.window_size = window_size

    def group_snps_by_region(self, snp_list):
        """
        split SNP list into groups based on window size

        Args:
            snp_list (list): SNP list, format ["chrom-pos-ref-alt", ...]

        Returns:
            dict: splited list of SNPs
        """
        snp_list = sorted(
            snp_list, key=lambda x: (x.split("-")[0], int(x.split("-")[1]))
        )
        grouped_snps = defaultdict(list)
        current_group = []
        current_chrom, current_start = None, None

        for snp in snp_list:
            chrom, pos = snp.split("-")[:2]
            pos = int(pos)
            if not current_group or (
                current_chrom == chrom and pos - current_start <= self.window_size
            ):
                current_group.append(snp)
                current_chrom, current_start = chrom, pos
            else:
                grouped_snps[(current_chrom, current_start)].extend(current_group)
                current_group = [snp]
                current_chrom, current_start = chrom, pos

        if current_group:
            grouped_snps[(current_chrom, current_start)].extend(current_group)

        return grouped_snps

    def fetch_snp_info_with_tbi(self, key, snp_list):
        """
        use tbi to get SNP info from .gz

        Args:
            key (str): stratification
            snp_list (list): missing SNP list

        Returns:
            list: missing SNP GWAS info
        """
        file_path = os.path.join(self.file_base_path, f"{key}.gz")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        # print("found file")
        tabix_file = pysam.TabixFile(file_path)
        grouped_snps = self.group_snps_by_region(snp_list)
        # print(grouped_snps)
        results = []

        for (chrom, start), snps in grouped_snps.items():
            region_start = int(start) - 100 * self.window_size
            region_end = int(start) + 100 * self.window_size
            try:
                for record in tabix_file.fetch(chrom, region_start, region_end):
                    # TODO: it seems like tabix index doesn't match the position
                    record_data = record.strip().split("\t")
                    # print(record_data)
                    pos = record_data[1]
                    # print(pos)
                    for snp in snps:
                        parts = snp.split("-")
                        if (
                            int(parts[1]) == int(pos)
                            and record_data[2] == parts[2]
                            and record_data[3] == parts[3]
                        ):
                            # print("found snp in raw file")
                            # print(record_data[2] == parts[2] and record_data[3] == parts[3])
                            results.append(
                                {
                                    "chrom": chrom,
                                    "pos": pos,
                                    "ref": record_data[2],
                                    "alt": record_data[3],
                                    "rsids": record_data[4],
                                    "nearest_genes": record_data[5],
                                    "pval": record_data[-4],
                                    "beta": record_data[-3],
                                    "sebeta": record_data[-2],
                                    "af": record_data[-1],
                                }
                            )
                    # if any((int(snp.split('-')[1]) == int(pos) and record_data[2] == snp.split('-')[2] and record_data[3] == snp.split('-')[3]) for snp in snps):
                    #     print("found snp in raw file")
                    #     for snp in snps:
                    #         parts = snp.split('-')
                    #         if len(parts) >= 4:  # 确保 snp 格式正确
                    #             print(record_data[2] == parts[2] and record_data[3] == parts[3])
                    #         else:
                    #             print(f"Invalid SNP format: {snp}")
                    #     # print(record_data[2] == snp.split('-')[2] and record_data[3] == snp.split('-')[3])
                    #     results.append({
                    #         "chrom": chrom,
                    #         "pos": pos,
                    #         "ref": record_data[2],
                    #         "alt": record_data[3],
                    #         "rsids": record_data[4],
                    #         "nearest_genes": record_data[5],
                    #         "pval": record_data[-4],
                    #         "beta": record_data[-3],
                    #         "sebeta": record_data[-2],
                    #         "af": record_data[-1],
                    #     })
            except ValueError as e:
                print(
                    f"Error fetching region {chrom}:{region_start}-{region_end} -> {e}"
                )

        return results

    def process_keys(self, api_data):
        """
        process gwas_missing_data back from UI and return results

        Args:
            api_data (dict): data back from UI, format {stratification: [missing SNP list]}。

        Returns:
            dict: missing SNP info list, format {stratification: [SNP GWAS info]}
        """
        results = {}
        print("Processing keys")

        for key, snp_list in api_data.items():
            print(f"Fetching SNPs for {key}")
            try:
                snp_info = self.fetch_snp_info_with_tbi(key, snp_list)
                results[key] = snp_info
            except Exception as e:
                results[key] = {"error": str(e)}

        return results
