import json
from database import DBHelper
def save_contacts():
    file = open('contacts.json','r')
    contacts = file.read()
    contacts_dictionary = json.loads(contacts)
    print(contacts_dictionary,type(contacts_dictionary))
    contacts_to_save = contacts_dictionary['contacts']
    db = DBHelper()
    db.select_collection('contacts')
    db.save_many(contacts_to_save)
def main():
    save_contacts()

if __name__ == '__main__':
    main()