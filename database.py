from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI
class DBHelper:
    
    def __init__(self,db_name='jai2026'):
        uri = MONGODB_URI
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client[db_name]
        print(' [DBHelper] Connection Created')
        
    def select_collection(self,collection_name = 'users'):
        self.collection = self.db[collection_name]
        print(' [DBHelper] Collection Selected',collection_name)
    
    def save(self,document):
        inserted_id = self.collection.insert_one(document)
        print(' [DBHelper] Document Saved. ID is:',inserted_id)
    
    def retrieve(self,condition = None):
        if condition is None:
            condition = {}
        result = list(self.collection.find(condition))
        print(' [DBHelper] Documents Retrieved. Result is:',result)
        # for document in result:
        #     print(document)
        return result
            
    def update(self,condition=None,document_to_update = None):
        result = self.collection.update_one(
            condition,
            {
                '$set': document_to_update
            }
        )
        return result
        # print(' [DBHelper] Documents Updated',result)
        
    def delete(self,condition):
        result = self.collection.delete_one(condition)
        print(' [DBHelper] Documents Deleted',result)
        return result