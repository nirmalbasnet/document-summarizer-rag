# RAG Demo Project

A simple Python web server project that serves HTML files locally.

## Setup

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the server (choose one):

   **Option A - Flask server (recommended):**

   ```bash
   python server.py
   ```

   Then go to: http://localhost:5000

   **Option B - Simple HTTP server (no dependencies):**

   ```bash
   python simple_server.py
   ```

   Then go to: http://localhost:8000

## Project Structure

```
rag-demo/
├── server.py          # Flask web server
├── index.html         # Main HTML file
├── requirements.txt   # Python dependencies
├── static/           # Static files (CSS, JS, images)
├── templates/        # HTML templates (for future use)
└── README.md         # This file
```

## Features

- Simple Flask web server
- Serves `index.html` at the root URL
- Static file serving from `/static/` directory
- Health check endpoint at `/health`
- Hot reloading during development

## Customization

- Edit `index.html` to modify the main page
- Add CSS, JavaScript, or images to the `static/` folder
- Modify `server.py` to add new routes or functionality
