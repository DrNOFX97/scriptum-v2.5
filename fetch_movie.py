#!/usr/bin/env python3
"""
Script para buscar metadados de um filme e gerar JSON
Uso: python3 fetch_movie.py "Inception.2010.en.srt"
"""

import sys
import json
from metadata.movie_metadata_manager import MovieMetadataManager

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 fetch_movie.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    # Inicializar manager
    manager = MovieMetadataManager()

    # Buscar metadados
    result = manager.process_subtitle_file(filename)

    # Imprimir JSON
    if result and result.get('metadata'):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Filme não encontrado"}))
        sys.exit(1)

if __name__ == '__main__':
    main()
