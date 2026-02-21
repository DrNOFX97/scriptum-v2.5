#!/usr/bin/env python3
"""
Scriptum API Server - Servidor HTTP simples para metadados de filmes
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import tempfile
import os
import email
from urllib.parse import urlparse, parse_qs
from metadata.movie_metadata_manager import MovieMetadataManager
from mkv.subtitle_extractor import MKVSubtitleExtractor
import sys

# Inicializar managers
print("🔧 Inicializando MovieMetadataManager...")
try:
    manager = MovieMetadataManager()
    print("✅ Manager inicializado com sucesso")
except Exception as e:
    print(f"❌ Erro ao inicializar manager: {e}")
    sys.exit(1)

print("🔧 Inicializando MKVSubtitleExtractor...")
try:
    mkv_extractor = MKVSubtitleExtractor()
    print("✅ MKV Extractor inicializado com sucesso")
except Exception as e:
    print(f"❌ Erro ao inicializar MKV extractor: {e}")
    sys.exit(1)

class ScriptumAPIHandler(BaseHTTPRequestHandler):
    """Handler para API de metadados"""

    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            if parsed.path == '/api/health':
                self.handle_health()
            elif parsed.path == '/api/metadata':
                self.handle_metadata(params)
            elif parsed.path == '/api/file':
                self.handle_file_serve(params)
            else:
                self.send_error(404, 'Endpoint not found')
        except Exception as e:
            print(f"❌ Erro no do_GET: {e}")
            self.send_error(500, str(e))

    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed = urlparse(self.path)

            if parsed.path == '/api/mkv/analyze':
                self.handle_mkv_analyze()
            elif parsed.path == '/api/mkv/extract':
                self.handle_mkv_extract()
            else:
                self.send_error(404, 'Endpoint not found')
        except Exception as e:
            print(f"❌ Erro no do_POST: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_health(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = {
            'status': 'ok',
            'service': 'Scriptum API',
            'version': '1.0.0'
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_metadata(self, params):
        """Metadata endpoint"""
        try:
            if 'filename' not in params:
                self.send_error(400, 'Parameter filename is required')
                return

            filename = params['filename'][0]
            print(f"📡 Buscando metadados para: {filename}")

            result = manager.process_subtitle_file(filename)

            if not result or not result.get('metadata'):
                self.send_error(404, 'Movie not found')
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            print(f"✅ Metadados enviados com sucesso")

        except Exception as e:
            print(f"❌ Erro ao processar metadados: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def parse_multipart(self):
        """Parse multipart form data manualmente (Python 3.13+)"""
        content_type = self.headers['Content-Type']
        if 'multipart/form-data' not in content_type:
            return None

        # Extrair boundary
        boundary = content_type.split('boundary=')[1].encode()

        # Ler body completo
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        # Dividir por boundary
        parts = body.split(b'--' + boundary)

        files = {}
        fields = {}

        for part in parts[1:-1]:  # Ignorar primeiro e último
            if not part.strip():
                continue

            # Separar headers e conteúdo
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue

            headers_text = part[:header_end].decode('utf-8', errors='ignore')
            content = part[header_end+4:]

            # Remover trailing \r\n
            if content.endswith(b'\r\n'):
                content = content[:-2]

            # Parse header Content-Disposition
            if 'Content-Disposition' in headers_text:
                for line in headers_text.split('\r\n'):
                    if 'Content-Disposition' in line:
                        # Extrair name e filename
                        name_match = line.find('name="')
                        if name_match != -1:
                            name_start = name_match + 6
                            name_end = line.find('"', name_start)
                            field_name = line[name_start:name_end]

                            # Check se é ficheiro
                            filename_match = line.find('filename="')
                            if filename_match != -1:
                                filename_start = filename_match + 10
                                filename_end = line.find('"', filename_start)
                                filename = line[filename_start:filename_end]

                                files[field_name] = {
                                    'filename': filename,
                                    'content': content
                                }
                            else:
                                # Campo normal
                                fields[field_name] = content.decode('utf-8', errors='ignore')

        return {'files': files, 'fields': fields}

    def handle_mkv_analyze(self):
        """Analisa ficheiro MKV e retorna tracks de legendas"""
        try:
            # Ler body como JSON
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            if 'file_path' not in data:
                self.send_error(400, 'file_path is required')
                return

            file_path = data['file_path']

            # Validar que ficheiro existe
            if not os.path.exists(file_path):
                self.send_error(404, f'File not found: {file_path}')
                return

            print(f"🔍 Analisando MKV: {file_path}")

            # Analisar tracks diretamente do ficheiro original
            tracks = mkv_extractor.list_subtitle_tracks(file_path)

            # Converter para dicionário
            tracks_data = [track.to_dict() for track in tracks]

            response = {
                'success': True,
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'tracks': tracks_data,
                'count': len(tracks_data)
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print(f"✅ {len(tracks_data)} tracks encontradas")

        except Exception as e:
            print(f"❌ Erro ao analisar MKV: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def handle_mkv_extract(self):
        """Extrai tracks de legendas selecionadas"""
        try:
            # Ler body como JSON
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            if 'file_path' not in data or 'track_ids' not in data:
                self.send_error(400, 'file_path and track_ids are required')
                return

            file_path = data['file_path']
            track_ids = data['track_ids']

            # Validar que ficheiro existe
            if not os.path.exists(file_path):
                self.send_error(404, f'File not found: {file_path}')
                return

            print(f"📤 Extraindo {len(track_ids)} track(s) de: {os.path.basename(file_path)}")

            # Criar diretório de saída
            output_dir = tempfile.mkdtemp(prefix='scriptum_subs_')

            # Extrair tracks diretamente do ficheiro original
            extracted_files = mkv_extractor.extract_multiple(file_path, track_ids, output_dir)

            # Preparar resposta com info dos ficheiros
            files_info = []
            for file_path_extracted in extracted_files:
                file_size = os.path.getsize(file_path_extracted)

                # Encontrar track_id baseado no nome do ficheiro
                track_id = None
                for tid in track_ids:
                    if f"_track{tid}_" in file_path_extracted or f"_track_{tid}_" in file_path_extracted:
                        track_id = tid
                        break

                files_info.append({
                    'path': file_path_extracted,
                    'size': file_size,
                    'name': os.path.basename(file_path_extracted),
                    'track_id': track_id
                })

            response = {
                'success': True,
                'extracted_files': files_info,
                'count': len(files_info),
                'output_dir': output_dir
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print(f"✅ {len(files_info)} ficheiro(s) extraído(s)")

        except Exception as e:
            print(f"❌ Erro ao extrair tracks: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def handle_file_serve(self, params):
        """Serve extracted subtitle file"""
        try:
            if 'path' not in params:
                self.send_error(400, 'Parameter path is required')
                return

            file_path = params['path'][0]

            # Validação de segurança: apenas ficheiros em /tmp/scriptum_subs_
            if not file_path.startswith('/tmp/scriptum_subs_') and not file_path.startswith('/var/folders/'):
                self.send_error(403, 'Access denied')
                return

            if not os.path.exists(file_path):
                self.send_error(404, 'File not found')
                return

            print(f"📄 Servindo ficheiro: {file_path}")

            # Ler e enviar ficheiro
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(content.encode('utf-8'))
            print(f"✅ Ficheiro servido ({len(content)} bytes)")

        except Exception as e:
            print(f"❌ Erro ao servir ficheiro: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"📡 {args[0]} - {args[1]}")

if __name__ == '__main__':
    port = 8080
    server = HTTPServer(('localhost', port), ScriptumAPIHandler)

    print("🚀 Scriptum API Server")
    print(f"📡 Server running on http://localhost:{port}")
    print(f"📄 Health check: http://localhost:{port}/api/health")
    print(f"🎬 Metadata: http://localhost:{port}/api/metadata?filename=Inception.2010.en.srt")
    print("\n⌨️  Press CTRL+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        server.shutdown()
