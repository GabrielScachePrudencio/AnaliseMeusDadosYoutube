import json
import os
import re
import sys

import numpy as np
import pandas as pd
import requests
from lightgbm import LGBMClassifier
from sklearn.preprocessing import LabelEncoder

sys.stdout.reconfigure(encoding="utf-8")

# ===================== CONFIGURAÇÃO =====================
ARQUIVO = "histórico-de-visualização.json"   # JSON com os vídeos assistidos
API_KEY = "AIzaSyCL_dNwFdJFzyDNUqZOLr56E3e6bSNODh8"          # YouTube Data API v3
CSV_LIMPO = "historico_limpo.csv"
CACHE_API = "metadados_cache.json"       # guarda o que já foi buscado
CSV_FINAL = "historico_enriquecido.csv"

CATEGORIAS = {
    "1": "Filmes e Animação", "2": "Autos", "10": "Música", "15": "Animais",
    "17": "Esportes", "19": "Viagens", "20": "Games", "22": "Pessoas e Blogs",
    "23": "Comédia", "24": "Entretenimento", "25": "Notícias e Política",
    "26": "Estilo e Como Fazer", "27": "Educação", "28": "Ciência e Tecnologia",
    "29": "Ativismo",
}


# ===================== ETAPA 1: LIMPEZA =====================
def etapa_limpeza():
    with open(ARQUIVO, encoding="utf-8") as f:
        dados = json.load(f)

    linhas = []
    for r in dados:
        titulo = r.get("title", "")
        if not titulo.startswith("Watched "):
            continue
        if any(d.get("name") == "From Google Ads" for d in r.get("details", [])):
            continue  # anúncio
        m = re.search(r"v=([\w-]{11})", r.get("titleUrl", ""))
        if not m:
            continue  # vídeo removido, sem link
        subs = r.get("subtitles") or []
        linhas.append({
            "video_id": m.group(1),
            "titulo": titulo.replace("Watched ", "", 1),
            "canal": subs[0]["name"] if subs else None,
            "time_utc": r["time"],
        })

    if not linhas:
        raise SystemExit("Nenhum vídeo real encontrado. Confira se o arquivo é o certo.")

    df = pd.DataFrame(linhas)
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
    df["data_brt"] = df["time_utc"].dt.tz_convert("America/Sao_Paulo")
    df = df.sort_values("data_brt").reset_index(drop=True)
    df.to_csv(CSV_LIMPO, index=False)
    print(f"[1] {len(dados)} registros no arquivo -> {len(df)} vídeos reais "
          f"({df['video_id'].nunique()} únicos)")
    return df


# ===================== ETAPA 2: API DO YOUTUBE =====================
def iso_para_segundos(d):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return None
    dias, h, mi, s = (int(x or 0) for x in m.groups())
    return dias * 86400 + h * 3600 + mi * 60 + s


def etapa_api(df):
    cache = {}
    if os.path.exists(CACHE_API):
        with open(CACHE_API, encoding="utf-8") as f:
            cache = json.load(f)

    ids = df["video_id"].unique().tolist()
    faltando = [i for i in ids if i not in cache]
    print(f"[2] {len(ids)} vídeos únicos, {len(faltando)} ainda sem metadados")

    for i in range(0, len(faltando), 50):
        lote = faltando[i:i + 50]
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,statistics,contentDetails",
                    "id": ",".join(lote), "key": API_KEY},
            timeout=30,
        )
        if resp.status_code != 200:
            print("Erro da API:", resp.status_code, resp.text[:300])
            break  # o que já foi buscado fica salvo no cache

        achados = {item["id"]: item for item in resp.json().get("items", [])}
        for vid in lote:
            item = achados.get(vid)
            if item is None:
                cache[vid] = None  # apagado ou privado
                continue
            cache[vid] = {
                "categoria_id": item["snippet"].get("categoryId"),
                "views": int(item.get("statistics", {}).get("viewCount", 0)),
                "duracao_s": iso_para_segundos(item["contentDetails"].get("duration")),
            }

        with open(CACHE_API, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        print(f"    {min(i + 50, len(faltando))}/{len(faltando)} buscados")

    meta = pd.DataFrame(
        [{"video_id": k, **v} for k, v in cache.items() if v is not None]
    )
    df = df.merge(meta, on="video_id", how="inner")
    df["categoria"] = df["categoria_id"].map(CATEGORIAS).fillna("Outros")
    df["is_short"] = (
        (df["duracao_s"] <= 60) | df["titulo"].str.lower().str.contains("#shorts")
    ).astype(int)
    df = df.sort_values("data_brt").reset_index(drop=True)
    df.to_csv(CSV_FINAL, index=False)
    print(f"[2] {len(df)} assistidas com metadados salvas em {CSV_FINAL}")
    return df


# ===================== ETAPA 3: MODELO =====================
def etapa_modelo(df):
    df = df.copy()
    df["hora"] = df["data_brt"].dt.hour
    df["dia_semana"] = df["data_brt"].dt.dayofweek
    df["log_views"] = np.log1p(df["views"])
    df["minutos_desde_anterior"] = (
        df["data_brt"].diff().dt.total_seconds().div(60).clip(upper=720)
    )
    df["categoria_anterior"] = df["categoria"].shift(1)
    df["alvo"] = df["categoria"].shift(-1)  # categoria do PRÓXIMO vídeo
    df = df.dropna(subset=["alvo", "categoria_anterior"]).reset_index(drop=True)

    todas = sorted(df["categoria"].unique())
    for col in ["categoria", "categoria_anterior"]:
        df[col] = pd.Categorical(df[col], categories=todas)

    features = ["hora", "dia_semana", "categoria", "log_views", "duracao_s",
                "is_short", "minutos_desde_anterior", "categoria_anterior"]

    le = LabelEncoder().fit(df["alvo"])
    y = le.transform(df["alvo"])
    X = df[features]

    corte = int(len(df) * 0.8)  # divisão temporal: passado treina, futuro testa
    X_tr, X_te, y_tr, y_te = X.iloc[:corte], X.iloc[corte:], y[:corte], y[corte:]
    print(f"[3] treino: {len(X_tr)} | teste: {len(X_te)} | classes: {len(le.classes_)}")

    modelo = LGBMClassifier(n_estimators=300, learning_rate=0.05,
                            num_leaves=15, min_child_samples=20, verbose=-1)
    modelo.fit(X_tr, y_tr)

    proba = modelo.predict_proba(X_te)
    classes = modelo.classes_
    pred = classes[proba.argmax(axis=1)]
    top3 = classes[np.argsort(proba, axis=1)[:, -3:]]

    acc = (pred == y_te).mean()
    acc3 = np.mean([y in t for y, t in zip(y_te, top3)])

    mais_comum = pd.Series(y_tr).mode()[0]
    base_maioria = (y_te == mais_comum).mean()
    base_repetir = (le.transform(df["categoria"].astype(str).iloc[corte:]) == y_te).mean()

    print("\n=== RESULTADOS (dados de teste) ===")
    print(f"Modelo, acerto exato:          {acc:.1%}")
    print(f"Modelo, acerto no top 3:       {acc3:.1%}")
    print(f"Baseline: sempre a mais comum ({le.classes_[mais_comum]}): {base_maioria:.1%}")
    print(f"Baseline: repetir a categoria atual: {base_repetir:.1%}")

    imp = pd.Series(modelo.feature_importances_, index=features).sort_values(ascending=False)
    print("\nImportância das variáveis:")
    print(imp.to_string())


# ===================== EXECUÇÃO =====================
if __name__ == "__main__":
    df = etapa_limpeza()
    df = etapa_api(df)
    etapa_modelo(df)