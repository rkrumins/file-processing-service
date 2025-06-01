# constants.py

# Application Defaults
DEFAULT_UPLOAD_DIRECTORY = "./files"
# DEFAULT_PROCESSING_DURATION_SECONDS = 10 # This seems unused if genai_processing_duration is primary
DEFAULT_PROCESSING_STEPS = 20
DEFAULT_GENAI_PROCESSING_DURATION_SECONDS = 60 # Default to 60 seconds

# CORS Defaults
DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Server Defaults
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 8000

# DEFAULT_TASK_STORAGE_TYPE = "in_memory" # This is effectively hardcoded to in_memory in server.py now
DEFAULT_SIMULATED_TASK_URL = "https://www.google.com" # Keep if still relevant for other potential uses

# MongoDB Defaults (currently unused but kept for reference if re-enabled)
DEFAULT_MONGODB_URI = "mongodb://localhost:27017"
DEFAULT_MONGODB_DATABASE_NAME = "files_db"
DEFAULT_MONGODB_COLLECTION_NAME = "tasks"

# External LLM service
DEFAULT_EXTERNAL_SERVICE_URL = "http://localhost:8001/process_data" # Example
DEFAULT_EXTERNAL_PROCESSING_ESTIMATED_DURATION_SECONDS = 120 # For progress simulation
DEFAULT_EXTERNAL_PROCESSING_TIMEOUT_SECONDS = 300 # Timeout for the actual call