import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ruta absoluta del directorio del script
BASE_DIR = Path(__file__).parent.resolve()

sys.path.insert(0, str(Path(__file__).parent))


# Carga el .env con ruta absoluta
load_dotenv(BASE_DIR / ".env")

# Fuerza stdio y rutas absolutas
os.environ["MCP_TRANSPORT"] = "stdio"
os.environ["CHROMA_PATH"] = str(BASE_DIR / "data" / "chroma")
os.environ["PYTHONPATH"] = str(BASE_DIR / "src")

# Agrega src al path
sys.path.insert(0, str(BASE_DIR / "src"))

# Importa y ejecuta el servidor
from server import mcp
mcp.run(transport="stdio")