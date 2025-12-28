from fastapi import FastAPI
from app.db.session import engine
from app.db.db import Base
from app.models.user import UserTable
from app.api import auth
from app.api import users
from app.api import tasks
from fastapi.middleware.cors import CORSMiddleware
from app.api import exam
from app.api import stat
from fastapi.staticfiles import StaticFiles
import os
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
current_file_path = os.path.abspath(__file__) 

# 2. Go up ONE level to reach the 'backend' folder
# If current_file_path is /home/.../backend/app/main.py,
# backend_dir becomes /home/.../backend
backend_dir = os.path.dirname(os.path.dirname(current_file_path))

# 3. Define the static path relative to the backend folder
static_path = os.path.join(backend_dir, "static")

# 4. CRITICAL: Ensure the directory exists BEFORE mounting
# This prevents the 'RuntimeError: Directory does not exist'
if not os.path.exists(static_path):
    os.makedirs(os.path.join(static_path, "exam_images"), exist_ok=True)
    print(f"📁 Created missing directory: {static_path}")

# 5. Mount the directory
app.mount("/static", StaticFiles(directory=static_path), name="static")

print(f"🚀 Server starting. Static files served from: {static_path}")
Base.metadata.create_all(bind=engine)
print(f"✅ Static files mounted at: {static_path}")
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(exam.router)
app.include_router(stat.router, prefix="/api/stats", tags=["Performance"])
@app.get("/")
def health_check():
    return {"status": "DB connected successfully"}
