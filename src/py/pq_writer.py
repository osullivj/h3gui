# builtin
import logging
import os
import os.path
# 3rd pty
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq
# h3gui
import nd_consts
import nd_utils

logr = nd_utils.init_logging('pq_writer', console=True)

def write_parquet(base_name, csv_in_path, target_dir):
    table = pa_csv.read_csv(csv_in_path)
    pq_out_path = os.path.join(target_dir, f'{base_name}.parquet')
    pq.write_table(table, pq_out_path)
    return pq_out_path


if __name__ == '__main__':
    nd_utils.init_logging(__file__)
    source_files = nd_utils.file_list(nd_consts.PQ_DIR, 'FGB??8_200809[01]?.csv')
    logr.info(f'Source CSVs found in {nd_consts.PQ_DIR}\n{source_files}')
    for sf in source_files:
        source_path = os.path.join(nd_consts.PQ_DIR, sf)
        base_name = os.path.splitext(sf)[0]
        pq_out_path = write_parquet(base_name, source_path, nd_consts.PQ_DIR)
        logr.info(f'{pq_out_path} written')
