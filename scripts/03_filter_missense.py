from pathlib import Path
import pandas as pd

from fertility_popeve.utils.config import load_config

config = load_config()

input_file = Path(config["paths"]["annotation"]) / "variant_table.parquet"
output_file = Path(config["paths"]["missense"]) / "missense_table.parquet"

output_file.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_parquet(input_file)

df = df[
    df["consequence"].str.contains("missense_variant", na=False)
    & df["hgvsp"].notna()
    & (df["hgvsp"] != "")
].copy()

df.to_parquet(output_file, index=False)

print(df.head())
print(f"\nSaved {len(df)} missense variants -> {output_file}")
