from pathlib import Path
import pandas as pd

from fertility_popeve.utils.config import load_config
from fertility_popeve.variant.protein_parser import parse_hgvsp

config = load_config()

input_file = Path(config["paths"]["missense"]) / "missense_table.parquet"
output_file = Path(config["paths"]["protein"]) / "protein_table.parquet"

output_file.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_parquet(input_file)

protein_records = []

for _, row in df.iterrows():
    result = parse_hgvsp(row["hgvsp"])

    if result is None:
        continue

    protein_records.append({
        **row.to_dict(),
        **result
    })

protein_df = pd.DataFrame(protein_records)
protein_df.to_parquet(output_file, index=False)

print(protein_df.head())
print(f"\nSaved {len(protein_df)} protein variants -> {output_file}")
