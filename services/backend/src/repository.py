from sqlalchemy.orm import Session
from . import models, schemas


# Obtener todos los IA usages con paginación
def read_ia_usages(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.IAUsage).offset(skip).limit(limit).all()


def read_ia_usages_history(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.IAUsageHistory).offset(skip).limit(limit).all()

# Obtener una facultad específica por nombre
def get_faculty_by_name(db: Session, faculty: str):
    return db.query(models.IAUsage).filter(models.IAUsage.faculty == faculty).first()


# Crear un nuevo registro IA usage
def create_ia_usage(db: Session, ia_usage: schemas.IAUsageCreate):
    try:
        db_ia_usage = models.IAUsage(
            faculty=ia_usage.faculty,
            usage_percentage=ia_usage.usage_percentage,
            latitude=ia_usage.latitude,
            longitude=ia_usage.longitude
        )
        db.add(db_ia_usage)
        db.commit()
        db.refresh(db_ia_usage)
        return db_ia_usage
    except:
        db.rollback()
        return {"message": "An error occurred inserting the IA-usage."}, 500


# Crear datos históricos basados en el nombre de la facultad
def create_ia_usage_history(db: Session, faculty: str, history: schemas.IAUsageHistoryCreate):
    # Obtener el ID del IA Usage asociado a la facultad
    ia_usage = get_faculty_by_name(db, faculty)
    if ia_usage:
        db_history = models.IAUsageHistory(
            usage_id=ia_usage.id,
            date=history.date,
            usage_percentage=history.usage_percentage
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history
    else:
        return None  # En caso de que la facultad no exista


# Eliminar un IA usage por nombre de facultad
def delete_ia_usage_by_faculty(db: Session, faculty: str):
    usage = get_faculty_by_name(db, faculty)
    if usage:
        db.delete(usage)
        db.commit()
        return True
    return False


# Eliminar datos históricos IA usage por ID
def delete_ia_usage_history(db: Session, history_id: int):
    history_record = db.query(models.IAUsageHistory).filter(models.IAUsageHistory.id == history_id).first()
    if history_record:
        db.delete(history_record)
        db.commit()
        return True
    return False


# Actualizar porcentaje de uso para una facultad específica
def update_ia_usage_percentage(db: Session, faculty: str, usage_percentage: float, longitude: float, latitude:float):
    usage = get_faculty_by_name(db, faculty)
    if usage:
        usage.usage_percentage = usage_percentage
        usage.longitude = longitude
        usage.latitude = latitude
        db.commit()
        db.refresh(usage)
        return usage
    return None


# Obtener todos los datos históricos para una facultad específica
def get_historical_data_by_faculty(db: Session, faculty: str):
    usage = get_faculty_by_name(db, faculty)
    if usage:
        return db.query(models.IAUsageHistory).filter(models.IAUsageHistory.usage_id == usage.id).all()
    return None


# Obtener lista de todas las facultades
def get_all_faculties(db: Session):
    return [record.faculty for record in db.query(models.IAUsage).distinct(models.IAUsage.faculty).all()]


# Obtener todos los datos históricos para todas las facultades
def get_all_historical_data(db: Session):
    return db.query(models.IAUsageHistory).all()