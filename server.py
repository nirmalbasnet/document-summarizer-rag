from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

from rag.chat import Chat
from rag.chunking import Chunking
from rag.vector_store import VectorStore
from rag.upload import DocumentUploader

load_dotenv()

app = Flask(__name__)

chat_instance = Chat()
uploader = DocumentUploader()

# Process the uploaded document for vector storage
vector_store = VectorStore()
splitter = Chunking()

@app.route("/")
def home():
    return redirect(url_for("chat"))

@app.route("/chat", methods=["GET"])
def chat_interface():
    """
    Route to display the chat interface page.
    """
    try:
        # Get upload statistics to show in chat interface
        stats = uploader.get_upload_stats()
        files = uploader.list_uploaded_files()
        
        file_count = stats.get('total_files', 0)
        
        return render_template("chat.html", 
                             file_count=file_count,
                             uploaded_files=files)
                             
    except Exception as e:
        print(f"Error loading chat interface: {e}")
        # Fallback with default values
        return render_template("chat.html", 
                             file_count=0,
                             uploaded_files=[])


@app.route("/upload")
def upload_interface():
    """
    Route to display the upload interface page.
    """
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handle file upload endpoint.
    Accepts single or multiple PDF files for processing.
    """
    try:
        # Check if any files were uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request'
            }), 400
        
        uploaded_files = request.files.getlist('file')

        print(f"Number of files uploaded: {uploaded_files}")
        
        if not uploaded_files or all(file.filename == '' for file in uploaded_files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # # Handle single file upload
        if len(uploaded_files) == 1:
            result = uploader.save_file(uploaded_files[0])
            
            # If successful, process the document for RAG
            if result['success']:
                try:
                    # Check if document is already processed
                    is_already_ingested = vector_store.is_document_already_ingested(
                        metadata={'document_name': result['filename']}
                    )

                    print(f"Is document already ingested: {is_already_ingested}")
                    
                    if not is_already_ingested:
                        # Get chunks from the uploaded document
                        chunks = splitter.get_chunks(
                            document_name=result['original_filename'],
                            file_path=result['file_path']
                        )
                        
                        # Add to vector store
                        vector_store.add_documents_from_chunks(
                            chunks,
                            document_name=result['filename'],
                            file_path=result['file_path']
                        )
                        
                        result['processed_for_rag'] = True
                        result['message'] += ' and processed for chat queries'
                    else:
                        result['processed_for_rag'] = False
                        result['message'] += ' (already processed for chat)'
                        
                except Exception as e:
                    print(f"Error processing document for RAG: {e}")
                    result['processed_for_rag'] = False
                    result['rag_error'] = str(e)
            
            return jsonify(result)
        
        # Handle multiple file upload
        else:
            result = uploader.upload_multiple_files(uploaded_files)
            
            # Process successful uploads for RAG
            if result['successful_uploads'] > 0:
                try:
                    processed_count = 0
                    
                    for file_result in result['results']:
                        if file_result['success']:
                            try:
                                # Check if document is already processed
                                is_already_ingested = vector_store.is_document_already_ingested(
                                    metadata={'document_name': file_result['filename']}
                                )
                                
                                if not is_already_ingested:
                                    # Get chunks from the uploaded document
                                    chunks = splitter.get_chunks(
                                        document_name=file_result['original_filename'],
                                        file_path=file_result['file_path']
                                    )
                                    
                                    # Add to vector store
                                    vector_store.add_documents_from_chunks(
                                        chunks,
                                        document_name=file_result['filename'],
                                        file_path=file_result['file_path']
                                    )
                                    
                                    processed_count += 1
                                    file_result['processed_for_rag'] = True
                                else:
                                    file_result['processed_for_rag'] = False
                                    
                            except Exception as e:
                                print(f"Error processing {file_result['filename']} for RAG: {e}")
                                file_result['processed_for_rag'] = False
                                file_result['rag_error'] = str(e)
                    
                    result['processed_for_rag'] = processed_count
                    result['message'] += f' ({processed_count} processed for chat queries)'
                    
                except Exception as e:
                    print(f"Error processing documents for RAG: {e}")
                    result['rag_error'] = str(e)
            
            return jsonify(result)
            
    except Exception as e:
        print(f"Error in upload endpoint: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route("/upload/delete/<filename>", methods=["DELETE"])
def delete_upload(filename):
    """
    Delete an uploaded file.
    """
    try:
        vector_store.delete_document_vectors(document_name=filename)
        result = uploader.delete_file(filename)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error deleting upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete file: {str(e)}'
        }), 500

@app.route("/upload/list", methods=["GET"])
def list_uploads():
    """
    List all uploaded files.
    """
    try:
        files = uploader.list_uploaded_files()
        stats = uploader.get_upload_stats()
        
        return jsonify({
            'success': True,
            'files': files,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error listing uploads: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list files: {str(e)}'
        }), 500

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    session_id = data.get("sessionId")

    try:
        response = chat_instance.get_response(session_id, user_message)
        
        print(f"User message: {user_message}")
        print(f"Bot response: {response}")
        
        return jsonify({"reply": response})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"reply": "Sorry, I'm having trouble right now. Please try again later."}), 500

if __name__ == "__main__":
    app.run(debug=True)
