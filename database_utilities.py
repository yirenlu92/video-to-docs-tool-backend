from supabase import create_client, Client
import json

SUPABASE_URL = "https://nexxosgljmgeohuwgiyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5leHhvc2dsam1nZW9odXdnaXlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODI1NDYwODQsImV4cCI6MTk5ODEyMjA4NH0.Ydok308_dhUaqdCpsjkU32jphUEA4Jz5Dx-KHhVF9pE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_project(project_id: int, user_id: int, task_status: str, video_url: str, title: str, folder_name: str):
    response = supabase.table("projects").insert([
        {"project_id": str(project_id), "user_id": str(user_id), "task_status": task_status, "video_url": video_url, "title": title, "folder_name": folder_name}
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

def update_or_add_screenshot_in_database(project_id: int, index: int, screenshot_url: str, text: str, screenshot_id: int):

    # if the screenshot already exists, update it
    # else, add it

    response = supabase.table("screenshots").select("*").eq("project_id", project_id).eq("index", index).execute()
    if response and response.data and len(response.data) >= 1:
        update_response = supabase.table("screenshots").update({"screenshot_url": screenshot_url, "text": text}).eq("project_id", project_id).eq("index", index).execute()
    else:
        insert_response = supabase.table("screenshots").insert([
            {"project_id": str(project_id), "index": index, "screenshot_url": screenshot_url, "text": text}
        ]).execute()

def fetch_screenshot_row(project_id: int, index: int):
    response = supabase.table("screenshots").select("*").eq("project_id", project_id).eq("index", index).execute()

    print(response.data)

    assert len(response.data) >= 1
    return response.data[0]

def update_markdown_project_status(project_id: int, screenshot_urls: list):
    response = supabase.table("projects").update({"screenshot_urls": json.dumps(screenshot_urls)}).eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1

def update_error_message(project_id: int, error_message: str):
    response = supabase.table("projects").update({"task_error_message": error_message}).eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1


def insert_timestamps_and_text(project_id: int, texts: list, timestamps: list):
    
    # insert timestamps and text into the projects table of the database
    response = supabase.table("projects").update({"timestamps": json.dumps(timestamps), "texts": json.dumps(texts), "task_status": 1}).eq("project_id", project_id).execute()

    print(response.data)

    assert len(response.data) >= 1

def insert_new_screenshot_in_screenshots_table(project_id: int, text: str, timestamp: str, index: int):

    # insert timestamps and text into the projects table of the database
    response = supabase.table("screenshots").insert({"project_id": str(project_id), "index": index, "timestamp": timestamp, "text": text, "annotations": [], "zoom_pan_settings": json.dumps({"x": 0, "y": 0, "zoom": 1})}).execute()
    
    print ("response from inserting new screenshot in screenshots table")

    print(response)

    assert len(response.data) >= 1