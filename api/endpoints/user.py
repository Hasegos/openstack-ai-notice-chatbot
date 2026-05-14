# api/endpoints/user.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
def register():
    return {"message": "register"}

@router.post("/login")
def login():
    return {"message": "login"}