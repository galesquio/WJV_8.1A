import re
import json
from pydal import DAL, Field




# Example connection; adjust the connection string and folder as necessary.
db = DAL('sqlite://WJV_DB4.db',folder = 'DB',migrate=False)
db.define_table('Room_rates_db',
                Field('Rate_ID', unique=True),
                Field('Rate_Name', type='string'),
                Field('Price_', type='integer'),
                Field('Price_add', type='integer'),
                Field('Head_price', type='integer'))

# Example usage: check if Room 11 with 24 hours exists.


#load the json file room_mapping.json in resource folder
with open('Resource/room_mapping.json', 'r') as file:
    room_mapping = json.load(file)


pass_ = True

for key, value in room_mapping.items():
    # Extract the room number and hours from the value
    room_number = key.split("_")[-1]  # Extract the room number from the string
    if int(room_number) != 97:
        print (room_number)
        hours = int(value[1])
        room_number_str = str(room_number).zfill(3)
        pattern = f"{room_number_str}_"
        print (pattern, value[0])
        if 'COTTAGE' in value[0]:
            records = db(db.Room_rates_db.Rate_ID.like(f"C%_{pattern}%")).select()
        else:
            # Records not starting with "C"
            records = db(~db.Room_rates_db.Rate_ID.like(f"C%") & db.Room_rates_db.Rate_ID.like(f"%_{pattern}%")).select()
        room_hours = []
        for row_index, record in enumerate(records):
            room_hours.append(int(record.Rate_ID.split("_")[-1]))
        if hours not in room_hours:
            print (room_hours)
            print(f"Room {room_number} with {hours} hours does NOT exist in the database.")
            pass_ = False
            break


if pass_:
    print ("All rooms are present in the database.")
    #wait user input to close the program
# input("Press Enter to exit...")
