import os
from database import tasks_collection, contacts_collection
from config import elevenlabs_client, ELEVENLABS_AGENT_ID, ELEVENLABS_PHONE_NUMBER_ID
import datetime
import re
import string
import threading
import time

# --- Twilio Integration ---
from twilio.rest import Client as TwilioClient

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Graceful fallback for fuzzy matching
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

# ==========================================
# CONFIGURATION: DEFAULT RETRY SETTINGS
# ==========================================
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_MINUTES = [2, 5, 15]

# Terminal Twilio Statuses (Once we hit these, we make a decision)
TWILIO_TERMINAL_STATUSES = [
    'completed', 'busy', 'no-answer', 'failed', 'canceled', 'invalid-number', 'rejected', 'declined'
]

def normalize_text(text: str) -> str:
    if not text: return ""
    text = str(text).lower().translate(str.maketrans('', '', string.punctuation))
    return " ".join(text.split())

def resolve_contact_for_call(contact_name_query: str):
    search_norm = normalize_text(contact_name_query)
    search_words = set(search_norm.split())
    if not search_words: return None

    regex_pattern = "|".join(re.escape(w) for w in search_words)
    condition = {"name": {"$regex": regex_pattern, "$options": "i"}}
    candidates = list(contacts_collection.find(condition))
    if not candidates: return None

    exact_matches = []
    subset_matches = []
    fuzzy_matches = []

    for doc in candidates:
        target_raw = doc.get("name", "")
        target_norm = normalize_text(target_raw)
        
        if search_norm == target_norm:
            exact_matches.append(doc)
            continue
            
        target_words = set(target_norm.split())
        if search_words.issubset(target_words):
            subset_matches.append(doc)
            continue
            
        if HAS_RAPIDFUZZ:
            score = fuzz.partial_ratio(search_norm, target_norm)
            if score >= 80: fuzzy_matches.append((doc, score))
        else:
            matcher = difflib.SequenceMatcher(None, search_norm, target_norm)
            if matcher.quick_ratio() >= 0.75: fuzzy_matches.append((doc, matcher.quick_ratio()))

    if exact_matches: return exact_matches[0]
    if subset_matches: return subset_matches[0]
    if fuzzy_matches:
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        return fuzzy_matches[0][0]
    return None


def execute_pending_calls():
    now = datetime.datetime.now()
    
    query = {
        'status': 'PENDING', 
        'action': 'call',
        '$or': [
            {'next_retry_at': {'$exists': False}},
            {'next_retry_at': None},
            {'next_retry_at': {'$lte': now}}
        ]
    }
    
    for task in tasks_collection.find(query):
        contact = resolve_contact_for_call(task['contact_name'])
        
        if not contact:
            tasks_collection.update_one(
                {'_id': task['_id']},
                {'$set': {'status': 'FAILED', 'error': 'CONTACT NOT FOUND'}}
            )
            print(f" [Automation Engine] Task '{task.get('title')}' FAILED permanently. Contact not found.")
            continue

        try:
            response = elevenlabs_client.conversational_ai.twilio.outbound_call(
                agent_id=ELEVENLABS_AGENT_ID,
                agent_phone_number_id=ELEVENLABS_PHONE_NUMBER_ID,
                to_number=contact['phone'],
                conversation_initiation_client_data={
                    'dynamic_variables': {
                        'contact_name': contact['name'],
                        'task_summary': task.get('description', '')
                    }
                }
            )
            
            # Extract Twilio Call SID if available in the response object, fallback to conversation ID
            call_sid = getattr(response, 'call_sid', getattr(response, 'conversation_id', None))
            
            tasks_collection.update_one(
                {'_id': task['_id']},
                {'$set': {
                    'status': 'CALLING',
                    'called_at': now,
                    'conversation_id': response.conversation_id,
                    'twilio_call_sid': call_sid
                }}
            )
            print(f" [Automation Engine] DIALED: '{task.get('title')}' to {contact['name']} (Conv: {response.conversation_id})")
        except Exception as e:
            handle_call_failure(task, str(e), max_retries=1, backoff=[2])


def handle_call_failure(task, reason_str: str, is_permanent: bool = False, max_retries: int = DEFAULT_MAX_RETRIES, backoff: list = DEFAULT_BACKOFF_MINUTES):
    current_retries = task.get('retry_count', 0)
    
    if is_permanent or current_retries >= max_retries:
        tasks_collection.update_one(
            {'_id': task['_id']},
            {'$set': {
                'status': 'FAILED', 
                'error': f"{reason_str} (Final Status reached)"
            }}
        )
        print(f" [Automation Engine] ❌ Task '{task.get('title')}' FAILED permanently. Reason: {reason_str}")
    else:
        backoff_index = min(current_retries, len(backoff) - 1)
        wait_minutes = backoff[backoff_index]
        next_retry = datetime.datetime.now() + datetime.timedelta(minutes=wait_minutes)
        
        tasks_collection.update_one(
            {'_id': task['_id']},
            {'$set': {
                'status': 'PENDING',
                'retry_count': current_retries + 1,
                'next_retry_at': next_retry,
                'last_error': reason_str
            }}
        )
        print(f" [Automation Engine] 🔄 Task '{task.get('title')}' ({reason_str}). Scheduled Retry {current_retries + 1}/{max_retries} at {next_retry.strftime('%H:%M:%S')}")


def fetch_conversation_status():
    for task in tasks_collection.find({'status': 'CALLING'}):
        try:
            conversation_id = task.get('conversation_id')
            twilio_call_sid = task.get('twilio_call_sid')
            
            # Retrieve ElevenLabs status
            el_conv = elevenlabs_client.conversational_ai.conversations.get(conversation_id=conversation_id)
            el_status = getattr(el_conv, 'status', '').lower()
            
            # Retrieve true Twilio status if client is configured and SID exists
            tw_status = None
            if twilio_client and twilio_call_sid and twilio_call_sid.startswith("CA"):
                try:
                    twilio_call = twilio_client.calls(twilio_call_sid).fetch()
                    tw_status = twilio_call.status.lower()
                except Exception as e:
                    print(f" [Automation Engine] Twilio API fetch error: {e}")
                    tw_status = None
            
            # Fallback to ElevenLabs status if Twilio is unavailable
            final_status = tw_status if tw_status else el_status
            
            # 1. Update Database with polling logs
            tasks_collection.update_one(
                {'_id': task['_id']},
                {'$set': {
                    'twilio_status': tw_status, 
                    'elevenlabs_status': el_status,
                    'last_polled_at': datetime.datetime.now()
                }}
            )
            
            print(f" [Automation Engine] POLLING '{task.get('title')}' | Twilio: {tw_status or 'N/A'} | ElevenLabs: {el_status}")

            # 2. Wait until terminal status is reached
            if final_status not in TWILIO_TERMINAL_STATUSES:
                # Still ringing, initiated, processing, or in-progress. Do nothing.
                continue
                
            # 3. Policy Execution on Terminal Status
            if final_status == 'completed':
                tasks_collection.update_one({'_id': task['_id']}, {'$set': {'status': 'COMPLETED'}})
                print(f" [Automation Engine] ✅ Task '{task.get('title')}' COMPLETED successfully.")
                
            elif final_status == 'busy':
                # Retry once after a short delay (e.g., 2 minutes)
                handle_call_failure(task, "busy", max_retries=1, backoff=[2])
                
            elif final_status == 'no-answer':
                # Retry with exponential backoff up to 3 times
                handle_call_failure(task, "no-answer", max_retries=3, backoff=[2, 5, 15])
                
            elif final_status == 'failed':
                # Retry only once for temporary failures
                handle_call_failure(task, "failed", max_retries=1, backoff=[5])
                
            elif final_status in ['canceled', 'invalid-number', 'rejected', 'declined']:
                # Never retry
                handle_call_failure(task, final_status, is_permanent=True)

        except Exception as e:
            print(f" [Automation Engine] Error fetching status for '{task.get('title')}': {e}")


def get_conversation_transcript(conversation_id):
    return elevenlabs_client.conversational_ai.conversations.get(
        conversation_id=conversation_id
    )

# --- Call Automation Engine ---
AUTOMATION_THREAD = None

def _automation_loop(interval_seconds: int = 15):
    print(" [Automation Engine] Running...")
    while True:
        try:
            fetch_conversation_status()
            execute_pending_calls()
        except Exception as e:
            print(f" [Automation Engine] Error in background loop: {e}")
        time.sleep(interval_seconds)

def start_automation_engine():
    global AUTOMATION_THREAD
    if AUTOMATION_THREAD is None or not AUTOMATION_THREAD.is_alive():
        AUTOMATION_THREAD = threading.Thread(target=_automation_loop, daemon=True)
        AUTOMATION_THREAD.start()
        print(" [Automation Engine] Daemon thread started successfully.")