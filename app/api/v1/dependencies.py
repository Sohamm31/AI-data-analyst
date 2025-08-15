from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import database
from app.models import user as user_model
from app.schemas import token as token_schema

# This tells FastAPI where the client should go to get a token.
# It points to the /token endpoint we created in the auth router.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Dependency function to be used in protected endpoints.
    1. It takes the token from the request's Authorization header.
    2. It decodes and verifies the JWT token.
    3. It fetches the user from the database based on the email in the token.
    4. It returns the full user object, making it available in the endpoint.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using your secret key and algorithm
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub") # "sub" is the standard claim for the subject (user's email)
        if email is None:
            raise credentials_exception
        token_data = token_schema.TokenData(email=email)
    except JWTError:
        # This catches any errors during decoding (e.g., expired token, invalid signature)
        raise credentials_exception
    
    # Fetch the user from the database
    user = db.query(user_model.User).filter(user_model.User.email == token_data.email).first()
    if user is None:
        # This handles the case where the user might have been deleted after the token was issued
        raise credentials_exception
    
    return user
