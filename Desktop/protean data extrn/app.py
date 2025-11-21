from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from protean import get_website_info, save_website_info_to_db, generate_ghana_ecommerce_sites

app = FastAPI(title="Protean Website Intelligence")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "image.png"


@app.get("/image.png")
async def logo_image():
    return FileResponse(LOGO_PATH, media_type="image/png")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": None,
            "url": "",
        },
    )


@app.post("/", response_class=HTMLResponse)
async def analyze(
    request: Request,
    url: str = Form(""),
    action: str = Form("analyze"),
):
    url = url.strip()

    if action == "reset":
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": None,
                "url": "",
            },
        )

    if not url:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": "Please enter a website URL.",
                "url": url,
            },
        )

    if not url.startswith("http"):
        url = "https://" + url

    info = get_website_info(url)

    if not info:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": "Failed to fetch website information. Please check the URL and try again.",
                "url": url,
            },
        )

    save_website_info_to_db(info)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": info,
            "error": None,
            "url": url,
        },
    )


@app.get("/ghana", response_class=HTMLResponse)
async def ghana_page(request: Request):
    return templates.TemplateResponse(
        "ghana.html",
        {
            "request": request,
            "result": None,
            "error": None,
        },
    )


@app.get("/api/ghana-sites")
async def get_ghana_sites():
    """Generate and return Ghana e-commerce websites as JSON."""
    sites = generate_ghana_ecommerce_sites()
    return JSONResponse({"sites": sites})


@app.post("/api/analyze-site")
async def analyze_site(url: str = Form(...)):
    """Analyze a single website and return info as JSON."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    info = get_website_info(url)

    if not info:
        return JSONResponse(
            {"error": "Failed to fetch website information."},
            status_code=400,
        )

    save_website_info_to_db(info)

    return JSONResponse(info)
