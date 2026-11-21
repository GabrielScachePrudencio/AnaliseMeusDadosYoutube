import pandas as pd

df = pd.read_csv("historico_completo.csv")
df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
df = df.sort_values("time_utc").reset_index(drop=True)

seq = pd.DataFrame({
    "ordem": range(1, len(df) + 1),
    "video_id": df["video_id"],
    "data_brt": df["data_brt"],
    "sessao_id": df["sessao_id"],
    "proximo_video_id": df["video_id"].shift(-1),
    "proximo_data_brt": df["data_brt"].shift(-1),
    "intervalo_s": df["tempo_ate_proximo_s"],
})

seq = seq.dropna(subset=["proximo_video_id"])
seq.to_csv("sequencia.csv", index=False, encoding="utf-8-sig")
print(f"Pronto: sequencia.csv ({len(seq)} linhas)")