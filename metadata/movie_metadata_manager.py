#!/usr/bin/env python3
"""
Movie Metadata Manager - Sistema completo de metadados de filmes
Integra detecção de filme + busca TMDB + glossário de personagens
"""

import sys
import os

# Adicionar diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tmdb_fetcher import TMDBFetcher
from movie_detector import MovieDetector
from typing import Dict, Optional
import json


class MovieMetadataManager:
    """Gerenciador completo de metadados de filmes"""

    def __init__(self, tmdb_api_key: Optional[str] = None):
        """
        Inicializa o gerenciador

        Args:
            tmdb_api_key: Chave da API TMDB (opcional)
        """
        self.detector = MovieDetector()
        self.fetcher = TMDBFetcher(tmdb_api_key)
        self.cache = {}

    def process_subtitle_file(self, filename: str) -> Dict:
        """
        Processa ficheiro de legenda e retorna todos os metadados

        Args:
            filename: Nome do ficheiro de legenda

        Returns:
            Dicionário completo com:
            - file_info: Informações extraídas do filename
            - metadata: Metadados do TMDB
            - glossary: Glossário de personagens
            - context: Contexto para tradução
        """
        print(f"\n🎬 Processando: {filename}")
        print("=" * 60)

        # 1. Detectar filme do filename
        file_info = self.detector.detect_from_filename(filename)
        print(f"\n📄 Informações do Ficheiro:")
        print(f"   Título: {file_info['title']}")
        if file_info['year']:
            print(f"   Ano: {file_info['year']}")
        if file_info['is_series']:
            print(f"   Série: S{file_info['season']:02d}E{file_info['episode']:02d}")

        # 2. Buscar metadados no TMDB
        print(f"\n🔍 Buscando no TMDB...")
        metadata = self.fetcher.get_movie_metadata(
            file_info['title'],
            file_info['year']
        )

        if not metadata:
            print("   ⚠️  Metadados não encontrados")
            return {
                'file_info': file_info,
                'metadata': None,
                'glossary': {},
                'context': self._create_basic_context(file_info)
            }

        print(f"   ✅ {metadata['title']} ({metadata['year']})")
        print(f"   ⭐ Rating: {metadata['rating']}/10")
        if metadata['genres']:
            print(f"   🎭 Géneros: {', '.join(metadata['genres'])}")

        # 3. Criar glossário de personagens
        print(f"\n📝 Criando Glossário de Personagens...")
        glossary = self.fetcher.create_character_glossary(metadata)

        if glossary:
            print(f"   ✅ {len(glossary)} termos no glossário")
            # Mostrar exemplos
            examples = list(glossary.items())[:5]
            for term, value in examples:
                print(f"      • {term} → {value}")
            if len(glossary) > 5:
                print(f"      ... e mais {len(glossary) - 5} termos")
        else:
            print("   ⚠️  Sem personagens disponíveis")

        # 4. Criar contexto para tradução
        context = self._create_translation_context(metadata, file_info)

        # 5. Compilar resultado
        result = {
            'file_info': file_info,
            'metadata': metadata,
            'glossary': glossary,
            'context': context,
            'summary': self._create_summary(metadata, glossary)
        }

        print(f"\n✅ Processamento concluído!")
        print(f"   Glossário: {len(glossary)} termos")
        print(f"   Contexto: {context[:100]}...")

        return result

    def _create_translation_context(self, metadata: Dict, file_info: Dict) -> str:
        """
        Cria contexto textual para ajudar a tradução

        Args:
            metadata: Metadados do filme
            file_info: Informações do ficheiro

        Returns:
            String de contexto
        """
        context_parts = []

        # Título e ano
        context_parts.append(f"Filme: {metadata['title']} ({metadata['year']})")

        # Géneros
        if metadata['genres']:
            genres_str = ', '.join(metadata['genres'])
            context_parts.append(f"Géneros: {genres_str}")

        # Sinopse resumida
        if metadata['overview']:
            synopsis = metadata['overview'][:150] + '...' if len(metadata['overview']) > 150 else metadata['overview']
            context_parts.append(f"Sinopse: {synopsis}")

        # Personagens principais
        if metadata['cast']:
            characters = [p['character'] for p in metadata['cast'][:3] if p['character']]
            if characters:
                context_parts.append(f"Personagens principais: {', '.join(characters)}")

        return ". ".join(context_parts)

    def _create_basic_context(self, file_info: Dict) -> str:
        """Cria contexto básico quando não há metadados"""
        return f"Título: {file_info['title']}"

    def _create_summary(self, metadata: Dict, glossary: Dict) -> str:
        """Cria resumo legível"""
        summary = f"📽️  {metadata['title']} ({metadata['year']})\n"
        summary += f"⭐ {metadata['rating']}/10\n"

        if metadata['genres']:
            summary += f"🎭 {', '.join(metadata['genres'])}\n"

        if metadata['cast']:
            summary += f"\n👥 Elenco Principal:\n"
            for person in metadata['cast'][:5]:
                summary += f"   • {person['character']} ({person['name']})\n"

        summary += f"\n📝 Glossário: {len(glossary)} termos preservados"

        return summary

    def save_metadata_to_file(self, result: Dict, output_file: str):
        """
        Salva metadados em ficheiro JSON

        Args:
            result: Resultado do process_subtitle_file
            output_file: Caminho do ficheiro de saída
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Metadados salvos em: {output_file}")


def main():
    """Teste do sistema completo"""
    import sys

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Testes padrão
        test_files = [
            "Inception.2010.1080p.en.srt",
            "Zootopia.2016.pt-pt.srt",
            "Orwell_en.srt"
        ]
        filename = test_files[0]

    manager = MovieMetadataManager()
    result = manager.process_subtitle_file(filename)

    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    print(result['summary'])

    # Salvar em JSON
    output_file = filename.replace('.srt', '_metadata.json')
    manager.save_metadata_to_file(result, output_file)


if __name__ == '__main__':
    main()
