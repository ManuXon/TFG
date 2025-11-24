from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import visualizations
from src.routers import auth as auth_router

app = FastAPI(title="MapAI API")

ALLOWED_ORIGINS = [
    "http://localhost:8050",
    "http://127.0.0.1:8050",
    # add your prod domain(s) here, e.g. "https://mapai.ub.edu"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(visualizations.router)

@app.get("/")
def root():
    return {"message": "Backend running successfully!"}
