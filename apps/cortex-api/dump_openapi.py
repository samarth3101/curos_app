import json
from pathlib import Path

from app.main import app

with Path("openapi.json").open("w") as f:
    json.dump(app.openapi(), f, indent=2)
