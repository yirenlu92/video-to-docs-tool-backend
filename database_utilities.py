from supabase import create_client, Client
import json

SUPABASE_URL = "https://nexxosgljmgeohuwgiyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5leHhvc2dsam1nZW9odXdnaXlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODI1NDYwODQsImV4cCI6MTk5ODEyMjA4NH0.Ydok308_dhUaqdCpsjkU32jphUEA4Jz5Dx-KHhVF9pE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_project(project_id: int, task_status: str, video_url: str, title: str, folder_name: str):
    response = supabase.table("projects").insert([
        {"project_id": str(project_id), "task_status": task_status, "video_url": video_url, "title": title, "folder_name": folder_name}
    ]).execute()

    print(response.data)

    assert len(response.data) >= 1

def fetch_project_data(project_id: int):
    response = supabase.table("projects").select("*").eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1
    return response.data[0]
    

def update_project_status(project_id: int, task_status: str):
    response = supabase.table("projects").update({"task_status": task_status}).eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1


def insert_timestamps_and_text(project_id: int, texts: list, timestamps: list):
    
    # insert timestamps and text into the projects table of the database
    response = supabase.table("projects").update({"timestamps": json.dumps(timestamps), "texts": json.dumps(texts)}).eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1