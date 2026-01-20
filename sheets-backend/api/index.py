from mangum import Mangum
import sys
import os

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

# Wrap FastAPI app with Mangum for serverless
handler = Mangum(app, lifespan="off")
