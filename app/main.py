from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

app = FastAPI(title="Scholarship Recommendation Web App")

# Templates resolve relative to this file so it works both locally and on Render
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# Load pre-computed embeddings and scholarship list
model_path = BASE_DIR / "workspace" / "Models" / "sbert"

# Load SBERT model to encode live student profiles at request time
model = SentenceTransformer("all-MiniLM-L6-v2")

with open(model_path / "profile_embeddings.pkl", "rb") as f:
    profile_embeddings = pickle.load(f)
with open(model_path / "scholarship_embeddings.pkl", "rb") as f:
    scholarship_embeddings = pickle.load(f)
with open(model_path / "scholarship_list.pkl", "rb") as f:
    scholarships = pickle.load(f)

similarity_scores = util.cos_sim(profile_embeddings, scholarship_embeddings)


@app.get("/health")
def health():
    """Health check endpoint used by Render."""
    return JSONResponse({"status": "ok", "scholarships_loaded": len(scholarships)})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request},
        request=request  #
    )

@app.post("/recommend", response_class=HTMLResponse)
def recommend(
    request: Request,
    cgpa: float = Form(...),
    income: int = Form(...)
):
    # Build a natural-language profile and encode it on the fly
    query = f"Student with CGPA {cgpa} and family income {income}"
    profile_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(profile_embedding, scholarship_embeddings)[0].cpu().tolist()

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for i, score in ranked[:3]:
        sch = scholarships[i]
        if "CGPA above 3.5" in sch and cgpa < 3.5:
            continue
        if "income below 30,000" in sch and income > 30000:
            continue
        results.append({"scholarship": sch, "score": round(score, 4)})

    return templates.TemplateResponse(
        name="results.html",
        context={
            "request": request,
            "cgpa": cgpa,
            "income": income,
            "recommendations": results
        },
    request = request
    )
