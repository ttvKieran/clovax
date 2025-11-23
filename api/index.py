import sys
from pathlib import Path

# Thêm project root vào sys.path để import module ngoài api/
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import FastAPI app
from app.personalize_api import app
