import os
from database import (
    DBHelper, get_dashboard_metrics, get_calls_query, get_tasks_query
)
from config import openai_client
import datetime
import json
import re
import string

# Graceful fallback for fuzzy matching
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

# --- 1. Database Connections ---
def get_db():
    db = DBHelper()
    db.select_collection("tasks")
    return db
db_helper = get_db()

def get_contact_db():
    db = DBHelper()
    db.select_collection("contacts")
    return db
contact_db_helper = get_contact_db()


# --- 2. Date Guardrail Helper ---
def verify_date_preset(date_preset, user_query):
    """Strips hallucinated date parameters unless explicitly typed in raw message."""
    if not date_preset or not user_query:
        return None
        
    query_lower = user_query.lower()
    if date_preset == "today" and "today" not in query_lower:
        return None
    if date_preset == "yesterday" and "yesterday" not in query_lower:
        return None
    if date_preset == "this_week" and "week" not in query_lower:
        return None
        
    return date_preset


# --- 3. Advanced Natural Matching Engine ---
def normalize_text(text: str) -> str:
    if not text: return ""
    text = str(text).lower().translate(str.maketrans('', '', string.punctuation))
    return " ".join(text.split())

def resolve_entity(db_helper_instance, field_name: str, search_query: str):
    if not search_query or not search_query.strip(): return None, "No search query provided."
    search_norm = normalize_text(search_query)
    search_words = set(search_norm.split())
    if not search_words: return None, "Invalid search query."

    regex_pattern = "|".join(re.escape(w) for w in search_words)
    condition = {field_name: {"$regex": regex_pattern, "$options": "i"}}
    candidates = db_helper_instance.retrieve(condition)

    if not candidates: return None, f"No matching {field_name} found."

    exact_matches = []
    subset_matches = []
    fuzzy_matches = []

    for doc in candidates:
        target_raw = doc.get(field_name, "")
        target_norm = normalize_text(target_raw)
        
        if search_norm == target_norm:
            exact_matches.append(target_raw)
            continue
            
        target_words = set(target_norm.split())
        if search_words.issubset(target_words):
            subset_matches.append(target_raw)
            continue
            
        if HAS_RAPIDFUZZ:
            score = fuzz.partial_ratio(search_norm, target_norm)
            if score >= 80: fuzzy_matches.append((target_raw, score))
        else:
            matcher = difflib.SequenceMatcher(None, search_norm, target_norm)
            if matcher.quick_ratio() >= 0.75: fuzzy_matches.append((target_raw, matcher.quick_ratio()))

    if len(exact_matches) == 1: return exact_matches[0], None
    if len(exact_matches) > 1: return None, f"Found multiple exact matches: **{', '.join(exact_matches)}**. Please clarify."
        
    if len(subset_matches) == 1: return subset_matches[0], None
    if len(subset_matches) > 1: return None, f"Found multiple partial matches: **{', '.join(subset_matches)}**. Please clarify."
        
    if fuzzy_matches:
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        best_score = fuzzy_matches[0][1]
        top_candidates = [m[0] for m in fuzzy_matches if m[1] >= best_score - 2]
        
        if len(top_candidates) == 1: return top_candidates[0], None
        else: return None, f"Found similar matches: **{', '.join(top_candidates)}**. Please clarify."
            
    return None, f"No matching {field_name} found."


# --- 4. Task & Call Methods ---
def save_task(task):
     task['status'] = 'PENDING'
     task['created_at'] = datetime.datetime.now()
     task['title'] = " ".join(task['title'].strip().split())
     task['contact_name'] = " ".join(task['contact_name'].strip().split())
     db_helper.save(task)
     return (
        f"Task saved successfully as **pending** \n\n"
        f"**Action** {task['action']} \n\n"
        f"**Title** {task['title']} \n\n"
        f"**Contact Name** {task['contact_name']} \n\n"
        f"**Description** {task['description']} \n\n"
    )

def list_tasks():
    documents = db_helper.retrieve()
    if len(documents) == 0: return "No tasks found."
    text = ""
    for i, task in enumerate(documents, start=1):
        text += (
            f"Task {i}\n\nTitle: {task['title']}\n\nDescription: {task['description']}\n\n"
            f"Action: {task['action']}\n\nContact: {task['contact_name']}\n\nStatus: {task['status']}\n\n"
            f"Created At: {task['created_at']}\n\n\n{'='*45}\n\n"
        )
    return text

def update_task(title, description=None, action=None, contact_name=None):
    real_title, error_msg = resolve_entity(db_helper, "title", title)
    if error_msg: return error_msg

    condition = {"title": real_title}
    updated_document = {}
    if description: updated_document["description"] = description
    if action: updated_document["action"] = action.lower()
    if contact_name: updated_document["contact_name"] = " ".join(contact_name.strip().split())

    result = db_helper.update(condition, updated_document)
    if result.matched_count == 0: return "Task not found."
    return f"Task **'{real_title}'** updated successfully."

def delete_task(title):
    real_title, error_msg = resolve_entity(db_helper, "title", title)
    if error_msg: return error_msg

    condition = {"title": real_title}
    result = db_helper.delete(condition)
    if result.deleted_count == 0: return "Task not found."
    return f"Task **'{real_title}'** deleted successfully."

def fetch_filtered_tasks(status=None, date_preset=None, action=None):
    documents = get_tasks_query(status, date_preset, action)
    if not documents:
        return f"No tasks found matching your criteria."

    text = f"**Found {len(documents)} task(s):**\n\n"
    for i, task in enumerate(documents, start=1):
        created_str = task.get('created_at').strftime("%Y-%m-%d %H:%M") if task.get('created_at') else "N/A"
        text += (
            f"**{i}. {task.get('title', 'Untitled')}**\n"
            f"- **Status**: {task.get('status', 'N/A')}\n"
            f"- **Action**: {task.get('action', 'N/A')} to {task.get('contact_name', 'N/A')}\n"
            f"- **Date**: {created_str}\n\n"
        )
    return text

def fetch_call_history(call_status_intent=None, date_preset=None):
    """Executes call details query using Canonical Analytics Service."""
    documents = get_calls_query(intent_status=call_status_intent, date_preset=date_preset)
    
    if not documents:
        return f"No call history found matching the criteria."

    text = f"**Found {len(documents)} call(s):**\n\n"
    for i, task in enumerate(documents, start=1):
        created_str = task.get('created_at').strftime("%Y-%m-%d %H:%M") if task.get('created_at') else "N/A"
        
        text += (
            f"**{i}. Call: {task.get('title', 'Untitled')}**\n"
            f"- **Contact**: {task.get('contact_name', 'N/A')}\n"
            f"- **System Status**: {task.get('status', 'N/A')}\n"
            f"- **Date**: {created_str}\n"
        )
        if 'twilio_status' in task and task['twilio_status']:
            text += f"- **Twilio Outcome**: {task['twilio_status']}\n"
        if 'error' in task and task['error']:
            text += f"- **Permanent Error**: {task['error']}\n"
        if 'last_error' in task and task['last_error']:
            text += f"- **Last Retry Error**: {task['last_error']}\n"
        if 'retry_count' in task and task['retry_count'] > 0:
            text += f"- **Retries Made**: {task['retry_count']}\n"
            
        text += "\n"
        
    return text


def save_contact(name, phone):
    clean_name = " ".join(name.strip().split())
    contact_db_helper.save({"name": clean_name, "phone": phone.strip()})
    return f"✅ Contact **{clean_name.title()}** saved successfully with phone `{phone.strip()}`."

def update_contact(name, phone):
    real_name, error_msg = resolve_entity(contact_db_helper, "name", name)
    if error_msg: return error_msg

    condition = {"name": real_name}
    result = contact_db_helper.update(condition, {"phone": phone.strip()})
    if result.matched_count == 0: return f"❌ Contact **{real_name}** not found."
    return f"✅ Contact **{real_name}** updated successfully with new phone `{phone.strip()}`."

def delete_contact(name):
    real_name, error_msg = resolve_entity(contact_db_helper, "name", name)
    if error_msg: return error_msg

    condition = {"name": real_name}
    result = contact_db_helper.delete(condition)
    if result.deleted_count == 0: return f"❌ Contact **{real_name}** not found."
    return f"🗑️ Contact **{real_name}** deleted successfully."

def search_contacts(name=None):
    if name and name.strip():
        real_name, error_msg = resolve_entity(contact_db_helper, "name", name)
        if error_msg: return error_msg
        condition = {"name": real_name}
    else:
        condition = {}

    documents = contact_db_helper.retrieve(condition)
    if not documents: return "No contacts found."
    text = f"**Found {len(documents)} contact(s):**\n\n"
    for c in documents:
        text += f"- **{c.get('name', 'Unknown').title()}**: `{c.get('phone', 'N/A')}`\n"
    return text


# --- 5. Tool Definitions ---
tools = [
    {
        "type": "function",
        "name": "save_task",
        "description": "Save a new task.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "contact_name": {"type": "string"},
                "action": {"type": "string", "enum": ["call","email","message","other"]},
            },
            "required": ["title", "description", "action", "contact_name"],
        },
    },
    {
        "type": "function",
        "name": "list_tasks",
        "description": "Retrieve and display ALL tasks stored in MongoDB without filtering.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "type": "function",
        "name": "delete_task",
        "description": "Delete a task by title.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"]
        }
    },
    {
        "type": "function",
        "name": "update_task",
        "description": "Update an existing task.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "action": {"type": "string"},
                "contact_name": {"type": "string"}
            },
            "required": ["title"]
        }
    },
    {
        "type": "function",
        "name": "fetch_filtered_tasks",
        "description": "Fetch generic TASKS. Do NOT use this tool for calls.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["PENDING", "COMPLETED", "FAILED"]},
                "date_preset": {"type": "string", "enum": ["today", "yesterday"]}
            }
        }
    },
    {
        "type": "function",
        "name": "fetch_call_history",
        "description": "Fetch CALLS specifically (e.g. 'which call failed', 'show failed calls', 'call history'). ALWAYS execute immediately without asking for clarification.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_status_intent": {
                    "type": "string", 
                    "enum": ["FAILED", "COMPLETED", "PENDING", "ALL"],
                    "description": "High level intent: FAILED for failed calls, COMPLETED for completed calls, PENDING for pending/calling calls, ALL for all calls."
                },
                "date_preset": {
                    "type": "string", 
                    "enum": ["today", "yesterday", "this_week"],
                    "description": "ONLY pass if user explicitly typed 'today', 'yesterday', or 'this_week' in their input."
                }
            }
        }
    },
    {
        "type": "function",
        "name": "save_contact",
        "description": "Save a new contact.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "phone": {"type": "string"}},
            "required": ["name", "phone"]
        }
    },
    {
        "type": "function",
        "name": "update_contact",
        "description": "Update an existing contact.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "phone": {"type": "string"}},
            "required": ["name", "phone"]
        }
    },
    {
        "type": "function",
        "name": "delete_contact",
        "description": "Delete a contact.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
    },
    {
        "type": "function",
        "name": "search_contacts",
        "description": "Search for a specific contact.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
    },
    {
        "type": "function",
        "name": "analyze_dashboard_data",
        "description": "Fetch aggregated dashboard analytics and numbers (counts, totals, success rates). Use this ONLY when asked 'how many', 'summarize', or for broad statistics.",
        "parameters": {"type": "object", "properties": {}}
    }
]


# --- 6. Intent Classifier ---
FAST_GREETING_REGEX = re.compile(
    r"^(hi|hello|hey|good morning|good evening|good afternoon|thanks|thank you|bye|how are you\??|who are you\??|what can you do\??|help|nice to meet you)[\s!.]*$",
    re.IGNORECASE
)

def classify_intent(text: str) -> str:
    if FAST_GREETING_REGEX.match(text.strip()): return "CASUAL"

    prompt = (
        "Classify the user message into exactly ONE category:\n"
        "CASUAL: Greetings, small talk, pleasantries.\n"
        "CALLS: Questions specifically about phone calls, call history, failed calls, who didn't answer, call status.\n"
        "TASKS: Questions about generic tasks, pending tasks, deleting/updating tasks.\n"
        "CONTACTS: Questions about managing, creating, or searching contacts.\n"
        "DASHBOARD: Questions asking for analytics, summaries, aggregated counts, 'how many', success rates.\n"
        "UNRELATED: Unrelated programming, math, general knowledge.\n\n"
        f"Message: '{text}'\n"
        "Category (CASUAL, CALLS, TASKS, CONTACTS, DASHBOARD, or UNRELATED):"
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        cat = response.choices[0].message.content.strip().upper()
        if "CASUAL" in cat: return "CASUAL"
        elif "CALLS" in cat: return "CALLS"
        elif "TASKS" in cat: return "TASKS"
        elif "CONTACTS" in cat: return "CONTACTS"
        elif "DASHBOARD" in cat: return "DASHBOARD"
        elif "UNRELATED" in cat: return "UNRELATED"
        return "CALLS" if "CALL" in text.upper() else "TASKS"
    except Exception:
        return "CALLS" if "CALL" in text.upper() else "TASKS"


# --- 7. AI Execution Engine ---
def agentic_save(input_list):
    user_query = next((item['content'] for item in reversed(input_list) if item['role'] == 'user'), "")
    intent = classify_intent(user_query) if user_query else "TASKS"

    if intent == "UNRELATED":
        return "I'm DelegateAI, your AI assistant for this platform. I can help you manage tasks, contacts, phone calls, schedules, and analytics, but I can't assist with unrelated programming or general knowledge requests."

    system_msg_content = (
        "You are DelegateAI, a specialized AI assistant for a Call Management Platform. "
        "FORMATTING RULE: Never use LaTeX formatting like \\[ ... \\] or \\( ... \\) for math. "
        "Always present numbers, percentages, and simple calculations in plain text and standard Markdown. "
    )
    
    if intent == "CALLS":
        system_msg_content += "CRITICAL INSTRUCTION: The user is asking about CALLS. You MUST call 'fetch_call_history' immediately. NEVER ask the user for clarification or timeframes."
    elif intent == "TASKS":
        system_msg_content += "The user is asking about TASKS. Use the generic task management tools."
    elif intent == "DASHBOARD":
        system_msg_content += "The user is asking about DASHBOARD analytics or aggregated counts. Use the 'analyze_dashboard_data' tool."
    elif intent == "CONTACTS":
        system_msg_content += "The user is asking about CONTACTS. Use contact management tools."
    elif intent == "CASUAL":
        system_msg_content += "The user is making casual conversation. Introduce yourself warmly and state your capabilities."

    system_msg = {"role": "system", "content": system_msg_content}

    if input_list and input_list[0].get("role") != "system":
        input_list.insert(0, system_msg)
    else:
        input_list[0] = system_msg

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
            arguments['user_original_text'] = user_query
            result = save_task(arguments)
        elif function_name == "update_task":
            result = update_task(
                title=arguments["title"],
                description=arguments.get("description"),
                action=arguments.get("action"),
                contact_name=arguments.get("contact_name")
            )
        elif function_name == "delete_task":
            result = delete_task(arguments["title"])
        elif function_name == "list_tasks":
            result = list_tasks()
        elif function_name == "fetch_filtered_tasks":
            safe_date = verify_date_preset(arguments.get("date_preset"), user_query)
            result = fetch_filtered_tasks(
                status=arguments.get("status"),
                date_preset=safe_date,
                action=arguments.get("action")
            )
        elif function_name == "fetch_call_history":
            safe_date = verify_date_preset(arguments.get("date_preset"), user_query)
            result = fetch_call_history(
                call_status_intent=arguments.get("call_status_intent"),
                date_preset=safe_date
            )
        elif function_name == "save_contact":
            result = save_contact(name=arguments["name"], phone=arguments["phone"])
        elif function_name == "update_contact":
            result = update_contact(name=arguments["name"], phone=arguments["phone"])
        elif function_name == "delete_contact":
            result = delete_contact(name=arguments["name"])
        elif function_name == "search_contacts":
            result = search_contacts(name=arguments.get("name"))
        elif function_name == "analyze_dashboard_data":
            summary_json = json.dumps(get_dashboard_metrics())
            tool_call_id = getattr(function_call, 'id', 'call_dash_001')
            
            assistant_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": function_call.arguments
                        }
                    }
                ]
            }
            
            tool_msg = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": function_name,
                "content": summary_json
            }
            
            msg_list = input_list + [assistant_msg, tool_msg]
            
            follow_up_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=msg_list
            )
            result = follow_up_response.choices[0].message.content

    else:
        result = assistant_text
        
    return result