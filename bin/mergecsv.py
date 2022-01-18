import pandas as pd
import sys

# Read the csv files and merge them
all_files = sys.argv[1:-1]
df_from_each_file = (pd.read_csv(f, sep=',') for f in all_files)
df_merged = pd.concat(df_from_each_file, ignore_index=False)
df_merged.to_csv(sys.argv[-1])
