from pydantic import BaseModel, Field

# Schema for the expected login payload
class LoginUser(BaseModel):
    """
    Schema for a user attempting to log in or register.
    """
    username: str = Field(..., example="jane.doe")
    password: str = Field(..., example="securepassword123")


# Schema for the successful token response
class Token(BaseModel):
    """
    Schema for the JWT token returned upon successful authentication.
    """
    access_token: str
    token_type: str = "bearer"