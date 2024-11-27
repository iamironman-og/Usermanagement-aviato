from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import firestore
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText

app = FastAPI()

# Initialize Firestore DB
db = firestore.Client(database='test')


class User(BaseModel):
    username: str
    email: str
    project_id: int


class UpdateUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    project_id: Optional[int] = None


@app.post("/add_users")
async def create_user(user: User):
    print(user.dict())
    user_ref = db.collection('users').document()
    user_ref.set(user.dict())
    return {"id": user_ref.id, **user.dict()}


@app.get("/get_users")
async def get_users():
    users_ref = db.collection('users')
    docs = users_ref.stream()
    users = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return users


@app.patch("/update_users/{user_id}")
async def update_user(user_id: str, user: UpdateUser):
    user_ref = db.collection('users').document(user_id)
    user_data = {k: v for k, v in user.dict().items() if v is not None}
    if not user_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    user_ref.update(user_data)
    return {"id": user_id, **user_data}


@app.delete("/delete_users/{user_id}")
async def delete_user(user_id: str):
    user_ref = db.collection('users').document(user_id)
    user_ref.delete()
    return {"message": "User deleted successfully"}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
