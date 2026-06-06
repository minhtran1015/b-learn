import sys
from pathlib import Path
import importlib.util

# Resolve repository root and add to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Dynamically import backend-api/serving_gateway.py due to hyphen in folder name
gateway_path = REPO_ROOT / "backend-api" / "serving_gateway.py"
spec = importlib.util.spec_from_file_location("serving_gateway", str(gateway_path))
serving_gateway = importlib.util.module_from_spec(spec)
sys.modules["backend_api_serving_gateway"] = serving_gateway
spec.loader.exec_module(serving_gateway)

app = serving_gateway.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
