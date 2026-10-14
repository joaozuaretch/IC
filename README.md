# Iniciação Científica

Tudo sobre a minha iniciação científica em Álgebra Abstrata (UEPG): reuniões, apresentações, notas e bibliografia.
O site é gerado a partir destas pastas e publicado no GitHub Pages a cada push na `main`.

- `Reuniões/` — uma nota `.md` por reunião (formato do Obsidian, com `[[links]]` e fórmulas em `$...$`).
- `Apresentações/`, `PDF's de conteúdo/` — PDFs que aparecem no site.
- `conteudo.json` — temas das reuniões e título/descrição de cada apresentação, nota e trabalho (a ordem é a de exibição).
- `build.py` — gera o site em `_site/`; o percurso e a bibliografia ficam no topo dele.
- `adicionar.html` (no site) — formulário para adicionar reuniões e PDFs pelo navegador. Grava direto na `main` com um token do GitHub guardado no navegador, cifrado com uma senha.
- `site/` — estilo, ícone e as ilustrações (SVG) da coluna lateral.
- As capas das apresentações são geradas da primeira página de cada PDF (precisa do `pdftoppm`, do poppler).

Para ver localmente: `python3 build.py && python3 -m http.server -d _site`.

Os livros de `Livros-Artigos/` não são publicados no site, só citados na bibliografia.
