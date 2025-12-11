from pydantic import BaseModel


class Token(BaseModel):
    """Schema for the JWT response body sent to the client."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for the payload data inside the JWT."""
    # This ID links the token back to the User in the database
    user_id: int
