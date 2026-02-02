from pydantic import BaseModel


class FirebaseUser(BaseModel):
    uid: str
    email: str
    name: str
