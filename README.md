# Document Summarizer RAG Application

A powerful Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and interact with them through a chat interface. The application uses AWS Bedrock models for embeddings and language generation, with ChromaDB as the vector store for efficient document retrieval.

## Features

- **Document Upload**: Upload single or multiple PDF files
- **Intelligent Chunking**: Automatically splits documents into optimized chunks for better retrieval
- **Vector Storage**: Uses ChromaDB for efficient similarity search and document retrieval
- **Chat Interface**: Interactive chat to ask questions about uploaded documents
- **AWS Bedrock Integration**: Uses Amazon Nova Lite and Titan embeddings models
- **Document Management**: View, list, and delete uploaded documents
- **Duplicate Detection**: Prevents re-processing of already uploaded documents

## Requirements

- Python 3.11.+
- AWS Account with Bedrock access
- AWS credentials configured

## Setup

### 1. Environment Configuration

Copy the example environment file and configure your AWS credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your AWS credentials:

```bash
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_SESSION_TOKEN=your_aws_session_token_if_using_temporary_credentials
AWS_REGION=us-east-1
```

**Important**: Ensure your AWS account has access to the following Bedrock models:

- `amazon.nova-lite-v1:0` (for chat/language generation)
- `amazon.titan-embed-text-v2:0` (for embeddings)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python server.py
```

The application will be available at: http://localhost:5000

## Project Structure

```
document-summarizer-rag/
├── server.py                 # Flask web server and API endpoints
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # Project documentation
├── rag/                     # RAG module
│   ├── __init__.py
│   ├── aws_bedrock_model.py # AWS Bedrock model initialization
│   ├── chat.py              # Chat functionality and response generation
│   ├── chunking.py          # Document chunking and text splitting
│   ├── upload.py            # File upload and management
│   └── vector_store.py      # ChromaDB vector store operations
├── static/                  # Static files
│   ├── style.css           # Application styling
│   └── documents/          # Uploaded PDF storage
├── templates/              # HTML templates
│   ├── chat.html           # Chat interface
│   ├── index.html          # Landing page
│   ├── upload.html         # Upload interface
│   └── upload_success.html # Upload confirmation
└── chroma_store/           # ChromaDB database files
    └── ...                 # Vector database storage
```

## Usage

### 1. Upload Documents

1. Navigate to http://localhost:5000/upload
2. Select one or multiple PDF files
3. Click "Upload" to process the documents
4. Documents will be automatically chunked and stored in the vector database

### 2. Chat with Documents

1. Go to http://localhost:5000/chat (or the main page)
2. Type questions about your uploaded documents
3. The system will retrieve relevant document sections and generate answers
4. View upload statistics and manage your documents from the chat interface

### 3. Manage Documents

- **List Documents**: View all uploaded files and their status
- **Delete Documents**: Remove documents and their associated vectors
- **View Stats**: See total file count and processing status

## API Endpoints

- `GET /` - Redirects to chat interface
- `GET /chat` - Chat interface page
- `POST /chat` - Send chat messages and receive responses
- `GET /upload` - Upload interface page
- `POST /upload` - Upload documents (single or multiple)
- `DELETE /upload/delete/<filename>` - Delete specific document
- `GET /upload/list` - List all uploaded documents

## Key Dependencies

- **Flask**: Web framework for the application
- **LangChain**: Framework for building LLM applications
- **ChromaDB**: Vector database for document embeddings
- **boto3**: AWS SDK for Bedrock integration
- **python-dotenv**: Environment variable management
- **beautifulsoup4**: HTML parsing for document processing
- **pypdf**: PDF document processing

## Troubleshooting

### AWS Credentials Issues

- Ensure your AWS credentials are correctly set in the `.env` file
- Verify your AWS account has Bedrock model access enabled
- Check that the specified AWS region supports the required Bedrock models

### Document Upload Issues

- Verify PDF files are not corrupted
- Check file permissions in the `static/documents/` directory
- Ensure sufficient disk space for document storage

### Vector Store Issues

- ChromaDB files are stored in `chroma_store/` directory
- Clear the vector store by deleting the `chroma_store/` directory if needed
- Re-upload documents after clearing the vector store

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
