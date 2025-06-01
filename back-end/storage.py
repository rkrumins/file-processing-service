from typing import Protocol, Dict, Any, Optional
# Removed Motor and Beanie imports

from models import TaskData  # Use TaskData for in-memory storage

# Removed constants import as it was for MongoDB defaults

# --- Storage Interface (Protocol) ---
class ITaskStorage(Protocol):
    # Initialize might not need MongoDB specific params anymore
    async def initialize(self): ... # Simplified initialize
    async def close(self): ...
    async def create_task(self, file_location: str, original_filename: str) -> TaskData: ...
    async def get_task(self, task_id: str) -> Optional[TaskData]: ...
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskData]: ...


# --- In-Memory Storage Implementation ---
class InMemoryTaskStorage(ITaskStorage):
    def __init__(self):
        self._tasks: Dict[str, TaskData] = {}

    async def initialize(self): # Simplified initialize
        print("Initializing InMemoryTaskStorage.")
        self._tasks = {}

    async def close(self):
        print("Closing InMemoryTaskStorage (no-op).")
        pass

    async def create_task(self, file_location: str, original_filename: str) -> TaskData:
        # TaskData model's default_factory for task_id and created_at will be used
        task_instance = TaskData(
            file_location=file_location,
            original_filename=original_filename
        )
        self._tasks[task_instance.task_id] = task_instance
        return task_instance

    async def get_task(self, task_id: str) -> Optional[TaskData]:
        return self._tasks.get(task_id)

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskData]:
        task = self._tasks.get(task_id)
        if task:
            # Create a new TaskData instance with updated fields
            # Pydantic models are generally immutable or encourage immutability
            updated_data = task.model_dump() # Get current data as dict
            updated_data.update(updates)    # Apply updates
            try:
                updated_task = TaskData(**updated_data) # Create new instance
                self._tasks[task_id] = updated_task
                return updated_task
            except Exception as e: # Catch potential validation errors
                print(f"Error updating task {task_id} with data {updated_data}: {e}")
                return task # Return original task on error
        return None