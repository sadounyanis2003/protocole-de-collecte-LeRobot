import pandas as pd
df = pd.read_parquet("/home/bakalem/Documents/base_donnée_LERobot/data/chunk-000/000001.parquet")
print(df)
df.to_csv("tout_le_parquet.csv", index=False)