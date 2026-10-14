# Iniciação Científica

Tudo sobre a minha iniciação científica em Álgebra Abstrata (UEPG): reuniões, apresentações, notas e bibliografia.
O site é gerado a partir destas pastas e publicado no GitHub Pages a cada push na `main`.

- `Reuniões/` — uma nota `.md` por reunião (formato do Obsidian, com `[[links]]` e fórmulas em `$...$`).
- `Apresentações/`, `PDF's de conteúdo/` — PDFs que aparecem no site.
- `build.py` — gera o site em `_site/`; os textos fixos (percurso, temas das reuniões, descrição dos PDFs, bibliografia) ficam no topo dele.
- `site/` — estilo e ícone.

Para ver localmente: `python3 build.py && python3 -m http.server -d _site`.

Os livros de `Livros-Artigos/` não são publicados no site, só citados na bibliografia.
