from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, DB_NAME
import json
import datetime
import re

mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = mongo_client[DB_NAME]
tasks_collection = db['tasks']
contacts_collection = db['contacts']

class DBHelper:
    def __init__(self, db_name='jai2026'):
        self.client = mongo_client
        self.db = self.client[db_name]
        print(' [DBHelper] Connection Created')
        
    def select_collection(self, collection_name='users'):
        self.collection = self.db[collection_name]
        print(' [DBHelper] Collection Selected', collection_name)
    
    def save(self, document):
        inserted_id = self.collection.insert_one(document)
        print(' [DBHelper] Document Saved. ID is:', inserted_id)
        return inserted_id
    
    def save_many(self, document):
        inserted_id = self.collection.insert_many(document)
        print(' [DBHelper] Documents Saved. ID is:', inserted_id)
        return inserted_id
    
    def retrieve(self, condition=None):
        if condition is None:
            condition = {}
        result = list(self.collection.find(condition))
        return result
            
    def update(self, condition=None, document_to_update=None):
        result = self.collection.update_one(condition, {'$set': document_to_update})
        return result
        
    def delete(self, condition):
        result = self.collection.delete_one(condition)
        print(' [DBHelper] Documents Deleted', result)
        return result

def save_contacts():
    file = open('contacts.json', 'r')
    contacts = file.read()
    contacts_dictionary = json.loads(contacts)
    contacts_to_save = contacts_dictionary['contacts']
    db_h = DBHelper()
    db_h.select_collection('contacts')
    db_h.save_many(contacts_to_save)


# ==============================================================================
# CANONICAL ANALYTICS LAYER (SINGLE SOURCE OF TRUTH)
# ==============================================================================

def build_canonical_call_filter(intent_status=None, date_preset=None):
    """
    Constructs the SINGLE CANONICAL MongoDB filter for call records across 
    Dashboard metrics, Analytics Chat, and Call History views.
    """
    condition = {"action": "call"}

    if intent_status:
        intent_upper = str(intent_status).upper().strip()
        
        if intent_upper == "FAILED":
            condition["$or"] = [
                {"status": {"$regex": "^FAILED$", "$options": "i"}},
                {"twilio_status": {"$in": ["failed", "no-answer", "busy", "canceled", "rejected", "declined"]}},
                {"error": {"$exists": True, "$ne": None}},
                {"last_error": {"$exists": True, "$ne": None}}
            ]
        elif intent_upper == "COMPLETED":
            condition["status"] = {"$regex": "^COMPLETED$", "$options": "i"}
            condition["twilio_status"] = {"$ne": "failed"}
        elif intent_upper == "PENDING":
            condition["status"] = {"$in": ["PENDING", "CALLING"]}

    if date_preset:
        now = datetime.datetime.now()
        if date_preset == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            condition["created_at"] = {"$gte": start, "$lt": end}
        elif date_preset == "yesterday":
            start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            condition["created_at"] = {"$gte": start, "$lt": end}
        elif date_preset == "this_week":
            start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            condition["created_at"] = {"$gte": start}

    return condition


def get_dashboard_metrics():
    """Calculates all dashboard cards using the Canonical Analytics Layer."""
    now = datetime.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Base Counts using Canonical Filters
    total_tasks = tasks_collection.count_documents({})
    total_contacts = contacts_collection.count_documents({})

    total_calls = tasks_collection.count_documents(build_canonical_call_filter())
    failed_calls = tasks_collection.count_documents(build_canonical_call_filter(intent_status="FAILED"))
    completed_calls = tasks_collection.count_documents(build_canonical_call_filter(intent_status="COMPLETED"))
    pending_calls = tasks_collection.count_documents(build_canonical_call_filter(intent_status="PENDING"))
    
    today_completed_filter = {**build_canonical_call_filter(intent_status="COMPLETED"), "created_at": {"$gte": today_start}}
    today_completed = tasks_collection.count_documents(today_completed_filter)

    # 2. Retry Metrics
    retry_pipeline = [{"$group": {"_id": None, "total_retries": {"$sum": "$retry_count"}}}]
    r_res = list(tasks_collection.aggregate(retry_pipeline))
    total_retries = r_res[0]['total_retries'] if r_res else 0

    today_retry_pipeline = [
        {"$match": {"created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total_retries": {"$sum": "$retry_count"}}}
    ]
    tr_res = list(tasks_collection.aggregate(today_retry_pipeline))
    today_retries = tr_res[0]['total_retries'] if tr_res else 0

    # 3. Contact Call Stats & Success Rates
    contact_pipeline = [
        {"$match": {"action": "call"}},
        {"$group": {
            "_id": "$contact_name",
            "call_count": {"$sum": 1},
            "success_count": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}}
        }},
        {"$project": {
            "call_count": 1,
            "success_count": 1,
            "success_rate": {"$divide": ["$success_count", {"$max": ["$call_count", 1]}]}
        }},
        {"$sort": {"call_count": -1}}
    ]
    contact_stats = list(tasks_collection.aggregate(contact_pipeline))
    most_called = contact_stats[0]['_id'] if contact_stats else "N/A"
    highest_success_contact = sorted(contact_stats, key=lambda x: x.get('success_rate', 0), reverse=True)[0]['_id'] if contact_stats else "N/A"

    # 4. Discrepancies
    task_contacts_raw = tasks_collection.distinct("contact_name")
    db_contacts_raw = contacts_collection.distinct("name")

    task_c_lower = {c.lower(): c for c in task_contacts_raw if c}
    db_c_lower = {c.lower(): c for c in db_contacts_raw if c}

    unassigned_lower = set(db_c_lower.keys()) - set(task_c_lower.keys())
    deleted_lower = set(task_c_lower.keys()) - set(db_c_lower.keys())

    unassigned_contacts = [db_c_lower[k] for k in unassigned_lower]
    deleted_contacts_raw = [task_c_lower[k] for k in deleted_lower]
    calls_to_deleted = tasks_collection.count_documents({"action": "call", "contact_name": {"$in": deleted_contacts_raw}}) if deleted_contacts_raw else 0

    return {
        "Total_Tasks_All_Time": total_tasks,
        "Total_Calls_All_Time": total_calls,
        "Failed_Calls_All_Time": failed_calls,
        "Pending_Calls_Current": pending_calls,
        "Completed_Calls_All_Time": completed_calls,
        "Total_Contacts": total_contacts,
        "Total_Retries_All_Time": total_retries,
        "Retries_Today": today_retries,
        "Most_Called_Contact_All_Time": most_called,
        "Contact_With_Highest_Success_Rate": highest_success_contact,
        "Contacts_With_No_Tasks_Assigned": unassigned_contacts,
        "Number_Of_Calls_To_Deleted_Contacts": calls_to_deleted,
        "Todays_Completed_Tasks_Count": today_completed
    }


def get_calls_query(intent_status=None, date_preset=None):
    """
    Shared query logic for retrieving call details. 
    Guarantees parity with get_dashboard_metrics via build_canonical_call_filter.
    """
    filter_cond = build_canonical_call_filter(intent_status, date_preset)
    results = list(tasks_collection.find(filter_cond).sort("created_at", -1))
    
    # Smart Fallback: If date filter returns 0 records, fall back to ALL TIME for the same intent
    if not results and date_preset:
        fallback_cond = build_canonical_call_filter(intent_status, date_preset=None)
        results = list(tasks_collection.find(fallback_cond).sort("created_at", -1))
        
    return results


def get_tasks_query(status=None, date_preset=None, action=None):
    """Shared query logic for retrieving generic non-call tasks."""
    condition = {}
    if status and status.strip():
        condition["status"] = {"$regex": f"^{re.escape(status.strip())}$", "$options": "i"}
    
    if action and action.strip():
        condition["action"] = {"$regex": f"^{re.escape(action.strip())}$", "$options": "i"}
    else:
        condition["action"] = {"$ne": "call"}
        
    if date_preset:
        now = datetime.datetime.now()
        if date_preset == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            condition["created_at"] = {"$gte": start, "$lt": end}
        elif date_preset == "yesterday":
            start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            condition["created_at"] = {"$gte": start, "$lt": end}

    return list(tasks_collection.find(condition).sort("created_at", -1))