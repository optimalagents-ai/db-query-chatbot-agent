import os
import json
import requests
from fastapi import FastAPI, Request, Form, HTTPException, Header
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware

from database import get_database_schema
from ai_service import process_chat_message, reset_engine

# Initialize FastAPI app
app = FastAPI(title="AI Database Query Chatbot")

# Set up templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent_id = os.getenv("AGENT_ID")
api_key = os.getenv("CREATOR_API_KEY")

def check_agent_run(user_token, api_key=api_key, agent_id=agent_id):
    url = "https://optimalagents.ai/check-users-credits"
    headers = {"User-Token": user_token}
    data = {"api_key": api_key, "agent_id": agent_id}
    response = requests.post(url, json=data, headers=headers)
    print(response.text)
    result = response.json()
    print(result)

    if result.get("status") == "allowed":
        print("Agent execution permitted.")
    else:
        print(f"Error: {result.get('message')}")
    return result

# Store chat history in memory (in a production app, you'd use a database)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(request: Request, message: str = Form(...), session_id: str = Form(...), user_token: Optional[str] = Header(None)):
    """Process a chat message and return a response"""
    if not user_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized. No User token provided."})
    print(user_token)
    resp = check_agent_run(user_token, api_key, agent_id)
    if resp.get("status") == "allowed":
        authorized = True
        enough_credits = True
    else:
        authorized = False
        enough_credits = False
    if not authorized or not enough_credits:
        return JSONResponse(status=403, content={"error": "Unauthorized or insufficient credits"})
    
    print(f"Received message: {message} from session: {session_id}")
    # Initialize chat history for this session if it doesn't exist
    try:
        # Get database schema

        response = process_chat_message(message)
        if response["type"] == "error":
            # Add error message to chat history
            return JSONResponse(content={
                "message": response["content"],
                "type": "text",
            })
        
        # Execute the SQL query
        try:
            
            # Generate explanation
            # explanation = explain_sql_query(response["sql_query"])
            content = response["content"]
            # Create response data
            response_data = {
                "message": content,
                "type":"results",
                "results": response["sql_result"],
                "sql": response["sql_query"],

                # "explanation": explanation
            }
            
            # Add assistant message to chat history
            return JSONResponse(content={
                "message": response_data,
                "type": "results",
            })
            
        except Exception as e:
            error_message = f"Error executing query: {str(e)}"
            return JSONResponse(content={
                "message": error_message,
                "type": "text",
            }, status_code=403)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/schema")
async def get_schema():
    """Get the database schema"""
    try:
        schema = get_database_schema()
        return JSONResponse(content={"schema": schema})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/db_update")
async def update_db_settings(request: Request, user_token: Optional[str] = Header(None)):
    """Update database connection settings"""
    try:
        form = await request.form()
        # Extract database settings from form
        db_settings = {
            "dbType" : form.get("dbType").lower(),
            "host": form.get("dbHost"),
            "port": form.get("dbPort"),
            "database": form.get("dbName"),
            "user": form.get("dbUsername"),
            "password": form.get("dbPassword"),
            "dbUrl": form.get("dbURL")
        }
        
        print(db_settings)
        # Create database URL from settings
        if db_settings['dbUrl'] and db_settings['dbUrl'] != "":
            db_url = db_settings['dbUrl']        
        elif db_settings["dbType"] == "postgresql":
            db_url = f"postgresql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['database']}"
        elif db_settings["dbType"] == "mysql":
            db_url = f"mysql+pymysql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['database']}"
        elif db_settings["dbType"] == "sqlite":
            db_url = f"sqlite:///{db_settings['database']}"
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Unsupported database type"
            })
        print(db_url)
        try:
           new_engine = reset_engine(db_url)
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "message": f"Failed to connect to the database: {e}"
            }, status_code=400)
        
        
        # Update database connection settings
        # Implementation would depend on your database connection handling
        
        return JSONResponse(content={
            "success": True,
            "message": "Database settings updated successfully"
        })
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"{e}"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)