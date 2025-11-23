from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import visualizations

app = FastAPI()

# Allow frontend requests (Dash/React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:8050"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(visualizations.router)

@app.get("/")
def root():
    return {"message": "Backend running successfully!"}
