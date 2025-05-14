from datetime import date, datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, constr, validator

app = FastAPI()

# Database simulation (in-memory storage)
users_db = {}
tasks_db = {}
task_id_counter = 1

# Status options
TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]

# Models
class UserBase(BaseModel):
    username: constr(min_length=3, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: date
    status: str = "pending"

class TaskCreate(TaskBase):
    user_id: int

class Task(TaskBase):
    id: int
    user_id: int
    created_at: datetime

    @validator('status')
    def validate_status(cls, v):
        if v not in TASK_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(TASK_STATUSES)}")
        return v

    @validator('due_date')
    def validate_due_date(cls, v):
        if v < date.today():
            raise ValueError("Due date must be today or in the future")
        return v

# Endpoints
@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate):
    user_id = len(users_db) + 1
    user_data = user.dict()
    user_data['id'] = user_id
    users_db[user_id] = user_data
    return user_data

@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/tasks/", response_model=Task)
def create_task(task: TaskCreate):
    if task.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    global task_id_counter
    task_data = task.dict()
    task_data['id'] = task_id_counter
    task_data['created_at'] = datetime.now()
    task_data['status'] = "pending"  # Default status
    
    # Validate due_date
    if task_data['due_date'] < date.today():
        raise HTTPException(status_code=400, detail="Due date must be today or in the future")
    
    tasks_db[task_id_counter] = task_data
    task_id_counter += 1
    return task_data

@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.put("/tasks/{task_id}", response_model=Task)
def update_task_status(task_id: int, status: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status not in TASK_STATUSES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(TASK_STATUSES)}"
        )
    
    tasks_db[task_id]['status'] = status
    return tasks_db[task_id]

@app.get("/users/{user_id}/tasks", response_model=List[Task])
def list_user_tasks(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_tasks = [task for task in tasks_db.values() if task['user_id'] == user_id]
    return user_tasks