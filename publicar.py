#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para publicar rapidamente um novo PDF (ou compilar um .tex)
no portfólio GitHub Pages (index.html) e enviar via Git.

Uso básico:
    python publicar.py caminho/do/arquivo.pdf "Título do Material"

Uso completo (opcional):
    python publicar.py caminho/do/arquivo.pdf "Título" "ensino" "Ensino Médio • Geometria" "Resumo do material" "a² + b² = c²"
"""

import re
import sys
import time
import shutil
import subprocess
import unicodedata
from pathlib import Path

CATEGORIAS_VALIDAS = {
    "ensino": "Educação Básica (EF & EM)",
    "ensino universitario": "Monitoria & Ensino Superior (UnB)",
    "pesquisa": "Pesquisa & PIBIC (CNPq)",
    "codigo": "Diagramação LaTeX & Python",
}

def limpar_nome_arquivo(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    limpo = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
    return f"{limpo}.pdf"

def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print('  python publicar.py <arquivo.pdf|arquivo.tex> "Título do Material" [categoria] [subtitulo] [descricao] [formula]')
        print("\nCategorias aceitas no filtro do site:")
        print('  - "ensino" (padrão)')
        print('  - "ensino universitario"')
        print('  - "pesquisa"')
        print('  - "codigo"')
        sys.exit(1)

    caminho_origem = Path(sys.argv[1]).expanduser().resolve()
    if not caminho_origem.exists():
        print(f"Erro: Arquivo não encontrado: {caminho_origem}")
        sys.exit(1)

    titulo = sys.argv[2]
    categoria = sys.argv[3].lower().strip() if len(sys.argv) > 3 else "ensino"
    if categoria not in CATEGORIAS_VALIDAS:
        print(f"Aviso: Categoria '{categoria}' não reconhecida. Usando 'ensino'.")
        categoria = "ensino"

    subtitulo = sys.argv[4] if len(sys.argv) > 4 else CATEGORIAS_VALIDAS[categoria]
    descricao = (
        sys.argv[5]
        if len(sys.argv) > 5
        else f"Material didático e lista de exercícios: {titulo}."
    )
    formula = sys.argv[6] if len(sys.argv) > 6 else "Material Didático • PDF Diagramado em LaTeX"

    # Se o arquivo passado for .tex, compila automaticamente com pdflatex
    if caminho_origem.suffix.lower() == ".tex":
        print(f"Compilando {caminho_origem.name} com pdflatex...")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", caminho_origem.name],
            cwd=caminho_origem.parent,
            check=True,
        )
        caminho_pdf = caminho_origem.with_suffix(".pdf")
    else:
        caminho_pdf = caminho_origem

    nome_pdf_final = limpar_nome_arquivo(titulo)
    destino_pdf = Path.cwd() / nome_pdf_final

    # 1. Copia o PDF com nome limpo para a raiz do repositório
    shutil.copy2(caminho_pdf, destino_pdf)
    print(f"✓ PDF copiado como: {nome_pdf_final}")

    # 2. Atualiza o index.html no marcador // [NOVO_MATERIAL]
    html_path = Path.cwd() / "index.html"
    if not html_path.exists():
        print("Erro: index.html não encontrado no diretório atual.")
        sys.exit(1)

    conteudo = html_path.read_text(encoding="utf-8")
    marcador = "// [NOVO_MATERIAL]"
    if marcador not in conteudo:
        print(f"Erro: Marcador '{marcador}' não encontrado no index.html.")
        sys.exit(1)

    novo_id = int(time.time())
    snippet_padrao = (
        f"% {titulo}\n"
        "\\documentclass[12pt,a4paper]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[brazil]{babel}\n"
        "\\usepackage{amsmath,amssymb,amsthm}\n"
        f"\\title{{{titulo}}}\n"
        "\\author{Arthur Amorim}"
    )

    novo_bloco = f"""// [NOVO_MATERIAL]
            {{
                id: {novo_id},
                title: "{titulo}",
                category: "{categoria}",
                categoryLabel: "{subtitulo}",
                iconType: "pdf-red",
                meta: "PDF • Material Didático (LaTeX)",
                fileUrl: "{nome_pdf_final}",
                description: "{descricao}",
                formula: "{formula}",
                snippet: `{snippet_padrao}`
            }},"""

    conteudo_atualizado = conteudo.replace(marcador, novo_bloco, 1)
    html_path.write_text(conteudo_atualizado, encoding="utf-8")
    print("✓ Card adicionado ao index.html")

    # 3. Git add, commit e push
    try:
        subprocess.run(["git", "add", nome_pdf_final, "index.html"], check=True)
        subprocess.run(["git", "commit", "-m", f"Adiciona PDF: {titulo}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✓ Alterações enviadas para o GitHub Pages com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Aviso: O arquivo index.html foi atualizado, mas o comando Git falhou ({e}).")

if __name__ == "__main__":
    main()
