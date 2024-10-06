from pymongo import MongoClient
from pprint import pprint
import re

# Function to sanitize input
def sanitize_input(user_input):
    if re.match("^[a-zA-Z]+$", user_input):  # Only allow alphabetic names
        return user_input
    else:
        raise ValueError("Invalid input: only alphabetic characters allowed")

def secure_find_employee(user_input):
    client = MongoClient('mongodb://hrUser:password@localhost:27017/companyDB')
    db = client.companyDB

    # Sanitize user input before passing it to the query
    sanitized_input = sanitize_input(user_input)
    employees = db.employees.find({"name": sanitized_input})
    return list(employees)

if __name__ == "__main__":
    try:
        user_input = input("Enter employee name: ")
        result = secure_find_employee(user_input)
        for employee in result:
            pprint(employee, indent=2)
    except ValueError as e:
        print(e)
