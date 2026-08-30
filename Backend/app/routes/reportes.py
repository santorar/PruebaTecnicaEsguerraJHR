from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import LibroMayorRequest, LibroMayorResponse
from sqlalchemy.orm import Session
from app.services import reportes as reportes_service

router = APIRouter(prefix="/libro_mayor", tags=["libro_mayor"])

@router.post("/", response_model=list[LibroMayorResponse])
def get_libro_mayor(request: LibroMayorRequest, db: Session = Depends(get_db)):
    return reportes_service.get_libro_mayor(db, request)