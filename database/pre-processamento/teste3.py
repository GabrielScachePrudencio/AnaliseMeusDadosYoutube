import sys
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

df = pd.read_csv("historico_completo_com_target.csv")
outros = df[df["tema"] == "outros"]
top = outros["canal"].value_counts().head(60).index

with open("canais_amostra.txt", "w", encoding="utf-8") as f:
    for canal in top:
        mask = outros["canal"] == canal
        titulos = outros[mask]["titulo"].sample(min(3, mask.sum()), random_state=0)
        f.write(f"## {canal}\n")
        for t in titulos:
            f.write(f"   - {t}\n")
print("Salvo em canais_amostra.txt")