import re
import pandas as pd

ENTRADA = "historico_enriquecido.csv"
SAIDA = "historico_com_target.csv"

# A ordem importa: o primeiro tema que casar ganha.
REGRAS = [
    ("anime_musica", [r"\bopening\b", r"\bending\b", r"\bost\b", r"\bamv\b", r"lyrics?", r"\bcover\b",
                      r"\bft\.", r"rap (de )?anime", r"anime (song|music|rap)", r"nightcore"]),
    ("musica_instrumental", [r"epic version", r"orchestra", r"orquestra", r"\bpiano\b", r"\bviolin\b",
                             r"violino", r"1 hour", r"\b8d\b", r"trilha sonora", r"soundtrack",
                             r"instrumental", r"\bguitar\b", r"violão"]),
    ("anime_geral", [r"\banime\b", r"epis[oó]dio", r"dublado", r"legendado", r"crunchyroll", r"naruto",
                     r"jujutsu", r"attack on titan", r"one piece", r"dragon ball", r"demon slayer",
                     r"mahoraga", r"megumi", r"\baot\b", r"boruto", r"bleach", r"hunter x hunter",
                     r"#anime", r"mang[aá]"]),
    ("musica_geral", [r"official (music )?video", r"clipe", r"ao vivo.*show", r"[aá]lbum", r"playlist",
                      r"\bvevo\b", r"\bm[uú]sica\b", r"\bmusic\b", r"\bsong\b", r"\bremix\b"]),
    ("futebol_geral", [r"futebol", r"\bgol\b", r"\bgols\b", r"lances", r"campeonato", r"brasileir[aã]o",
                       r"libertadores", r"champions", r"copa do mundo", r"neymar", r"messi", r"cristiano ronaldo",
                       r"flamengo", r"corinthians", r"palmeiras", r"#futebol", r"transfer[eê]ncia", r"vianalista"]),
    ("esportes_geral", [r"\bnba\b", r"\bufc\b", r"\bf1\b", r"f[oó]rmula 1", r"\bmma\b", r"v[oô]lei",
                        r"basquete", r"\btreino\b", r"muscula[cç][aã]o", r"\bboxe\b", r"nfl", r"t[eê]nis"]),
    ("gameplay_geral", [r"gameplay", r"walkthrough", r"let'?s play", r"speedrun", r"minecraft", r"fortnite",
                        r"free fire", r"valorant", r"league of legends", r"\blol\b", r"roblox", r"\bgta\b",
                        r"cs ?go", r"counter-strike", r"\bpartida\b", r"\blive\b.*jog", r"zerando"]),
    ("games_noticias_dicas", [r"review.*(jogo|game)", r"lan[cç]amento.*(jogo|game)", r"trailer.*(jogo|game)",
                              r"\bbuild\b", r"tier list", r"\bgame\b", r"\bgames\b", r"\bjogo\b", r"\bjogos\b",
                              r"playstation", r"\bps5\b", r"xbox", r"nintendo", r"\bsteam\b"]),
    ("humor_memes", [r"\bmeme", r"engra[cç]ado", r"\breact\b", r"tentar n[aã]o rir", r"com[eé]dia",
                     r"pegadinha", r"#humor", r"#meme", r"zoeira", r"try not to laugh", r"\bfunny\b"]),
    ("exploracao_aventura", [r"explorador", r"aventura", r"sobreviv[eê]ncia", r"expedi[cç][aã]o",
                             r"viagem", r"\bzingo\b", r"explorer", r"survival", r"atrapado", r"selva"]),
    ("historia_geral", [r"hist[oó]ria", r"grandes navega[cç][oõ]es", r"marinheiro", r"imp[eé]rio",
                        r"idade m[eé]dia", r"\bguerra\b", r"\bchina\b", r"jap[aã]o", r"\bromano", r"egito",
                        r"segunda guerra", r"revolu[cç][aã]o", r"\bhistory\b"]),
    ("ciencia_geral", [r"f[ií]sica", r"qu[ií]mica", r"biologia", r"\bespa[cç]o\b", r"universo", r"experimento",
                       r"#fisica", r"ci[eê]ncia", r"\bnasa\b", r"buraco negro", r"astronomia", r"\bscience\b"]),
    ("tecnologia_hardware", [r"\bpc\b", r"placa de v[ií]deo", r"\bram\b", r"mem[oó]ria ram", r"monitor",
                             r"\bsetup\b", r"hardware", r"celular", r"smartphone", r"iphone", r"android",
                             r"gadget", r"processador", r"\bgpu\b", r"\bcpu\b", r"kabum", r"notebook"]),
    ("programacao_estudo", [r"python", r"c[oó]digo", r"programa[cç][aã]o", r"tutorial", r"\bcurso\b",
                            r"machine learning", r"javascript", r"\breact\b.*(js|native|hook)", r"\bsql\b",
                            r"\bjava\b", r"\bc\+\+", r"\bhtml\b", r"\bcss\b", r"node\.?js", r"\bgit\b",
                            r"\bapi\b", r"data science", r"pandas", r"\bdjango\b", r"\bflask\b"]),
    ("filmes_series", [r"trailer", r"\bfilme\b", r"\bfilmes\b", r"s[eé]rie", r"final explicado", r"netflix",
                       r"resenha", r"\bmovie\b", r"hbo", r"disney\+", r"marvel", r"\bdc\b", r"star wars"]),
    ("podcasts_entrevistas", [r"podcast", r"entrevista", r"\bcortes?\b", r"debate", r"bate-papo",
                              r"flow", r"inteligência ltda", r"\binterview\b"]),
    ("curiosidades_geral", [r"curiosidades", r"voc[eê] sabia", r"\bvs\b", r"compara[cç][aã]o",
                            r"como funciona", r"document[aá]rio", r"\bfatos\b", r"por que", r"porque"]),
    ("noticias_atualidades", [r"not[ií]cia", r"pol[ií]tica", r"economia", r"jornal", r"urgente",
                              r"\bg1\b", r"cnn", r"telejornal", r"elei[cç][aã]o", r"governo"]),
    ("vlogs_cotidiano", [r"\bvlog\b", r"rotina", r"dia a dia", r"receita", r"culin[aá]ria", r"\bdiy\b",
                         r"lifestyle", r"unboxing", r"\bcozinha\b", r"churrasco"]),
]

REGRAS_COMPILADAS = [(tema, re.compile("|".join(pads), re.IGNORECASE)) for tema, pads in REGRAS]


def classificar(titulo, canal):
    texto = f"{titulo or ''} {canal or ''}"
    for tema, padrao in REGRAS_COMPILADAS:
        if padrao.search(texto):
            return tema
    return "outros"


df = pd.read_csv(ENTRADA)
df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
df = df.sort_values("time_utc").reset_index(drop=True)

df["tema"] = [classificar(t, c) for t, c in zip(df["titulo"].fillna(""), df["canal"].fillna(""))]
df["tema_next_video"] = df["tema"].shift(-1)

df = df.dropna(subset=["tema_next_video"]).reset_index(drop=True)
df.to_csv(SAIDA, index=False, encoding="utf-8-sig")
print(f"Pronto: {SAIDA} ({len(df)} linhas)")