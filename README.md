# 🎓 Scholarship Recommendation System
LIve on => https://scholarship-recommendation-platform.onrender.com/
<img width="1362" height="625" alt="image" src="https://github.com/user-attachments/assets/9edd7e4f-7c35-4523-a414-2f99e7efe8bf" />


An AI-powered web app that matches students to scholarships using **Sentence-BERT** semantic similarity. Built with FastAPI and deployed on Render.

---

## How It Works

1. The student enters their **CGPA** and **family income**
2. The app builds a natural-language profile: `"Student with CGPA 3.8 and family income 15000"`
3. SBERT encodes it into a vector at request time
4. Cosine similarity is computed against pre-encoded scholarship vectors
5. Top matches are filtered by eligibility rules and returned ranked by score

---

## Features

- Live SBERT encoding — no dataset row index required, any student can use it
- Eligibility filtering by CGPA and family income
- Clean, recruiter-friendly UI
- `/health` endpoint for uptime monitoring
- CI/CD via GitHub Actions → auto-deploy to Render on every push to `main`

---

## Project Structure

```
scholarship_recommendation/
├── app/
│   ├── main.py               # FastAPI app & routes
│   └── templates/
│       ├── index.html        # Input form (CGPA + income)
│       └── results.html      # Recommendation results
├── workspace/
│   ├── Models/sbert/
│   │   ├── scholarship_embeddings.pkl   # Pre-computed scholarship vectors
│   │   └── scholarship_list.pkl         # Scholarship name list
│   ├── Data/                 # Cleaned scholarship data
│   ├── Data_Cleaning/        # Cleaning notebooks
│   ├── NER/                  # Named entity recognition notebook
│   ├── Topic_Modeling/       # LDA topic modeling notebook
│   ├── Word_Embedding/       # SBERT embedding notebook
│   └── Resume_Testing/       # End-to-end recommendation notebook
├── data/raw/                 # Raw scraped data
├── tests/
│   └── test_main.py          # Pytest test suite
├── .github/workflows/
│   └── ci.yml                # GitHub Actions CI/CD
├── render.yaml               # Render service config
├── requirements.txt
└── README.md
```

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/scholarship-recommendation.git
cd scholarship-recommendation

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
uvicorn app.main:app --reload

# App is now at http://localhost:8000
```

---

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

The test suite mocks `pickle.load` and `SentenceTransformer` so no GPU or large model download is needed in CI.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Student input form |
| `POST` | `/recommend` | Returns top scholarship matches |
| `GET` | `/health` | Health check (used by Render) |

### POST `/recommend` — form fields

| Field | Type | Description |
|-------|------|-------------|
| `cgpa` | float | Cumulative GPA (0.0 – 4.0) |
| `income` | int | Annual family income in ETB |

### Example `/health` response

```json
{ "status": "ok", "scholarships_loaded": 3 }
```

---

## Deployment on Render

### One-time setup

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Web Service**.
3. Connect your GitHub repo.
4. Render will auto-detect `render.yaml` and fill in:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy**.

> ⚠️ The first deploy downloads the SBERT model (~90 MB). Render caches it after that, so subsequent deploys are fast.

### Auto-deploy on push (CI/CD)

After deploying, set up the GitHub secret so pushes to `main` trigger a Render redeploy:

| Step | What to do |
|------|-----------|
| 1 | Render dashboard → your service → **Settings** → scroll to **Deploy Hook** → copy the URL |
| 2 | GitHub → your repo → **Settings → Secrets → Actions → New secret** |
| 3 | Name: `RENDER_DEPLOY_HOOK_URL` · Value: paste the Render URL |

Now every push to `main` will: **lint → test → deploy** (deploy only runs if tests pass).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI |
| Server | Uvicorn |
| ML / Embeddings | Sentence-Transformers (SBERT) |
| Templating | Jinja2 |
| Testing | Pytest + HTTPX |
| Linting | Ruff |
| CI/CD | GitHub Actions |
| Hosting | Render |
