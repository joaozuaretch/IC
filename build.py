#!/usr/bin/env python3
"""Gera o site da iniciação científica a partir das pastas deste repositório.

Uso:  python3 build.py   (o resultado vai para _site/)

As reuniões são lidas de Reuniões/**/*.md, no formato das notas do Obsidian.
Os PDFs citados nas notas com [[...]] viram links. Os textos fixos do site
(sobre, percurso, bibliografia, descrição dos arquivos) estão logo abaixo.
"""
import html
import re
import shutil
import subprocess
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "_site"

NOME = "João Vinícius Zuaretch"
LATTES = "https://lattes.cnpq.br/2268915045028482"
SITE_PESSOAL = "https://joaozuaretch.github.io/Site/"
ORIENTADOR = "Giuliano Gadioli La Guardia"
TITULO_PROJETO = "Grupos de Sylow e Extensões de Corpos"

# ---------------------------------------------------------------- textos fixos

SOBRE = [
    "Nesta página reúno tudo o que se relaciona à minha iniciação científica em Álgebra Abstrata na "
    "Universidade Estadual de Ponta Grossa (UEPG): o registro de cada reunião de orientação, as "
    "apresentações que preparei, notas de estudo, exercícios e a bibliografia.",
    "Comecei pelo básico da teoria de grupos e segui por homomorfismos, grupos cíclicos e o Teorema de "
    "Lagrange; depois vieram anéis, ideais, corpos de frações e anéis de polinômios, até chegar às "
    "extensões de corpos e aos Teoremas de Sylow.",
]

# (período, tema, detalhe) — a linha do tempo da página inicial
PERCURSO = [
    ("Fev 2026", "Grupos e homomorfismos", "Propriedades de grupos e subgrupos, homomorfismos e núcleo."),
    ("Mar 2026", "Teorema de Cayley", "Teorema de Cayley, múltiplos e potências em um grupo."),
    ("Abr 2026", "Grupos cíclicos", "Classificação dos grupos cíclicos em finitos e infinitos."),
    ("Mai 2026", "Teorema de Lagrange", "Classes laterais, Teorema de Lagrange, subgrupos normais e Teorema do Homomorfismo."),
    ("Jun 2026", "Anéis e corpos", "Definições e primeiras proposições, anéis de integridade e corpos."),
    ("Jul 2026", "Corpo de frações e ideais", "Corpo de frações, característica, ideais e anéis de polinômios."),
    ("Ago 2026", "Extensões de corpos", "Teorema de Kronecker e corpos de decomposição, seguindo Rotman."),
    ("Out 2026", "Teoremas de Sylow", "Os Teoremas de Sylow (Rotman, Advanced Modern Algebra, seção 5.2)."),
]

# Tema curto de cada reunião, usado nas listas. Reunião sem tema aqui usa a primeira frase da nota.
TEMAS = {
    "2026-02-03": "Correções das propriedades de grupos e subgrupos",
    "2026-02-26": "Homomorfismos de grupos e núcleo",
    "2026-03-05": "Teorema de Cayley (início)",
    "2026-03-19": "Teorema de Cayley, múltiplos e potências",
    "2026-04-10": "Grupos cíclicos",
    "2026-04-16": "Classificação dos grupos cíclicos",
    "2026-05-15": "Exposição de Joao Roseira sobre extensões de anéis",
    "2026-05-18": "Grupos cíclicos, relações de equivalência e classes laterais",
    "2026-05-21": "Teorema de Lagrange",
    "2026-05-28": "Subgrupos normais e Teorema do Homomorfismo",
    "2026-06-11": "Início do estudo de anéis",
    "2026-06-18": "Anéis e corpos",
    "2026-06-25": "Homomorfismos de anéis",
    "2026-07-06": "Corpo de frações, característica e ideais",
    "2026-07-27": "Anéis de polinômios e extensões de corpos",
    "2026-08-19": "Extensões de corpos e Teorema de Kronecker",
    "2026-08-27": "Teorema de Kronecker e corpos de decomposição",
}

# Arquivos publicados no site: nome do arquivo -> (título, descrição). A ordem é a de exibição.
APRESENTACOES = {
    "Grupos__Homomorfismo__Teorema_de_Lagrange.pdf": ("Grupos, Homomorfismo e Teorema de Lagrange", "Grupos e subgrupos, homomorfismos, Teorema de Cayley, grupos cíclicos, classes laterais e Teorema de Lagrange."),
    "Anéis e Corpos.pdf": ("Anéis e Corpos", "Capítulo 5 de Garcia e Lequain: definições, proposições e demonstrações."),
    "Corpo_de_Frações_de_um_Anel_de_Integridade.pdf": ("Corpo de Frações e Característica", "Corpo de frações de um anel de integridade e característica de anéis e corpos."),
    "Ideais_em_um_Anel_Comutativo.pdf": ("Ideais em Anéis Comutativos", "Ideais e ideal gerado, corpos como anéis sem ideais não triviais, interseção e soma de ideais, ideais primos e maximais."),
    "Anéis_Quocientes.pdf": ("Anéis Quocientes", "O anel quociente A/I de um anel comutativo por um ideal e o Teorema do Homomorfismo para anéis."),
    "Anéis_de_Polinômios.pdf": ("Anéis de Polinômios", "Polinômios como sequências de coeficientes, adição e multiplicação, grau e o anel R[x], seguindo Rotman."),
    "Extensões_de_Corpos.pdf": ("Extensões de Corpos", "Quociente de k[x] por um ideal principal, extensões de corpos, Teorema de Kronecker e corpos de decomposição, seguindo Rotman."),
    "Teoremas_de_Sylow.pdf": ("Os Teoremas de Sylow", "Subgrupos de Sylow e os três Teoremas de Sylow, com aplicações a grupos simples, grupos unitriangulares e grupos de ordem 2p. Rotman, Advanced Modern Algebra, seção 5.2."),
    "Grupos_Abelianos_Finitos.pdf": ("Grupos Abelianos Finitos", "Somas diretas, grupos abelianos livres, decomposição primária e subgrupos puros, até o Teorema da Base, seguindo Rotman."),
    "Teorema_de_Bezout.pdf": ("Teorema de Bézout", "O plano projetivo e o Teorema de Bézout sobre o número de pontos de interseção de duas curvas, com o Teorema do hexágono de Pascal."),
    "Inteiros_Gaussianos.pdf": ("Inteiros Gaussianos", "O anel ℤ[i]: norma, unidades, divisão euclidiana, ℤ[i] como domínio principal, primos gaussianos e o teorema de Fermat sobre somas de dois quadrados."),
}
# arquivo-fonte (LaTeX) publicado ao lado de uma apresentação
FONTES = {"Teoremas_de_Sylow.pdf": "Teoremas_de_Sylow.zip"}

NOTAS = {
    "Correções_1.pdf": ("Propriedades de um Grupo", "Demonstrações das propriedades de grupos e da proposição sobre subgrupos, com as correções da orientação. Dezembro de 2025."),
    "Exercícios_Álgebra.pdf": ("Exercícios de Álgebra", "Exercícios resolvidos do livro de Hygino Domingues. Janeiro de 2026."),
    "Exemplo_Homomorfismo.pdf": ("Exemplo: homomorfismo de grupos", "Um homomorfismo de (Z₃, +) em um grupo de rotações."),
    "Questão.pdf": ("Relações de equivalência a partir de subgrupos de (Z, +)", "Resposta à pergunta deixada na reunião de 18 de maio."),
    "2026-05-26-Nota-16-05.pdf": ("Nota de 26 de maio de 2026", "Anotações sobre classes laterais e subgrupos normais."),
    "Anéis.pdf": ("Anotações sobre Anéis", "Definição de anel e primeiras propriedades. Junho de 2026."),
    "Apresentaýýo_Banner_ENCPOS_2026.pdf": ("Inverse Limit and Completion", "Anotações de estudo sobre limite inverso, a partir de Lang, Algebra, cap. I, §10."),
}

TRABALHOS = {
    "Poster_ENCPOS___UFSC (1).pdf": ("Limite Inverso de Grupos", "Pôster apresentado no III EncPos MTM (UFSC), 2026. Com Joao Vitor Roseira e Giuliano Gadioli La Guardia."),
    "Apresentação_Teorema_Fundamental_da_Teoria_de_Galois.pdf": ("Teorema Fundamental da Teoria de Galois", "Apresentação no IX SIGMAT (UEPG), 2026, com Joao Roseira. Menção Honrosa."),
    "Uma_Introdução_à_Teoria_de_Galois___Minicurso.pdf": ("Uma Introdução à Teoria de Galois: material", "Texto do minicurso ministrado com Joao Roseira na UEPG, 2026."),
    "Introdução_à_Teoria_de_Galois___Slide.pdf": ("Uma Introdução à Teoria de Galois: slides", "Slides do minicurso, IX SIGMAT, 2026."),
}

# Livros não são publicados no site, só citados.
BIBLIOGRAFIA = [
    "DOMINGUES, H. H.; IEZZI, G. <em>Álgebra Moderna</em>.",
    "GARCIA, A.; LEQUAIN, Y. <em>Elementos de Álgebra</em>. Rio de Janeiro: IMPA (Projeto Euclides).",
    "GONÇALVES, A. <em>Introdução à Álgebra</em>. Rio de Janeiro: IMPA (Projeto Euclides).",
    "ROTMAN, J. J. <em>Advanced Modern Algebra</em>.",
    "ROTMAN, J. J. <em>A First Course in Abstract Algebra: with Applications</em>. Prentice Hall, 2006.",
    "ROTMAN, J. J. <em>Galois Theory</em>. 2. ed. Springer (Universitext).",
    "FRALEIGH, J. B. <em>A First Course in Abstract Algebra</em>.",
    "LANG, S. <em>Algebra</em>. Springer (Graduate Texts in Mathematics, 211).",
    "TENGAN, E. Notas de Teoria de Galois.",
    "<em>Álgebra Exemplar</em>.",
    "WASHINGTON, L. C. <em>Elliptic Curves: Number Theory and Cryptography</em>. 2. ed.",
    "<em>Curvas Elípticas e Criptografia</em>.",
    "<em>Group Theory and Quantum Mechanics</em>.",
    "<em>Introdução à Teoria dos Códigos Corretores de Erros</em>.",
]

# Ilustração da coluna lateral de cada página (site/ilustracoes/*.svg) e sua legenda. Só aparece em telas largas.
ILUSTRACOES = {
    "inicio": [
        ("torre-raizes.svg", "Uma torre de extensões quadráticas: cada passo dobra o grau, até [ℚ(√2, √3, √5) : ℚ] = 8."),
        ("galois.svg", "A correspondência de Galois para ℚ(√2, √3): cada subcorpo corresponde a um subgrupo de G = {1, σ, τ, στ}, com σ: √3 ↦ −√3 e τ: √2 ↦ −√2."),
    ],
    "reunioes": [
        ("classes.svg", "As classes laterais de 3ℤ em ℤ: três classes disjuntas, de mesmo tamanho, que cobrem todos os inteiros."),
        ("ciclico.svg", "O grupo cíclico de ordem 6 e seus subgrupos, um para cada divisor de 6."),
    ],
    "apresentacoes": [
        ("tabuas.svg", "Os dois grupos de ordem 4: o cíclico ℤ₄ e o de Klein ℤ₂ × ℤ₂."),
        ("sylow.svg", "Os subgrupos de S₃: três subgrupos de Sylow de ordem 2 e um único de ordem 3, que é normal."),
    ],
    "materiais": [
        ("torre-cubica.svg", "O corpo de decomposição de x³ − 2 sobre ℚ: um passo de grau 3 e outro de grau 2."),
        ("reticulado-cubico.svg", "Os subcorpos de ℚ(∛2, ω), na altura do seu grau sobre ℚ: três de grau 3 e um de grau 2."),
    ],
}

# ---------------------------------------------------------------- utilidades

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def data_extenso(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9.]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def esc(s):
    return html.escape(s, quote=True)


# Todos os arquivos que podem ser publicados, indexados pelo nome (como nos [[links]] do Obsidian).
PASTAS_PUBLICAS = ["Apresentações", "PDF's de conteúdo", "Reuniões"]
PUBLICADOS = set(APRESENTACOES) | set(NOTAS) | set(TRABALHOS) | set(FONTES.values())
ARQUIVOS = {}
for pasta in PASTAS_PUBLICAS:
    for p in sorted((RAIZ / pasta).rglob("*")):
        # anotações das reuniões (PDF) entram todas; nas outras pastas, só o que está nas tabelas acima
        if p.name in PUBLICADOS or (pasta == "Reuniões" and p.suffix.lower() == ".pdf"):
            ARQUIVOS[p.name] = p


def url_arquivo(nome, raiz):
    return f"{raiz}arquivos/{slug(nome)}"


def titulo_arquivo(nome):
    for tabela in (APRESENTACOES, NOTAS, TRABALHOS):
        if nome in tabela:
            return tabela[nome][0]
    return Path(nome).stem.replace("_", " ").strip()


# ---------------------------------------------------------------- reuniões

class Reuniao:
    def __init__(self, caminho):
        self.caminho = caminho
        self.id = re.search(r"\d{4}-\d{2}-\d{2}", caminho.stem).group(0)
        self.data = date.fromisoformat(self.id)
        texto = caminho.read_text(encoding="utf-8").replace("\r\n", "\n")
        partes = re.split(r"^\*+\s*Conte[úu]dos usados\s*:?.*$", texto, maxsplit=1, flags=re.M)
        self.corpo = partes[0].strip()
        self.usados = re.findall(r"\[\[([^\]]+)\]\]", partes[1]) if len(partes) > 1 else []
        self.usados = [u.strip() for u in self.usados]

    @property
    def tema(self):
        if self.id in TEMAS:
            return TEMAS[self.id]
        frase = re.split(r"(?<=[.!?])\s", re.sub(r"\s+", " ", self.corpo))[0]
        return frase if len(frase) < 140 else frase[:137].rsplit(" ", 1)[0] + "…"

    def url(self, raiz):
        return f"{raiz}reunioes/{self.id}.html"


REUNIOES = sorted((Reuniao(p) for p in (RAIZ / "Reuniões").rglob("*.md")), key=lambda r: r.data)


def link_wiki(alvo, raiz):
    alvo = alvo.strip()
    m = re.fullmatch(r"Reuni[ãa]o (\d{4}-\d{2}-\d{2})", alvo)
    if m:
        return f'<a href="{raiz}reunioes/{m.group(1)}.html">reunião de {esc(data_extenso(date.fromisoformat(m.group(1))))}</a>'
    if alvo in ARQUIVOS:
        return f'<a href="{url_arquivo(alvo, raiz)}" target="_blank" rel="noopener">{esc(titulo_arquivo(alvo))}</a>'
    return f'<span class="ref">{esc(Path(alvo).stem if alvo.lower().endswith(".pdf") else alvo)}</span>'


def inline(texto, raiz):
    """Converte a marcação de uma linha, sem mexer no que está entre $...$."""
    pedacos = re.split(r"(\$\$.+?\$\$|\$.+?\$)", texto)
    saida = []
    for i, p in enumerate(pedacos):
        if i % 2:
            saida.append(esc(p))
            continue
        links = []

        def guarda(m):
            links.append(link_wiki(m.group(1), raiz))
            return f"\0{len(links) - 1}\0"

        p = re.sub(r"!?\[\[([^\]]+)\]\]+", guarda, p)
        p = esc(p)
        p = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", p)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
        p = re.sub(r"\0(\d+)\0", lambda m: links[int(m.group(1))], p)
        saida.append(p)
    return "".join(saida)


def markdown(texto, raiz):
    blocos, lista, paragrafo = [], [], []

    def fecha():
        if paragrafo:
            blocos.append(f"<p>{inline(' '.join(paragrafo), raiz)}</p>")
            paragrafo.clear()
        if lista:
            blocos.append("<ul>" + "".join(f"<li>{inline(i, raiz)}</li>" for i in lista) + "</ul>")
            lista.clear()

    for linha in texto.split("\n"):
        bruta = linha
        linha = linha.strip()
        if not linha:
            fecha()
        elif m := re.fullmatch(r"!\[\[([^\]]+)\]\]", linha):
            fecha()
            nome = m.group(1)
            if nome in ARQUIVOS:
                blocos.append(f'<div class="docs"><a class="doc-link" href="{url_arquivo(nome, raiz)}" target="_blank" rel="noopener">{esc(titulo_arquivo(nome))} (PDF)</a></div>')
        elif m := re.fullmatch(r"#{1,6}\s*(.+)", linha):
            fecha()
            blocos.append(f"<h3>{inline(m.group(1).rstrip(' :'), raiz)}</h3>")
        elif m := re.fullmatch(r"[-*]\s+(.+)", linha):
            if paragrafo:
                fecha()
            lista.append(m.group(1))
        elif bruta.startswith("\t") or bruta.startswith(">"):
            fecha()
            blocos.append(f"<blockquote>{inline(linha.lstrip('> ').strip(chr(34) + ' '), raiz)}</blockquote>")
        else:
            if lista:
                fecha()
            paragrafo.append(linha)
    fecha()
    return "\n".join(blocos)


# ---------------------------------------------------------------- páginas

PAGINAS = [("index.html", "Início"), ("reunioes/index.html", "Reuniões"),
           ("apresentacoes.html", "Apresentações"), ("materiais.html", "Materiais")]

KATEX = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>"""


def pagina(caminho, titulo, conteudo, descricao, atual=None, matematica=False, ilustracao=None):
    raiz = "../" * caminho.count("/")
    atributo = ' aria-current="page"'
    nav = "".join(f'<li><a href="{raiz}{href}"{atributo if href == atual else ""}>{nome}</a></li>'
                  for href, nome in PAGINAS)
    esquerda = direita = ""
    if ilustracao:
        figuras = []
        for lado, (arquivo, legenda) in zip(("esq", "dir"), ILUSTRACOES[ilustracao]):
            svg = (RAIZ / "site" / "ilustracoes" / arquivo).read_text(encoding="utf-8").strip()
            figuras.append(f'<aside class="ilustra {lado}" aria-hidden="true"><figure>{svg}'
                           f'<figcaption>{esc(legenda)}</figcaption></figure></aside>')
        esquerda, direita = figuras
    titulo_completo = "Iniciação Científica — " + NOME if titulo is None else f"{titulo} — Iniciação Científica"
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo_completo)}</title>
<meta name="description" content="{esc(descricao)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="icon" href="{raiz}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{raiz}style.css">
{KATEX if matematica else ""}
</head>
<body>
<div class="pagina">
{esquerda}
<main>
  <ul class="nav">{nav}</ul>
{conteudo}
  <footer>Iniciação científica de <a href="{SITE_PESSOAL}">{NOME}</a> · <a href="{LATTES}" target="_blank" rel="noopener">Currículo Lattes</a></footer>
</main>
{direita}
</div>
</body>
</html>
"""
    destino = SAIDA / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(doc, encoding="utf-8")


def linha(quando, corpo, href=None, externo=False):
    bloco = f'<div class="row"><div class="when">{quando}</div><p class="what">{corpo}</p></div>'
    if href:
        alvo = ' target="_blank" rel="noopener"' if externo else ""
        return f'<a class="row-link" href="{href}"{alvo}>{bloco}</a>'
    return bloco


def linha_reuniao(r, raiz):
    return linha(f"{r.data.day:02d}/{r.data.month:02d}", f"<strong>{esc(r.tema)}</strong>", r.url(raiz))


def gera_inicio():
    ultimas = "\n".join(linha_reuniao(r, "") for r in reversed(REUNIOES[-3:]))
    percurso = "\n".join(linha(q, f"<strong>{esc(t)}</strong><small>{esc(d)}</small>") for q, t, d in reversed(PERCURSO))
    sobre = "\n".join(f"<p>{p}</p>" for p in SOBRE)
    conteudo = f"""
  <header>
    <h1>Iniciação Científica</h1>
    <p class="lead">{TITULO_PROJETO}. Bolsista CNPq (PIBIC), Universidade Estadual de Ponta Grossa (UEPG).</p>
    <p class="meta">{NOME} · Orientador: {ORIENTADOR}</p>
  </header>

  <section>
    <h2>Sobre</h2>
    {sobre}
  </section>

  <section>
    <h2>Percurso</h2>
    {percurso}
  </section>

  <section>
    <h2>Últimas reuniões</h2>
    {ultimas}
    <p><a href="reunioes/index.html">Todas as {len(REUNIOES)} reuniões →</a></p>
  </section>

  <section>
    <h2>Neste site</h2>
    {linha("Reuniões", "<strong>Registro das reuniões de orientação</strong><small>O que foi apresentado, as correções e o que ficou para a próxima.</small>", "reunioes/index.html")}
    {linha("Apresentações", f"<strong>Slides preparados para as reuniões</strong><small>{len(APRESENTACOES)} apresentações em PDF, na ordem de estudo.</small>", "apresentacoes.html")}
    {linha("Materiais", "<strong>Notas, exercícios, trabalhos e bibliografia</strong><small>Pôster, minicurso e apresentações em eventos.</small>", "materiais.html")}
  </section>
"""
    pagina("index.html", None, conteudo,
           f"Iniciação científica de {NOME} em Álgebra Abstrata na UEPG: reuniões, apresentações e materiais.",
           atual="index.html", ilustracao="inicio")


def gera_reunioes():
    blocos, mes = [], None
    for r in reversed(REUNIOES):
        if (r.data.year, r.data.month) != mes:
            mes = (r.data.year, r.data.month)
            blocos.append(f"<h2>{MESES[r.data.month - 1].capitalize()} de {r.data.year}</h2>")
        blocos.append(linha_reuniao(r, "../"))
    conteudo = f"""
  <h1>Reuniões</h1>
  <p class="lead">Registro das {len(REUNIOES)} reuniões de orientação com {ORIENTADOR}, da mais recente à mais antiga.</p>
  {"".join(blocos)}
"""
    pagina("reunioes/index.html", "Reuniões", conteudo, "Registro das reuniões de orientação da iniciação científica.",
           atual="reunioes/index.html", ilustracao="reunioes")

    for i, r in enumerate(REUNIOES):
        raiz = "../"
        lista_usados = ""
        if r.usados:
            itens = "".join(f"<li>{link_wiki(u, raiz)}</li>" for u in r.usados)
            lista_usados = f'<h2>Materiais usados</h2>\n  <ul class="toc">{itens}</ul>'
        ant = f'<a href="{REUNIOES[i - 1].id}.html">← {esc(data_extenso(REUNIOES[i - 1].data))}</a>' if i > 0 else "<span></span>"
        prox = f'<a href="{REUNIOES[i + 1].id}.html">{esc(data_extenso(REUNIOES[i + 1].data))} →</a>' if i + 1 < len(REUNIOES) else "<span></span>"
        conteudo = f"""
  <a class="back" href="index.html">← Todas as reuniões</a>
  <h1>Reunião de {esc(data_extenso(r.data))}</h1>
  <p class="meta">{esc(r.tema)}</p>
  <div class="note">
{markdown(r.corpo, raiz)}
  </div>
  {lista_usados}
  <nav class="pager">{ant}{prox}</nav>
"""
        pagina(f"reunioes/{r.id}.html", f"Reunião de {data_extenso(r.data)}", conteudo,
               f"Reunião de orientação de {data_extenso(r.data)}: {r.tema}.", matematica="$" in r.corpo, ilustracao="reunioes")


def reunioes_que_usam(nome):
    return [r for r in REUNIOES if nome in r.usados or f"[[{nome}]]" in r.corpo]


def capa(nome, raiz=""):
    """Gera a imagem da primeira página do PDF (precisa do pdftoppm, do poppler). Devolve a URL ou None."""
    if not shutil.which("pdftoppm") or not nome.lower().endswith(".pdf"):
        return None
    destino = SAIDA / "capas" / Path(slug(nome)).stem
    destino.parent.mkdir(exist_ok=True)
    try:
        subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=82", "-f", "1", "-l", "1", "-scale-to", "480",
                        "-singlefile", str(ARQUIVOS[nome]), str(destino)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        return None
    return f"{raiz}capas/{destino.name}.jpg"


def linha_arquivo(nome, titulo, descricao, raiz="", com_capa=False):
    if nome not in ARQUIVOS:
        return ""
    usos = reunioes_que_usam(nome)
    extra = ""
    if usos:
        datas = ", ".join(f'{r.data.day:02d}/{r.data.month:02d}' for r in usos)
        extra = f'<span class="tags">{"Reuniões" if len(usos) > 1 else "Reunião"}: {datas}</span>'
    fonte = ""
    if nome in FONTES and FONTES[nome] in ARQUIVOS:
        fonte = f' · <a href="{url_arquivo(FONTES[nome], raiz)}">código-fonte LaTeX</a>'
    desc = f"<small>{esc(descricao)}{fonte}</small>" if descricao or fonte else ""
    corpo = f'<a href="{url_arquivo(nome, raiz)}" target="_blank" rel="noopener"><strong>{esc(titulo)}</strong></a>{desc}{extra}'
    imagem = capa(nome, raiz) if com_capa else None
    if not imagem:
        return linha("PDF", corpo)
    return (f'<div class="card"><a class="capa" href="{url_arquivo(nome, raiz)}" target="_blank" rel="noopener" tabindex="-1">'
            f'<img src="{imagem}" alt="Capa de {esc(titulo)}" loading="lazy"></a><p class="what">{corpo}</p></div>')


def gera_apresentacoes():
    linhas = "\n".join(linha_arquivo(n, t, d, com_capa=True) for n, (t, d) in APRESENTACOES.items())
    conteudo = f"""
  <h1>Apresentações</h1>
  <p class="lead">Slides que preparei para apresentar nas reuniões, na ordem em que os conteúdos foram estudados.</p>
  {linhas}
"""
    pagina("apresentacoes.html", "Apresentações", conteudo, "Slides das apresentações da iniciação científica.",
           atual="apresentacoes.html", ilustracao="apresentacoes")


def gera_materiais():
    notas = "\n".join(linha_arquivo(n, t, d) for n, (t, d) in NOTAS.items())
    trabalhos = "\n".join(linha_arquivo(n, t, d, com_capa=True) for n, (t, d) in TRABALHOS.items())
    biblio = "\n".join(f"<li>{b}</li>" for b in BIBLIOGRAFIA)
    conteudo = f"""
  <h1>Materiais</h1>
  <p class="lead">Notas de estudo, exercícios, trabalhos apresentados em eventos e a bibliografia usada.</p>

  <h2>Trabalhos e eventos</h2>
  {trabalhos}

  <h2>Notas e exercícios</h2>
  {notas}

  <h2>Bibliografia</h2>
  <ul class="toc">{biblio}</ul>
"""
    pagina("materiais.html", "Materiais", conteudo, "Notas, exercícios, trabalhos e bibliografia da iniciação científica.",
           atual="materiais.html", ilustracao="materiais")


def main():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    for nome in ("style.css", "favicon.svg"):
        shutil.copy(RAIZ / "site" / nome, SAIDA / nome)
    (SAIDA / ".nojekyll").touch()
    (SAIDA / "arquivos").mkdir()
    for nome, caminho in ARQUIVOS.items():
        shutil.copy(caminho, SAIDA / "arquivos" / slug(nome))
    gera_inicio()
    gera_reunioes()
    gera_apresentacoes()
    gera_materiais()
    print(f"{len(REUNIOES)} reuniões, {len(ARQUIVOS)} arquivos -> {SAIDA}")


if __name__ == "__main__":
    main()
