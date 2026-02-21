#!/usr/bin/env python3
"""
Scriptum API Server - Servidor Flask para metadados de filmes
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from metadata.movie_metadata_manager import MovieMetadataManager
import os

app = Flask(__name__)
CORS(app)  # Permitir CORS para desenvolvimento local

# Inicializar manager
manager = MovieMetadataManager()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Scriptum API',
        'version': '1.0.0'
    })

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """
    Busca metadados de um filme

    Query params:
        filename: Nome do ficheiro de legenda (ex: Inception.2010.en.srt)

    Returns:
        JSON com metadados completos do filme
    """
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'error': 'Parâmetro filename é obrigatório'}), 400

    try:
        result = manager.process_subtitle_file(filename)

        if not result or not result.get('metadata'):
            return jsonify({'error': 'Filme não encontrado'}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metadata/search', methods=['GET'])
def search_metadata():
    """
    Busca filme por título

    Query params:
        title: Título do filme
        year: Ano (opcional)

    Returns:
        JSON com metadados do filme
    """
    title = request.args.get('title')
    year = request.args.get('year', type=int)

    if not title:
        return jsonify({'error': 'Parâmetro title é obrigatório'}), 400

    try:
        metadata = manager.fetcher.get_movie_metadata(title, year)

        if not metadata:
            return jsonify({'error': 'Filme não encontrado'}), 404

        # Criar glossário
        glossary = manager.fetcher.create_character_glossary(metadata)

        # Criar contexto
        file_info = {'title': title, 'year': year}
        context = manager._create_translation_context(metadata, file_info)

        return jsonify({
            'metadata': metadata,
            'glossary': glossary,
            'context': context
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Scriptum API Server")
    print("📡 Server running on http://localhost:5000")
    print("📄 Health check: http://localhost:5000/api/health")
    print("🎬 Metadata: http://localhost:5000/api/metadata?filename=Inception.2010.en.srt")
    print("\n⌨️  Press CTRL+C to stop\n")

    app.run(debug=True, port=5000)
