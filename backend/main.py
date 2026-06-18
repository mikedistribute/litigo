from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.v1.routes import analysis


app = FastAPI(title="Litigo API", version="1.0.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(OUTPUTS_DIR)), name="files")

app.include_router(analysis.router, prefix="/api/v1")