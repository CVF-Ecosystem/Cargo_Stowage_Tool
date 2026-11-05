from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router

app = FastAPI(title="SCST Demo API", version="0.1.0", description="Synthetic BOX / single-layer planning demo; not operational approval.")
app.include_router(router)


def _start_auto_backup() -> None:
    """M5b: background auto backup; any failure is swallowed so startup is never blocked or broken."""
    try:
        from .adapters import backup_auto
        backup_auto.start_background()
    except Exception:
        pass


app.router.on_startup.append(_start_auto_backup)
dist = Path(__file__).resolve().parents[3] / "apps" / "frontend" / "dist"

if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def index():
    if not (dist / "index.html").is_file():
        return {"message": "Build frontend first: tooling/setup.ps1"}
    return FileResponse(dist / "index.html")
