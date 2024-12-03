from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import firestore
from typing import Optional

app = FastAPI()

# Initialize Firestore DB
db = firestore.Client(database='test')


class User(BaseModel):
    username: str
    email: str
    project_ref: str
    role: str


class UpdateUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    project_ref: Optional[str] = None
    role: Optional[str] = None


@app.post("/add_users")
async def create_user(user: User):
    project_ref = db.collection('projects').document(user.project_ref)
    project = project_ref.get()
    if not project.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    user_ref = db.collection('users').document()
    user_data = user.dict()
    user_data['project_ref'] = project_ref
    user_ref.set(user_data)
    return {"id": user_ref.id, **user.dict()}


@app.get("/get_users")
async def get_users():
    projects_ref = db.collection('projects')
    project_docs = projects_ref.stream()
    result = []

    for project_doc in project_docs:
        project_data = project_doc.to_dict()
        project_id = project_doc.id
        project_name = project_data.get('name', 'Unnamed Project')

        users_ref = db.collection('users').where(
            'project_ref', '==', db.collection('projects').document(project_id)
        )
        user_docs = users_ref.stream()
        users = []
        for user_doc in user_docs:
            user_data = user_doc.to_dict()
            print(user_data)
            del user_data['project_ref']
            users.append({"id": user_doc.id, **user_data})

        result.append({
            "id": project_id,
            "name": project_name,
            "users": users
        })

    return result


@app.patch("/update_users/{user_id}")
async def update_user(user_id: str, user: UpdateUser):
    user_ref = db.collection('users').document(user_id)
    user_data = {k: v for k, v in user.dict().items() if v is not None}
    if not user_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if project_ref_id := user_data.get('project_ref'):
        project_ref = db.collection('projects').document(project_ref_id)
        project = project_ref.get()
        if not project.exists:
            raise HTTPException(status_code=404, detail="Project not found")
    user_ref.update(user_data)
    return {"id": user_id, **user_data}


@app.delete("/delete_users/{user_id}")
async def delete_user(user_id: str):
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.delete()
    return {"message": "User deleted successfully"}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
