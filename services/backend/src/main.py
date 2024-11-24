from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import models, repository
from . import schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)  # Creem la base de dades amb els models definits

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.mount("/static", StaticFiles(directory="services/frontend/dist/static"), name="static")
# templates = Jinja2Templates(directory="services/frontend/dist")


# @app.get("/")
# async def serve_index(request: Request):
# return templates.TemplateResponse("index.html", {"request": request})


# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ia-usages/", response_model=List[schemas.IAUsage])
def read_ia_usages(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return repository.read_ia_usages(skip=skip, limit=limit, db=db)


@app.get("/ia-usages-history/", response_model=List[schemas.IAUsageHistory])
def read_ia_usages_history(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return repository.read_ia_usages_history(skip=skip, limit=limit, db=db)


@app.post("/ia-usage/", response_model=schemas.IAUsage)
def create_ia_usage(ia_usage: schemas.IAUsageCreate, db: Session = Depends(get_db)):
    db_ia_usage = repository.get_faculty_by_name(db, faculty=ia_usage.faculty)
    if db_ia_usage:
        raise HTTPException(status_code=400, detail="Faculty already Exists, Use put for updating")
    else:
        return repository.create_ia_usage(db=db, ia_usage=ia_usage)


# Delete an IA usage record by faculty name
@app.delete("/ia-usage/{faculty_name}")
def delete_ia_usage(faculty_name: str, db: Session = Depends(get_db)):
    deleted = repository.delete_ia_usage_by_faculty(db=db, faculty=faculty_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return {"message": f"Deleted IA usage record for faculty {faculty_name}"}


# Delete an IA usage history record by ID
@app.delete("/ia-usage-history/{history_id}")
def delete_ia_usage_history(history_id: int, db: Session = Depends(get_db)):
    deleted = repository.delete_ia_usage_history(db=db, history_id=history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History record not found")
    return {"message": f"Deleted IA usage history record with ID {history_id}"}


# Update usage percentage by faculty name
@app.put("/ia-usage/{faculty_name}", response_model=schemas.IAUsage)
def update_ia_usage(faculty_name: str, usage_percentage: float, latitude: float, longitude: float, db: Session = Depends(get_db)):
    updated_ia_usage = repository.update_ia_usage_percentage(db=db, faculty=faculty_name,
                                                             usage_percentage=usage_percentage, longitude=longitude, latitude=latitude)
    if not updated_ia_usage:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return updated_ia_usage


# Crear un nuevo registro histórico basado en el nombre de la facultad
@app.post("/ia-usage-history/{faculty_name}", response_model=schemas.IAUsageHistory)
def create_ia_usage_history(faculty_name: str, history: schemas.IAUsageHistoryCreate, db: Session = Depends(get_db)):
    created_history = repository.create_ia_usage_history(db=db, faculty=faculty_name, history=history)
    if not created_history:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return created_history


# Get all historical usage data for a given faculty
@app.get("/ia-usage-history/{faculty_name}", response_model=List[schemas.IAUsageHistory])
def get_ia_usage_history_by_faculty(faculty_name: str, db: Session = Depends(get_db)):
    history = repository.get_historical_data_by_faculty(db=db, faculty=faculty_name)
    if not history:
        raise HTTPException(status_code=404, detail="Faculty not found or no history available")
    return history


# Get the list of all faculties
@app.get("/faculties/", response_model=List[str])
def get_all_faculties(db: Session = Depends(get_db)):
    return repository.get_all_faculties(db=db)


# Get all historical usage data for all faculties
@app.get("/ia-usages-history/all/", response_model=List[schemas.IAUsageHistory])
def get_all_ia_usages_history(db: Session = Depends(get_db)):
    historical_data = repository.get_all_historical_data(db=db)
    if not historical_data:
        raise HTTPException(status_code=404, detail="No historical data available")
    return historical_data
