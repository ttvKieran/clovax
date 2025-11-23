import sys
from pathlib import Path

# Đảm bảo import được app.personalize_api khi chạy trên Vercel
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app.personalize_api import app

# Entry point cho Vercel: uvicorn api.index:app
