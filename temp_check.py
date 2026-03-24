import pandas as pd

df = pd.read_csv(
    r"C:\Users\Usuario\Downloads\Datos\Datos\SECOP_II_-_Contratos_Electrónicos_20260322.csv",
    nrows=3,
    encoding='latin-1'
)
print(df.columns.tolist())