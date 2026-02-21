"""
Chunked upload endpoints for parallel file upload.
Accepts file chunks in parallel and stores them in Google Cloud Storage.
GCS is used instead of local filesystem to handle Cloud Run's stateless nature.
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import hashlib
import time
from google.cloud import firestore, storage
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

GCS_BUCKET = "scriptum-uploads"
GCS_CHUNKS_PREFIX = "chunks"
GCS_ASSEMBLED_PREFIX = "uploads"

# Local temp dir for assembly (fast ephemeral disk in Cloud Run)
LOCAL_UPLOAD_FOLDER = Path(__file__).parent.parent.parent.parent / 'uploads'
LOCAL_UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)


def create_chunked_upload_blueprint():
    """
    Create blueprint for chunked parallel upload endpoints.

    Chunks are stored in GCS to survive Cloud Run restarts/scaling.
    Final assembled file is written to GCS and a signed URL is returned.
    """
    bp = Blueprint('chunked_upload', __name__)

    db = firestore.Client()
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(GCS_BUCKET)

    @bp.route('/start-chunked-upload', methods=['POST'])
    def start_chunked_upload():
        """
        Start a chunked upload session.

        Request JSON:
            - filename: original filename
            - total_size: total file size in bytes
            - chunk_size: size of each chunk
            - total_chunks: total number of chunks

        Response JSON:
            - success: boolean
            - upload_id: unique upload session ID
        """
        try:
            data = request.json

            if not data:
                return jsonify({'error': 'No data provided'}), 400

            required_fields = ['filename', 'total_size', 'chunk_size', 'total_chunks']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing field: {field}'}), 400

            # Generate unique upload ID
            upload_id = f"upload_{int(time.time())}_{hashlib.md5(data['filename'].encode()).hexdigest()[:8]}"

            logger.info(
                f"Starting chunked upload: {upload_id} for {data['filename']} "
                f"({data['total_size']} bytes, {data['total_chunks']} chunks)"
            )

            # Create upload session in Firestore
            upload_ref = db.collection('chunked_uploads').document(upload_id)
            upload_ref.set({
                'upload_id': upload_id,
                'filename': data['filename'],
                'total_size': data['total_size'],
                'chunk_size': data['chunk_size'],
                'total_chunks': data['total_chunks'],
                'status': 'uploading',
                'chunks_received': [],
                'storage': 'gcs',
                'gcs_bucket': GCS_BUCKET,
                'created_at': firestore.SERVER_TIMESTAMP
            })

            logger.info(f"Upload session created in Firestore: {upload_id}")

            return jsonify({
                'success': True,
                'upload_id': upload_id
            })

        except Exception as e:
            logger.error(f"Error starting chunked upload: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @bp.route('/upload-chunk/<upload_id>/<int:chunk_index>', methods=['POST'])
    def upload_chunk(upload_id: str, chunk_index: int):
        """
        Upload a single chunk directly to GCS.

        Args:
            upload_id: Upload session ID
            chunk_index: Index of the chunk (0-based)

        Request: multipart/form-data
            - chunk: chunk file data

        Response JSON:
            - success: boolean
            - chunk_index: index of uploaded chunk
        """
        try:
            if 'chunk' not in request.files:
                return jsonify({'error': 'No chunk data'}), 400

            chunk = request.files['chunk']
            chunk_data = chunk.read()

            if not chunk_data:
                return jsonify({'error': 'Empty chunk data'}), 400

            # Verify upload session exists in Firestore
            upload_ref = db.collection('chunked_uploads').document(upload_id)
            upload_doc = upload_ref.get()

            if not upload_doc.exists:
                logger.error(f"Upload session not found: {upload_id}")
                return jsonify({'error': 'Upload session not found'}), 404

            # Upload chunk to GCS
            gcs_path = f"{GCS_CHUNKS_PREFIX}/{upload_id}/chunk_{chunk_index:04d}"
            blob = bucket.blob(gcs_path)
            blob.upload_from_string(chunk_data, content_type='application/octet-stream')

            chunk_size = len(chunk_data)
            logger.debug(f"Chunk {chunk_index} uploaded to GCS: gs://{GCS_BUCKET}/{gcs_path} ({chunk_size} bytes)")

            # Update Firestore progress (use transaction to avoid race conditions)
            @firestore.transactional
            def update_progress(transaction, ref):
                doc = ref.get(transaction=transaction)
                if not doc.exists:
                    return

                data = doc.to_dict()
                chunks_received = data.get('chunks_received', [])

                if chunk_index not in chunks_received:
                    chunks_received.append(chunk_index)
                    chunks_received.sort()
                    progress = (len(chunks_received) / data['total_chunks']) * 100
                    transaction.update(ref, {
                        'chunks_received': chunks_received,
                        'progress': progress,
                        'last_updated': firestore.SERVER_TIMESTAMP
                    })

            transaction = db.transaction()
            update_progress(transaction, upload_ref)

            logger.info(f"Chunk {chunk_index} saved to GCS for upload {upload_id}")

            return jsonify({
                'success': True,
                'chunk_index': chunk_index
            })

        except Exception as e:
            logger.error(f"Error uploading chunk {chunk_index} for {upload_id}: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @bp.route('/finalize-chunked-upload/<upload_id>', methods=['POST'])
    def finalize_chunked_upload(upload_id: str):
        """
        Finalize upload by assembling chunks using GCS Compose.

        GCS Compose merges objects directly in GCS (no local disk needed).
        Compose supports up to 32 objects per operation, so we do it in rounds:
          Round 1: Compose groups of 32 chunks → intermediate blobs
          Round 2: Compose all intermediates → final file

        Args:
            upload_id: Upload session ID

        Response JSON:
            - success: boolean
            - file_path: server-accessible path for processing
            - gcs_path: full gs:// URI
        """
        try:
            upload_ref = db.collection('chunked_uploads').document(upload_id)
            upload_doc = upload_ref.get()

            if not upload_doc.exists:
                return jsonify({'error': 'Upload not found'}), 404

            data = upload_doc.to_dict()

            # Verify all chunks received
            chunks_received = set(data.get('chunks_received', []))
            total_chunks = data['total_chunks']
            expected_chunks = set(range(total_chunks))
            missing_chunks = expected_chunks - chunks_received

            if missing_chunks:
                logger.error(f"Missing chunks for {upload_id}: {sorted(missing_chunks)[:20]}...")
                return jsonify({
                    'error': 'Not all chunks received',
                    'received': len(chunks_received),
                    'expected': total_chunks,
                    'missing_chunks': sorted(list(missing_chunks))[:20]
                }), 400

            logger.info(f"Finalizing upload {upload_id}: composing {total_chunks} chunks in GCS")

            output_filename = f"assembled_{upload_id}_{data['filename']}"
            gcs_assembled_path = f"{GCS_ASSEMBLED_PREFIX}/{output_filename}"

            # Build list of chunk blobs in order
            chunk_blobs = [
                bucket.blob(f"{GCS_CHUNKS_PREFIX}/{upload_id}/chunk_{i:04d}")
                for i in range(total_chunks)
            ]

            # GCS Compose: max 32 sources per operation
            # Use multi-round compose: groups → intermediate → final
            GCS_COMPOSE_MAX = 32
            intermediate_blobs = []

            if total_chunks <= GCS_COMPOSE_MAX:
                # Single compose operation
                final_blob = bucket.blob(gcs_assembled_path)
                final_blob.compose(chunk_blobs)
                logger.info(f"Single compose: {total_chunks} chunks → {gcs_assembled_path}")

            else:
                # Round 1: compose groups of 32
                for group_idx in range(0, total_chunks, GCS_COMPOSE_MAX):
                    group = chunk_blobs[group_idx:group_idx + GCS_COMPOSE_MAX]
                    inter_path = f"{GCS_CHUNKS_PREFIX}/{upload_id}/inter_{group_idx:04d}"
                    inter_blob = bucket.blob(inter_path)
                    inter_blob.compose(group)
                    intermediate_blobs.append(inter_blob)

                    logger.info(
                        f"Composed group {group_idx//GCS_COMPOSE_MAX + 1}: "
                        f"chunks {group_idx}-{group_idx + len(group) - 1}"
                    )

                # Round 2: compose intermediates (if ≤32) or do another round
                if len(intermediate_blobs) <= GCS_COMPOSE_MAX:
                    final_blob = bucket.blob(gcs_assembled_path)
                    final_blob.compose(intermediate_blobs)
                    logger.info(f"Final compose: {len(intermediate_blobs)} intermediates → {gcs_assembled_path}")
                else:
                    # Round 3 (edge case: >1024 chunks = >32 intermediates)
                    round3_blobs = []
                    for group_idx in range(0, len(intermediate_blobs), GCS_COMPOSE_MAX):
                        group = intermediate_blobs[group_idx:group_idx + GCS_COMPOSE_MAX]
                        inter2_path = f"{GCS_CHUNKS_PREFIX}/{upload_id}/inter2_{group_idx:04d}"
                        inter2_blob = bucket.blob(inter2_path)
                        inter2_blob.compose(group)
                        round3_blobs.append(inter2_blob)

                    final_blob = bucket.blob(gcs_assembled_path)
                    final_blob.compose(round3_blobs)
                    logger.info(f"Round 3 compose: {len(round3_blobs)} blobs → final")

            # Verify assembled file size
            final_blob.reload()
            actual_size = final_blob.size
            expected_size = data['total_size']
            size_diff_mb = abs(actual_size - expected_size) / (1024 * 1024)

            if size_diff_mb > 1:
                logger.warning(
                    f"Size mismatch: expected {expected_size:,} bytes, "
                    f"got {actual_size:,} bytes (diff: {size_diff_mb:.2f}MB)"
                )
            else:
                logger.info(f"Assembly verified: {actual_size:,} bytes at gs://{GCS_BUCKET}/{gcs_assembled_path}")

            # Clean up GCS chunks and intermediates
            try:
                blobs_to_delete = list(bucket.list_blobs(prefix=f"{GCS_CHUNKS_PREFIX}/{upload_id}/"))
                if blobs_to_delete:
                    bucket.delete_blobs(blobs_to_delete)
                    logger.info(f"Deleted {len(blobs_to_delete)} chunk/intermediate blobs from GCS")
            except Exception as e:
                logger.warning(f"Failed to cleanup GCS chunks: {e}")

            # Update Firestore
            upload_ref.update({
                'status': 'completed',
                'gcs_path': gcs_assembled_path,
                'output_filename': output_filename,
                'actual_size': actual_size,
                'progress': 100,
                'completed_at': firestore.SERVER_TIMESTAMP
            })

            logger.info(f"Upload {upload_id} completed: gs://{GCS_BUCKET}/{gcs_assembled_path}")

            return jsonify({
                'success': True,
                'file_path': f"gs://{GCS_BUCKET}/{gcs_assembled_path}",
                'gcs_path': f"gs://{GCS_BUCKET}/{gcs_assembled_path}",
                'filename': output_filename,
                'upload_id': upload_id,
                'size': actual_size
            })

        except Exception as e:
            logger.error(f"Error finalizing upload {upload_id}: {e}", exc_info=True)

            try:
                upload_ref.update({
                    'status': 'error',
                    'error': str(e),
                    'failed_at': firestore.SERVER_TIMESTAMP
                })
            except Exception:
                pass

            return jsonify({'error': str(e)}), 500

    @bp.route('/chunked-upload-status/<upload_id>', methods=['GET'])
    def get_chunked_upload_status(upload_id: str):
        """
        Get upload progress status.
        """
        try:
            upload_ref = db.collection('chunked_uploads').document(upload_id)
            upload_doc = upload_ref.get()

            if not upload_doc.exists:
                return jsonify({'error': 'Upload not found'}), 404

            data = upload_doc.to_dict()

            return jsonify({
                'upload_id': upload_id,
                'status': data['status'],
                'progress': data.get('progress', 0),
                'chunks_received': len(data.get('chunks_received', [])),
                'total_chunks': data['total_chunks'],
                'filename': data['filename']
            })

        except Exception as e:
            logger.error(f"Error getting upload status for {upload_id}: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    return bp
