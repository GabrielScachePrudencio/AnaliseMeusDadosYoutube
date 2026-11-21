import re
import pandas as pd
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ENTRADA = "historico_completo.csv"
SAIDA = "historico_completo_com_target.csv"
LIMITE_SESSAO_S = 30 * 60  # intervalo maior que isso = o próximo vídeo não conta

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
                        r"basquete", r"\btreino\b", r"muscula[cç][aã]o", r"\bboxe\b", r"\bnfl\b", r"t[eê]nis"]),
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
                        r"resenha", r"\bmovie\b", r"\bhbo\b", r"disney\+", r"marvel", r"\bdc\b", r"star wars"]),
        ("podcasts_entrevistas", [r"podcast", r"entrevista", r"\bcortes?\b", r"debate", r"bate-papo",
                                r"\bflow\b", r"intelig[eê]ncia ltda", r"\binterview\b"]),
        ("curiosidades_geral", [r"curiosidades", r"voc[eê] sabia", r"\bvs\b", r"compara[cç][aã]o",
                                r"como funciona", r"document[aá]rio", r"\bfatos\b", r"por que", r"porque"]),
        ("noticias_atualidades", [r"not[ií]cia", r"pol[ií]tica", r"economia", r"jornal", r"urgente",
                                r"\bg1\b", r"\bcnn\b", r"telejornal", r"elei[cç][aã]o", r"governo"]),
        ("vlogs_cotidiano", [r"\bvlog\b", r"rotina", r"dia a dia", r"receita", r"culin[aá]ria", r"\bdiy\b",
                            r"lifestyle", r"unboxing", r"\bcozinha\b", r"churrasco"]),
    ]

REGRAS_COMPILADAS = [(tema, re.compile("|".join(pads), re.IGNORECASE)) for tema, pads in REGRAS]

import unicodedata

# Palavras-chave e canais novos, somados às regras existentes
EXTRAS = {
    "anime_musica": [r"anirap", r"shiny_sz", r"\bamv\b", r"\bmv\b", r"kimi no na wa", r"just a dream",
                     r"contrato fechado", r"feiticeiro imortal", r"d\.headz", r"shigatsu", r"chopin", r"\betude\b"],
    "anime_geral": [r"jumentossauro", r"psicologia dos animes", r"otagust", r"kimetsu", r"tokyo ghoul", r"kaneki",
                    r"chainsaw man", r"haikyuu", r"summer time render", r"doki doki", r"hakari", r"gyokko",
                    r"\bshigatsu\b", r"\bsimpsons\b.*\banime\b", r"nerdcf", r"dunerd", r"baymax"],
    "musica_instrumental": [r"chopin", r"\betude\b", r"sonata", r"\bop\.\s?\d+"],
    "musica_geral": [r"davie504", r"\bmv\b", r"\bbass\b", r"talent"],
    "futebol_geral": [r"desimpedidos", r"fut soeiro", r"davy jones", r"vini ?jr", r"copadomundo", r"bruno henrique",
                      r"melhores times", r"torcedor", r"\bflu\b"],
    "esportes_geral": [r"sinuca", r"billiards", r"xadrez", r"pedaleria", r"\bbike\b", r"jiu", r"\bninja\b"],
    "gameplay_geral": [r"leagueoflegends", r"wildrift", r"wild rift", r"\bpbe\b", r"faker", r"\bt1\b", r"worlds",
                       r"mundial da zueira", r"bronziocre", r"ismalakoi", r"quarto plano", r"sev7n", r"skins?",
                       r"sylas", r"yuumi", r"ekko", r"valheim", r"dark souls", r"black ops", r"pixelmon",
                       r"pok[eé]mon", r"free ?fire", r"freefire", r"minecart", r"capcom", r"silksong",
                       r"metaphor", r"cronosfera", r"gamer pra sempre", r"pixelisoturi", r"charlez bronson",
                       r"\b2v2\b", r"morteiro", r"lktpb", r"lkpb", r"daniel marcon", r"linkzin", r"digital circus",
                       r"microtransa", r"pompano", r"matheusu", r"abias ff", r"vuko clips", r"levil devil"],
    "humor_memes": [r"felipe neto", r"zueira", r"maicon k", r"utopia", r"queimando de raiva", r"\bbe like\b",
                    r"andrezitos", r"t3ddy", r"revira e voltha", r"eu sou barone", r"feigo", r"tinocando"],
    "exploracao_aventura": [r"mundo indescoberto", r"cariocas na estrada", r"\bpraia\b", r"turismo", r"\bmenor pa[ií]s\b"],
    "historia_geral": [r"nerd militar", r"na linha de contato", r"super tucano", r"navios?", r"submarino",
                       r"canal nostalgia", r"\bdoc\b", r"hawking"],
    "ciencia_geral": [r"manual do mundo", r"gabriel inventor", r"alex circuitos", r"mosfet", r"eletr[oô]nica",
                      r"motor el[eé]trico", r"engenharia", r"lucax franco", r"matem[aá]tic", r"equaciona",
                      r"fossa das marianas", r"mosquitos?", r"desat[oô]mico"],
    "tecnologia_hardware": [r"photoshop", r"filmora", r"chroma key", r"ducthang", r"mockup"],
    "programacao_estudo": [r"lucas montano", r"programador", r"code review", r"howdy", r"engenharia de software",
                           r"univesp", r"aula \d+"],
    "podcasts_entrevistas": [r"geralpodcuts", r"podcuts", r"\bcuts\b", r"briggs"],
    "curiosidades_geral": [r"investiga, pinhel", r"mundo indescoberto", r"teste", r"voc[eê] tem", r"dentista",
                           r"polici", r"corrup[cç][aã]o", r"\bcirurgia\b"],
    "noticias_atualidades": [r"indiciado", r"apostas"],
    "vlogs_cotidiano": [r"sushi", r"temaki", r"piscina", r"limpeza", r"satisf", r"\bdicas?\b", r"liquidificador",
                        r"\buber\b", r"\bchinelo\b", r"andressa fontinele", r"rhuan f[eé]lix", r"max eagle", r"minecine",
                        r"zelo canal", r"pneus?", r"postura", r"zeka ramos", r"sejanatural", r"\basmr\b"],
}

# Temas novos
NOVOS = [
    ("educacao_estudos", [r"brasil escola", r"univesp", r"profinho", r"\benem\b", r"vestibular", r"\baula\b",
                          r"reda[cç][aã]o", r"resumo", r"coreano online", r"idioma", r"ingl[eê]s", r"estudar"]),
    ("animais_natureza", [r"animais?", r"cobras?", r"bi[oó]logo", r"wild boppr", r"coiote", r"texugo", r"toninhas?",
                          r"\btatu\b", r"\bgato\b", r"\bcachorro\b", r"natureza", r"selvagem"]),
   ("asmr", [r"\basmr\b", r"ear licking", r"ear eating", r"ear cleaning", r"ear massage", r"ear brushing"]),
]

for i, (tema, pads) in enumerate(REGRAS):
    REGRAS[i] = (tema, pads + EXTRAS.get(tema, []))
# novos temas ficam no fim (menor prioridade)
REGRAS.extend(NOVOS)

REGRAS_COMPILADAS = [(tema, re.compile("|".join(pads), re.IGNORECASE)) for tema, pads in REGRAS]



CANAL_TEMA = {
    "CheffOtto": "vlogs_cotidiano",
    "Gudan, o Husky": "animais_natureza",
    "Top Pet Pet Shop": "animais_natureza",
    "MrBeast": "curiosidades_geral",
    "Cadê a chave?": "humor_memes",
    "Senhor Reddit": "humor_memes",
    "Lives do alanzoka": "gameplay_geral",
    "Pensando RPG": "gameplay_geral",
    "TOHO animation チャンネル": "anime_geral",
    "アニプレックス チャンネル": "anime_geral",
    "ANIMONK": "anime_geral",
    "Shooter_sz": "anime_musica",
    "Rafael Pedreiro 👷": "vlogs_cotidiano",
    "Bounty Breaker": "vlogs_cotidiano",
    "Red Bull": "esportes_geral",
    "CazéTV": "futebol_geral",
    "Mark Rober": "ciencia_geral",
    "Aero Por Trás da Aviação": "ciencia_geral",
    "NicK Psicologia": "ciencia_geral",
    "Krusty Recaps": "filmes_series",
    "GL Art": "vlogs_cotidiano",
}
CANAL_TEMA = {k.strip().lower(): v for k, v in CANAL_TEMA.items()}

CANAL_TEMA.update({
    # anime / música de anime
    "Miura Jam": "anime_musica", "7 Minutoz": "anime_musica", "M4rkim": "anime_musica",
    "Apolo🦅": "anime_musica", "Enygma": "anime_musica", "VMZ": "anime_musica", "Shoto": "anime_musica",
    "Cenário Transparente": "anime_geral", "TempoNerd": "anime_geral", "Tsuki Aru": "anime_geral",
    "Gabi Xavier": "anime_geral", "Inferno de Dante": "anime_geral",
    # futebol / esportes
    "Michael bnk": "futebol_geral", "João Sanque": "futebol_geral", "Sem Zika": "futebol_geral",
    "David Seybering": "esportes_geral",
    # games
    "Yoda SL": "gameplay_geral", "Canal do King": "gameplay_geral", "DonJone": "gameplay_geral",
    "Lukskk": "gameplay_geral", "Pijack": "gameplay_geral", "Vinizxnn": "gameplay_geral",
    # humor
    "O Canal do Pcini": "humor_memes", "JJ": "humor_memes", "orochidois": "humor_memes",
    "卓キチちゃんねる": "humor_memes", "Leo Otaco": "humor_memes", "Fhany": "humor_memes",
    "Goularte2": "humor_memes", "Tutuba Tron": "humor_memes", "MEDRADO SHORTS": "humor_memes",
    "Jogando a Vida Fora": "humor_memes", "Diggo": "humor_memes", "Elegas": "humor_memes",
    "Giuliana Mafra": "humor_memes",
    # filmes / séries
    "Rupert TV": "filmes_series", "Canal PeeWee": "filmes_series", "Gaveta": "filmes_series",
    "Rhonin Studio": "filmes_series",
    # curiosidades
    "República Coisa de Nerd": "curiosidades_geral", "Paulo Jubilut": "curiosidades_geral",
    "Léo Crunfli": "curiosidades_geral", "Canal do Ramsés": "curiosidades_geral",
    "Arttur": "curiosidades_geral", "Artioli": "curiosidades_geral",
    "Daniel Oliver": "curiosidades_geral", "Túlio Parreiras": "curiosidades_geral",
    "Micael Melo": "curiosidades_geral", "Victor Han Shorts": "curiosidades_geral",
    "MotionMe": "curiosidades_geral",
    # ciência / saúde
    "Dr. Magno": "ciencia_geral", "QueroQuiro": "ciencia_geral",
    # animais
    "Yago Stephano": "animais_natureza",
    # notícias
    "Elementar": "noticias_atualidades",
    # vlogs / cotidiano
    "Braian Rizzo": "vlogs_cotidiano", "Experiência Flamino": "vlogs_cotidiano",
    "Sau Sampaio": "vlogs_cotidiano", "MeChamoJojo": "vlogs_cotidiano",
    "Instrutor Thiago": "vlogs_cotidiano",
})
# NFKC também nas chaves, para casar com nomes que têm emoji ou caracteres japoneses
CANAL_TEMA = {unicodedata.normalize("NFKC", k).strip().lower(): v for k, v in CANAL_TEMA.items()}

def classificar(titulo, canal):
    canal_norm = unicodedata.normalize("NFKC", canal).strip().lower()
    if canal_norm in CANAL_TEMA:
        return CANAL_TEMA[canal_norm]
    texto = unicodedata.normalize("NFKC", f"{titulo} {canal}")
    for tema, padrao in REGRAS_COMPILADAS:
        if padrao.search(texto):
            return tema
    return "outros"

df = pd.read_csv(ENTRADA)
df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
df = df.sort_values("time_utc").reset_index(drop=True)
df.insert(0, "ordem", range(1, len(df) + 1))  # mesma ordem do sequencia.csv

# Tema do vídeo atual
df["tema"] = [classificar(t, c) for t, c in zip(df["titulo"].fillna(""), df["canal"].fillna(""))]

# Target: tema do próximo vídeo, só se ele veio na mesma sessão (intervalo <= 30 min)
df["tema_next_video"] = df["tema"].shift(-1)
intervalo = df["time_utc"].shift(-1) - df["time_utc"]
mesma_sessao = intervalo.dt.total_seconds() <= LIMITE_SESSAO_S
df.loc[~mesma_sessao, "tema_next_video"] = None

df = df.dropna(subset=["tema_next_video"]).reset_index(drop=True)
df["time_utc"] = df["time_utc"].astype(str)
df.to_csv(SAIDA, index=False, encoding="utf-8-sig")

print(f"Pronto: {SAIDA} ({len(df)} linhas, {df.shape[1]} colunas)")
print(f"Vídeos em 'outros': {(df['tema'] == 'outros').mean():.1%}")



print("=== Distribuição do tema_next_video (target) ===")
print(df["tema_next_video"].value_counts().to_string())

print("\n=== 5 exemplos por tema ===")
for tema, grupo in df.groupby("tema"):
    print(f"\n## {tema}")
    for _, r in grupo.sample(min(5, len(grupo)), random_state=1).iterrows():
        print(f"   - {r['titulo']}  |  {r['canal']}")