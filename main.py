from pathlib import Path
import sys

# Ensure Smart_Data_Analyst directory is in Python path
base_dir = Path(__file__).resolve().parent
smart_dir = base_dir / "Smart_Data_Analyst"
if str(smart_dir) not in sys.path:
    sys.path.insert(0, str(smart_dir))

# Import the FastAPI app
from api import app

