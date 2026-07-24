from database import tasks_collection,contacts_collection
from config import elevenlabs_client,ELEVENLABS_AGENT_ID,ELEVENLABS_PHONE_NUMBER_ID
import datetime
def execute_pending_calls():
    result = []
    for task in tasks_collection.find(
                {'status':'PENDING',
                'action':'call'}
                ):
        contact = contacts_collection.find_one({'name':task['contact_name'].lower()})
        
        if not contact:
            tasks_collection.update_one(
                {'_id': task['_id']},
                {'$set': {'status': 'FAILED','error':'CONTACT NOT FOUND'}}
            )
            result.append(f'Call Failed for {task['title']}. Contact Not Found {task['contact_name']}')
        else:
            response = elevenlabs_client.conversational_ai.twilio.outbound_call(
                agent_id=ELEVENLABS_AGENT_ID,
                agent_phone_number_id=ELEVENLABS_PHONE_NUMBER_ID,
                to_number=contact['phone'],
                conversation_initiation_client_data= {
                    'dynamic_variables':{
                        'contact_name':task['contact_name'],
                        'task_summary':task['description']
                    }
                }
            )
            tasks_collection.update_one(
                {'_id': task['_id']},
                {'$set': {'status': 'CALLING',
                          'called_at': datetime.datetime.now(),
                          'conversation_id':response.conversation_id
                          }
                 }
            )
            result.append(f'Call Placed for {task['title']} to {task['contact_name']}')
    return result if result else ['No Pending Calls']

def fetch_conversation_status():
    result = []
    for task in tasks_collection.find(
                    {'status':'CALLING'}
                    ):
        print('task:',task)
        conversation = elevenlabs_client.conversational_ai.conversations.get(
                        conversation_id=task['conversation_id']
                    )
        # result.append([conversation.status])
        if conversation.status == 'done':
                tasks_collection.update_one(
                                {'_id': task['_id']},
                                {'$set': {'status': 'COMPLETED'
                                        }
                                }
                            )
                
        else:
                tasks_collection.update_one(
                                {'_id': task['_id']},
                                {'$set': {'status': 'PENDING'
                                          }
                                 }
                            )        
    for task in tasks_collection.find(
        {'status':'COMPLETED'}
    ):
        result.append(f"Task Completed: {task['title']} - {task['description']} - Called {task['contact_name']}")
    
    return result

def get_conversation_transcript(conversation_id):
    conversation = elevenlabs_client.conversational_ai.conversations.get(
        conversation_id=conversation_id
    )
    return conversation