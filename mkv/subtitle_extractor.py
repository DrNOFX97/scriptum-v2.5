#!/usr/bin/env python3
"""
MKV Subtitle Extractor - Extrai legendas de ficheiros MKV
"""

import subprocess
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional


class SubtitleTrack:
    """Representa uma track de legendas"""

    def __init__(self, track_id: int, codec: str, language: str, track_name: str, is_default: bool):
        self.track_id = track_id
        self.codec = codec
        self.language = language
        self.track_name = track_name
        self.is_default = is_default

    def __repr__(self):
        return f"Track {self.track_id}: {self.language} ({self.codec}) - {self.track_name}"

    def to_dict(self) -> Dict:
        return {
            'id': self.track_id,
            'codec': self.codec,
            'language': self.language,
            'name': self.track_name,
            'is_default': self.is_default
        }


class MKVSubtitleExtractor:
    """Extrai legendas de ficheiros MKV"""

    SUBTITLE_CODECS = {
        'S_TEXT/UTF8': 'SRT',
        'S_TEXT/SSA': 'SSA',
        'S_TEXT/ASS': 'ASS',
        'S_HDMV/PGS': 'PGS',
        'S_VOBSUB': 'VobSub',
        'S_TEXT/WEBVTT': 'WebVTT'
    }

    def __init__(self):
        """Inicializa o extractor"""
        self.mkvmerge_path = self._find_mkvmerge()
        self.mkvextract_path = self._find_mkvextract()

        if not self.mkvmerge_path:
            raise RuntimeError("mkvmerge não encontrado! Instale mkvtoolnix: brew install mkvtoolnix")

        if not self.mkvextract_path:
            raise RuntimeError("mkvextract não encontrado! Instale mkvtoolnix: brew install mkvtoolnix")

    def _find_mkvmerge(self) -> Optional[str]:
        """Encontra o executável mkvmerge"""
        try:
            result = subprocess.run(['which', 'mkvmerge'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _find_mkvextract(self) -> Optional[str]:
        """Encontra o executável mkvextract"""
        try:
            result = subprocess.run(['which', 'mkvextract'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def list_subtitle_tracks(self, mkv_file: str) -> List[SubtitleTrack]:
        """
        Lista todas as tracks de legendas no ficheiro MKV

        Args:
            mkv_file: Caminho para o ficheiro MKV

        Returns:
            Lista de SubtitleTrack
        """
        if not os.path.exists(mkv_file):
            raise FileNotFoundError(f"Ficheiro não encontrado: {mkv_file}")

        print(f"🔍 Analisando ficheiro MKV: {mkv_file}")

        # Usar mkvmerge -J para obter info em JSON
        try:
            result = subprocess.run(
                [self.mkvmerge_path, '-J', mkv_file],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            tracks = []

            # Processar tracks
            for track in data.get('tracks', []):
                if track['type'] == 'subtitles':
                    track_id = track['id']
                    codec = track['codec']
                    language = track['properties'].get('language', 'und')
                    track_name = track['properties'].get('track_name', '')
                    is_default = track['properties'].get('default_track', False)

                    subtitle_track = SubtitleTrack(
                        track_id=track_id,
                        codec=self.SUBTITLE_CODECS.get(codec, codec),
                        language=language,
                        track_name=track_name,
                        is_default=is_default
                    )

                    tracks.append(subtitle_track)
                    print(f"   ✅ {subtitle_track}")

            print(f"\n📊 Total: {len(tracks)} track(s) de legendas encontradas")
            return tracks

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao analisar MKV: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON do mkvmerge: {e}")
            raise

    def extract_subtitle(self, mkv_file: str, track_id: int, output_file: Optional[str] = None) -> str:
        """
        Extrai uma track de legendas específica

        Args:
            mkv_file: Caminho para o ficheiro MKV
            track_id: ID da track a extrair
            output_file: Caminho de saída (opcional)

        Returns:
            Caminho do ficheiro extraído
        """
        if not os.path.exists(mkv_file):
            raise FileNotFoundError(f"Ficheiro não encontrado: {mkv_file}")

        # Gerar nome de output se não fornecido
        if not output_file:
            mkv_path = Path(mkv_file)
            output_file = str(mkv_path.parent / f"{mkv_path.stem}_track{track_id}.srt")

        print(f"📤 Extraindo track {track_id} para: {output_file}")

        try:
            # mkvextract tracks input.mkv track_id:output.srt
            result = subprocess.run(
                [self.mkvextract_path, 'tracks', mkv_file, f'{track_id}:{output_file}'],
                capture_output=True,
                text=True,
                check=True
            )

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"   ✅ Legendas extraídas ({file_size} bytes)")
                return output_file
            else:
                raise RuntimeError("Ficheiro de saída não foi criado")

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao extrair legendas: {e.stderr}")
            raise

    def extract_multiple(self, mkv_file: str, track_ids: List[int], output_dir: Optional[str] = None) -> List[str]:
        """
        Extrai múltiplas tracks de legendas

        Args:
            mkv_file: Caminho para o ficheiro MKV
            track_ids: Lista de IDs de tracks
            output_dir: Diretório de saída (opcional)

        Returns:
            Lista de caminhos dos ficheiros extraídos
        """
        if not output_dir:
            output_dir = str(Path(mkv_file).parent)

        os.makedirs(output_dir, exist_ok=True)

        extracted_files = []

        for track_id in track_ids:
            try:
                mkv_path = Path(mkv_file)
                output_file = os.path.join(output_dir, f"{mkv_path.stem}_track{track_id}.srt")

                result = self.extract_subtitle(mkv_file, track_id, output_file)
                extracted_files.append(result)

            except Exception as e:
                print(f"⚠️ Erro ao extrair track {track_id}: {e}")
                continue

        print(f"\n✅ {len(extracted_files)}/{len(track_ids)} tracks extraídas com sucesso")
        return extracted_files


def main():
    """Função de teste"""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python3 subtitle_extractor.py <ficheiro.mkv>")
        sys.exit(1)

    mkv_file = sys.argv[1]

    try:
        extractor = MKVSubtitleExtractor()

        # Listar tracks
        tracks = extractor.list_subtitle_tracks(mkv_file)

        if not tracks:
            print("\n⚠️ Nenhuma track de legendas encontrada")
            sys.exit(0)

        # Mostrar tracks
        print("\n📋 Tracks disponíveis:")
        for i, track in enumerate(tracks, 1):
            default_marker = "⭐" if track.is_default else "  "
            print(f"   {default_marker} [{i}] Track {track.track_id}: {track.language} ({track.codec})")
            if track.track_name:
                print(f"        Nome: {track.track_name}")

        # Perguntar quais extrair
        print("\n❓ Quais tracks deseja extrair? (ex: 1,3 ou 'all' para todas)")
        choice = input("   Escolha: ").strip().lower()

        if choice == 'all':
            track_ids = [t.track_id for t in tracks]
        else:
            indices = [int(x.strip()) for x in choice.split(',')]
            track_ids = [tracks[i-1].track_id for i in indices if 0 < i <= len(tracks)]

        if not track_ids:
            print("⚠️ Nenhuma track selecionada")
            sys.exit(0)

        # Extrair
        print(f"\n🚀 Extraindo {len(track_ids)} track(s)...\n")
        extracted = extractor.extract_multiple(mkv_file, track_ids)

        print(f"\n✅ Ficheiros extraídos:")
        for file in extracted:
            print(f"   📄 {file}")

        # Perguntar sobre tradução
        print("\n❓ Deseja traduzir estas legendas?")
        translate = input("   (s/n): ").strip().lower()

        if translate == 's':
            print("\n🔄 Iniciando processo de tradução...")
            # Aqui integramos com o sistema de tradução
        else:
            print("\n👋 Processo concluído!")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
