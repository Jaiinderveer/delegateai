from database import DBHelper
from config import openai_client
import datetime
import json

def get_db():
    db = DBHelper()
    db.select_collection("tasks")
    return db
db_helper = get_db()

def save_task(task):
     # Adding 2 more keys in task
     task['status'] = 'PENDING'
     task['created_at'] = datetime.datetime.now()
     db_helper.save(task)
     result = (
        f"Task saved successfully as **pending** \n\n",
        f"**Action** {task['action']} \n\n",
        f"**Title** {task['title']} \n\n",
        f"**Description** {task['description']} \n\n"
    )

     return result

def list_tasks():
    documents = db_helper.retrieve()

    if len(documents) == 0:
        return "No tasks found."

    text = ""

    for i, task in enumerate(documents, start=1):
        text += (
            f"Task {i}\n\n"
            f"Title: {task['title']}\n\n"
            f"Description: {task['description']}\n\n"
            f"Action: {task['action']}\n\n"
            f"Contact: {task['contact_name']}\n\n"
            f"Phone: {task['contact_phone']}\n\n"
            f"Status: {task['status']}\n\n"
            f"Created At: {task['created_at']}\n\n"
            f"\n{'='*45}\n\n"
        )

    return text

def update_task(title,
                description=None,
                action=None,
                contact_name=None,
                contact_phone=None):

    condition = {
        "title": title
    }

    updated_document = {}

    if description:
        updated_document["description"] = description

    if action:
        updated_document["action"] = action

    if contact_name:
        updated_document["contact_name"] = contact_name

    if contact_phone:
        updated_document["contact_phone"] = contact_phone

    result = db_helper.update(condition, updated_document)

    if result.matched_count == 0:
        return "Task not found."

    return "Task updated successfully."
def delete_task(title):

    result = db_helper.delete({
        "title": title
    })

    if result.deleted_count == 0:
        return "Task not found."

    return "Task deleted successfully."

# 2. Define a list of callable tools for the model
tools = [
    {
        "type": "function",
        "name": "save_task",
        "description": "Save the task in MongoDB Atlas which a user will write",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the Task",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the Task",
                },
                "action": {
                    "type": "string",
                    "enum": ["call","email","message","other"],
                    "description": "Action of the Task can be call, message or email",
                },
                
            },
            "required": ["title", "description", "action"],
        },
    },
    {
        "type": "function",
        "name": "list_tasks",
        "description": "Retrieve and display every task stored in MongoDB.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "type": "function",
        "name": "delete_task",
        "description": "Delete the task whose title matches the user's request.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type":"string"
                }
            },
            "required":["title"]
        }
    },
    {
        "type": "function",
        "name": "update_task",
        "description": ("Update an existing task. "
    "Only modify the fields explicitly mentioned by the user. "
    "Leave all other fields unchanged."),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                },
                "action": {
                    "type": "string"
                },
                
            },
            "required": [
                "title"
            ]
        }
    }
]
def agentic_save(input_list):
    
    response = openai_client.responses.create(
        model="gpt-4o-mini",
        tools=tools,
        input=input_list,
    )  

    function_call = None
    assistant_text = ""

    for item in response.output:

        if item.type == "function_call":
            function_call = item
            break

        elif item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    assistant_text += content.text
    result = "Sorry, I couldn't understand your request."
    if function_call:

        function_name = function_call.name
        arguments = json.loads(function_call.arguments)

        if function_name == "save_task":
            arguments['user_original_text'] = input_list[0]['content']
            result = save_task(arguments)

        elif function_name == "update_task":
            result = update_task(
    title=arguments["title"],
    description=arguments.get("description"),
    action=arguments.get("action"),
    contact_name=arguments.get("contact_name"),
    contact_phone=arguments.get("contact_phone")
    )

        elif function_name == "delete_task":
            result = delete_task(arguments["title"])

        elif function_name == "list_tasks":
            result = list_tasks()

    else:
        result = assistant_text
    return result
