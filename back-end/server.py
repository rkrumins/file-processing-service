import shutil
import os
import asyncio
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from typing import Optional, AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from pydantic import Field as PydanticField # Alias to avoid conflict with FastAPI's Field

import utils
# constants.py might be less needed if all defaults are in Pydantic settings
# import constants
from models import TaskData
from storage import ITaskStorage, InMemoryTaskStorage


# --- Pydantic Settings Model ---
class AppSettings(BaseSettings):
    # Existing fields with their current defaults
    upload_directory: str = "./files"
    processing_steps: int = 20
    external_service_url: str = "http://localhost:8001/process_data"
    external_processing_estimated_duration_seconds: int = 120
    external_processing_timeout_seconds: int = 300
    cors_allowed_origins: list[str] = PydanticField(default_factory=lambda: ["http://localhost:3000"])
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Add fields from config.yaml (application section) that were causing errors
    # Defaults are set based on your provided config.yaml
    simulated_task_url: Optional[str] = "https://news.ycombinator.com"
    processing_duration_seconds: Optional[int] = 15
    genai_processing_duration_seconds: Optional[int] = 60
    task_storage_type: Optional[str] = "in_memory"
    # Note: If these fields are always expected and used, you might remove Optional
    # and not provide a default if they must come from config or environment.
    # However, providing defaults based on your example config.yaml is safe.

    class Config:
        env_file = ".env" # Optional: for loading from .env file
        env_prefix = "APP_" # Optional: for environment variable prefixing
        # extra = 'forbid' # This is the default in Pydantic v2 and is good practice

# Load settings from config.yaml and then potentially override with environment variables
cli_args = utils.parse_arguments()
yaml_config = utils.load_config(cli_args.config)

# Flatten YAML config for Pydantic settings compatibility if nested
flat_yaml_config = {}
if "application" in yaml_config:
    flat_yaml_config.update(yaml_config["application"])
if "cors" in yaml_config: # Pydantic expects cors_allowed_origins
    if "allowed_origins" in yaml_config["cors"]:
        flat_yaml_config["cors_allowed_origins"] = yaml_config["cors"]["allowed_origins"]
if "server" in yaml_config:
    flat_yaml_config["server_host"] = yaml_config["server"].get("host", AppSettings().server_host)
    flat_yaml_config["server_port"] = yaml_config["server"].get("port", AppSettings().server_port)

settings = AppSettings(**flat_yaml_config)


os.makedirs(settings.upload_directory, exist_ok=True)


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Application startup: Initializing resources...")
    task_manager = InMemoryTaskStorage()
    await task_manager.initialize()
    app.state.task_manager = task_manager # Store in app.state
    print("Task manager initialized with InMemoryTaskStorage.")
    yield
    print("Application shutdown: Cleaning up resources...")
    if hasattr(app.state, 'task_manager') and app.state.task_manager:
        await app.state.task_manager.close()
    print("Task manager closed.")


app = FastAPI(lifespan=lifespan)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# --- Helper for External Service Call ---
async def call_external_service(
        task_id: str,
        payload: Dict[str, Any],
        task_manager: ITaskStorage,
        current_progress_val: int
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Makes the call to the external service and handles its response/errors.
    Returns (success_status, response_data).
    NOTE: External call is currently disabled for testing/development.
    """
    print(f"Task {task_id}: Simulating external service call (currently disabled). Payload: {payload}")

    # Simulate a short delay as if a quick call was made
    await asyncio.sleep(0.1)

    # Simulate a successful response
    mock_response_data = {
        "message": "Processing simulated successfully by external service (call disabled).",
        "received_payload": payload,
        "processed_rows": 150  # Example data
    }
    print(f"Task {task_id}: Simulated successful response from external microservice.")
    return True, mock_response_data

    # --- Original code for actual external call (commented out) ---
    # try:
    #     async with httpx.AsyncClient(timeout=settings.external_processing_timeout_seconds) as client:
    #         print(f"Task {task_id}: Sending data to external microservice at {settings.external_service_url}...")
    #         response = await client.post(settings.external_service_url, json=payload)
    #         response.raise_for_status()
    #         print(f"Task {task_id}: Received response from external microservice.")
    #         return True, response.json()
    # except httpx.RequestError as exc:
    #     error_message = f"Microservice call failed: {exc}"
    #     print(f"Task {task_id}: {error_message}")
    #     if task_manager:
    #         await task_manager.update_task(
    #             task_id,
    #             {"status": "error", "error_message": error_message, "progress": current_progress_val}
    #         )
    #     return False, None
    # except Exception as exc:
    #     error_message = f"Microservice response error: {exc}"
    #     print(f"Task {task_id}: {error_message}")
    #     if task_manager:
    #         await task_manager.update_task(
    #             task_id,
    #             {"status": "error", "error_message": error_message, "progress": current_progress_val}
    #         )
    #     return False, None


# --- Background Task Processing ---
async def process_file_async(task_id: str, task_manager: ITaskStorage): # Pass task_manager
    """
    Orchestrates file processing by calling an external service and simulating progress.
    """
    current_progress_val = 0
    try:
        task_entry = await task_manager.get_task(task_id)
        if not task_entry:
            print(f"Task {task_id}: Not found at start of processing.")
            return

        await task_manager.update_task(task_id, {"status": "processing", "progress": 0})
        print(
            f"Task {task_id}: Starting processing for '{task_entry.original_filename}'. "
            f"External service: {settings.external_service_url}. "
            f"Estimated duration: {settings.external_processing_estimated_duration_seconds}s."
        )

        payload_to_send = {
            "file_key": task_entry.file_location,
            "original_filename": task_entry.original_filename,
            "task_id_for_reference": task_id
        }

        num_progress_steps = max(1, settings.processing_steps)
        sleep_per_step = settings.external_processing_estimated_duration_seconds / num_progress_steps \
            if settings.external_processing_estimated_duration_seconds > 0 else 0

        # Create the task for the actual service call
        service_call_task = asyncio.create_task(
            call_external_service(task_id, payload_to_send, task_manager, current_progress_val)
        )

        for i in range(num_progress_steps):
            if service_call_task.done():
                break
            if sleep_per_step > 0:
                await asyncio.sleep(sleep_per_step)

            current_progress_val = int(((i + 1) / num_progress_steps) * 99)
            task_still_exists = await task_manager.get_task(task_id) # Check for cancellation
            if not task_still_exists:
                print(f"Task {task_id}: Cancelled during external processing.")
                service_call_task.cancel()
                try:
                    await service_call_task
                except asyncio.CancelledError:
                    print(f"Task {task_id}: External service call task cancelled.")
                return
            await task_manager.update_task(task_id, {"progress": current_progress_val})
            print(f"Task {task_id}: Waiting for external service, simulated progress {current_progress_val}%")

        try:
            service_call_successful, processed_data_from_service = await service_call_task
        except asyncio.CancelledError:
            print(f"Task {task_id}: External service call task was cancelled before completion.")
            return

        if not service_call_successful:
            print(f"Task {task_id}: External service call not successful (final check).")
            return

        print(f"Task {task_id}: External processing successful. Result: {str(processed_data_from_service)[:200]}")
        await task_manager.update_task(task_id, {"status": "complete", "progress": 100, "error_message": None})
        print(f"Task {task_id}: Processing complete for '{task_entry.original_filename}'.")

    except Exception as e:
        print(f"Error in process_file_async for task {task_id}: {e}")
        if task_manager: # Ensure task_manager is available
            await task_manager.update_task(
                task_id,
                {"status": "error", "error_message": str(e), "progress": current_progress_val}
            )


# --- API Endpoints ---
def get_task_manager(request: Request) -> ITaskStorage:
    if not hasattr(request.app.state, 'task_manager') or not request.app.state.task_manager:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable, task manager not ready.")
    return request.app.state.task_manager

@app.post("/upload/")
async def create_upload_file(request: Request, file: UploadFile = File(...)):
    task_manager = get_task_manager(request)
    original_filename = file.filename
    file_location = utils.get_timestamped_filepath(settings.upload_directory, original_filename)

    try:
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        await file.close()

    created_task = await task_manager.create_task(
        file_location=file_location,
        original_filename=original_filename
    )
    # Pass the task_manager instance from app.state to the background task
    asyncio.create_task(process_file_async(created_task.task_id, task_manager))
    return JSONResponse(
        status_code=202,
        content={
            "task_id": created_task.task_id,
            "message": f"File '{original_filename}' received. Processing delegated.",
            "filename": original_filename
        }
    )

@app.get("/status/{task_id}", response_model=TaskData, response_model_exclude_none=True)
async def get_processing_status(request: Request, task_id: str):
    task_manager = get_task_manager(request)
    task_instance = await task_manager.get_task(task_id)
    if not task_instance:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_instance

@app.get("/download/{task_id}")
async def download_processed_file(request: Request, task_id: str):
    task_manager = get_task_manager(request)
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "complete":
        raise HTTPException(status_code=400, detail=f"Task not complete. Status: {task.status}")

    if not task.file_location or not os.path.exists(task.file_location):
        raise HTTPException(status_code=404, detail="Processed file not found.")
    return FileResponse(path=task.file_location, filename=task.original_filename)

@app.get("/health")
async def health_check(request: Request):
    task_manager_ready = hasattr(request.app.state, 'task_manager') and request.app.state.task_manager is not None
    if not task_manager_ready:
        return {"message": "Service starting...", "status": "initializing"}
    return {"message": "Service running.", "storage_type": "in_memory"}


# --- Main Execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.server_host, port=settings.server_port, reload=True)