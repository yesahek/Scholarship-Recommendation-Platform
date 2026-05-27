# 🎓 Scholarship Recommendation System
Link => https://scholarship-recommendation-platform.onrender.com/
<img width="1348" height="646" alt="image" src="https://github.com/user-attachments/assets/b25a1c1f-be88-4bd5-a0e2-6a80b907913e" />

An AI-powered web app that matches students to scholarships using **Sentence-BERT** semantic similarity. Built with FastAPI and deployed on Render.

---

## Features

- Semantic matching via SBERT embeddings (pre-computed, no GPU needed at runtime)
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
│       ├── index.html        # Input form
│       └── results.html      # Recommendation results
├── workspace/
│   ├── Models/sbert/         # Pre-computed embeddings (.pkl)
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
git clone https://github.com/yesahek/scholarship-recommendation.git
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

The test suite mocks the `.pkl` model files so no GPU or large files are required to run CI.

---

## Deployment on Render

### Auto-deploy on push (CI/CD)

After deploying, set up the GitHub secret so pushes to `main` trigger a Render redeploy:

Now every push to `main` will: **run tests → lint → deploy** (deploy only runs if tests pass).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Student input form |
| `POST` | `/recommend` | Returns top scholarship matches |
| `GET` | `/health` | Health check (used by Render) |

### Example `/health` response

```json
{ "status": "ok", "scholarships_loaded": 3 }
```

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
