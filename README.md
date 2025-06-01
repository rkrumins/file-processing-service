# File Upload & Processing Service

A full-stack application for uploading, processing, and downloading files. The back-end is built with FastAPI (Python), and the front-end uses React (JavaScript).

---

## Features

- Upload files via a web interface
- Asynchronous file processing with progress tracking
- Download processed files
- In-memory task management (optionally extendable)
- Configurable via YAML

---

## Architecture

- **Back-end:** FastAPI, async processing, in-memory storage (`back-end/server.py`)
- **Front-end:** React, Material UI, Axios (`front-end/src/App.js`)

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js & npm

---

### Back-end Setup

1. **Install dependencies:**
    ```bash
    cd back-end
    pip install -r requirements.txt
    ```

2. **Configuration:**
    - Edit `config.yaml` to adjust settings (upload directory, CORS, processing durations, etc.)
    - Environment variables can override config values (see `server.py` for details).

3. **Run the server:**
    ```bash
    uvicorn server:app --reload
    ```
    - Default: http://localhost:8000

---

### Front-end Setup

1. **Install dependencies:**
    ```bash
    cd front-end
    npm install
    ```

2. **Start the development server:**
    ```bash
    npm start
    ```
    - Default: http://localhost:3000

---

## Usage

1. Open the front-end in your browser.
2. Upload a file.
3. Wait for processing to complete (progress bar shown).
4. Download the processed file.

---

## API Endpoints

- `POST /upload/` — Upload a file for processing
- `GET /status/{task_id}` — Get processing status for a file
- `GET /download/{task_id}` — Download the processed file
- `GET /health` — Health check endpoint

---

## Configuration

- All options are in `back-end/config.yaml`:
    - `upload_directory`: Directory for uploaded files
    - `external_service_url`: URL of the external processing service
    - `processing_steps`: Number of progress steps
    - `external_processing_estimated_duration_seconds`: Simulated processing time
    - `CORS` settings, etc.
- Environment variables can override config values.

---

## Project Structure

```text
project-root/
├── back-end/
│   ├── server.py
│   ├── models.py
│   ├── storage.py
│   ├── utils.py
│   ├── constants.py
│   └── config.yaml
└── front-end/
    └── src/
        └── App.js
```

## Developer Setup

Follow these steps to set up your development environment:

1. **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd project-root
    ```

2. **Set up Python virtual environment (recommended):**
    ```bash
    cd back-end
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Install front-end dependencies:**
    ```bash
    cd ../front-end
    npm install
    ```

4. **Configure environment variables (optional):**
    - Copy `.env.example` to `.env` in both `back-end` and `front-end` if available, and adjust as needed.

5. **Run back-end and front-end in development mode:**
    - Back-end:
        ```bash
        cd back-end
        uvicorn server:app --reload
        ```
    - Front-end:
        ```bash
        cd front-end
        npm start
        ```

6. **Code style and linting:**
    - Back-end: Use `flake8` or `black` for Python code formatting.
    - Front-end: Use `eslint` and `prettier` for JavaScript/React code.

7. **Run tests:**
    - Back-end:
        ```bash
        cd back-end
        pytest
        ```
    - Front-end:
        ```bash
        cd front-end
        npm test
        ```
