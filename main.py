from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List
import nh3
import os
from dotenv import load_dotenv

from database import CensusTract, get_db

load_dotenv()

app = FastAPI(title="IGS API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-for-real-use")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class User(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class CensusTractModel(BaseModel):
    census_tract: str = Field(..., max_length=11)
    inclusion_score: float = Field(..., ge=0, le=100)
    growth_score: float = Field(..., ge=0, le=100)
    economy_score: float = Field(..., ge=0, le=100)
    community_score: float = Field(..., ge=0, le=100)

    class Config:
        from_attributes = True  # Pydantic v2 / ORM mode equivalent


# Simulated user database (demo only – not for production)
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("securepassword123"),
    }
}


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decode JWT and return current username if valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in users_db:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that issues JWT access tokens.
    """
    user = users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/tracts/", response_model=List[CensusTractModel])
async def get_tracts(
    current_user: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Return all census tracts from the database (JWT protected).
    """
    tracts = db.query(CensusTract).all()
    # Sanitize string fields with nh3
    return [
        CensusTractModel(
            census_tract=nh3.clean(t.census_tract),
            inclusion_score=t.inclusion_score,
            growth_score=t.growth_score,
            economy_score=t.economy_score,
            community_score=t.community_score,
        )
        for t in tracts
    ]


@app.get("/tracts/{census_tract}", response_model=CensusTractModel)
async def get_single_tract(
    census_tract: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Challenge (FastAPI / Dictionary Processing):

    - Fetch a single census tract.
    - Store result in a Python dictionary before returning.
    """
    tract = (
        db.query(CensusTract)
        .filter(CensusTract.census_tract == census_tract)
        .first()
    )

    if tract is None:
        raise HTTPException(status_code=404, detail="Census tract not found")

    # Dictionary processing challenge
    tract_dict = {
        "census_tract": nh3.clean(tract.census_tract),
        "inclusion_score": tract.inclusion_score,
        "growth_score": tract.growth_score,
        "economy_score": tract.economy_score,
        "community_score": tract.community_score,
    }

    # Pydantic will convert this dict into the response model
    return tract_dict


@app.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    """
    Challenge (JWT):

    - Simple endpoint to return the current authenticated username.
    """
    return {"username": current_user}
