from pymongo import MongoClient
from pprint import pprint

# Connect to MongoDB's companyDB with a given user role
def connect_mongo(user, password):
    # Connect specifically to companyDB
    client = MongoClient(f'mongodb://{user}:{password}@localhost:27017/companyDB')
    db = client.companyDB  # Specify the database explicitly
    return db

# Function to filter the data based on the user's role
def filter_data_by_role(user_role):
    db = connect_mongo(user_role, 'password')  # Password is assumed to be 'password' for simplicity
    employees = db.employees.find()
    
    # Filter the documents based on the user's role
    filtered_results = []
    for employee in employees:
        filtered_doc = {}
        if 'accessPolicy' in employee:
            if employee['accessPolicy']['name']['role']:
                filtered_doc['name'] = employee['name']
            if user_role in employee['accessPolicy']['salary']['role']:
                filtered_doc['salary'] = employee['salary']
            if employee['accessPolicy']['department']['role']:
                filtered_doc['department'] = employee['department']
        filtered_results.append(filtered_doc)
    return filtered_results

if __name__ == '__main__':
    # Example with hrUser who should see salary
    print("Data accessible to hrUser:")
    hr_data = filter_data_by_role('hrUser')
    pprint(hr_data, indent=2)

    # Example with regularUser who should not see salary
    print("\nData accessible to regularUser:")
    regular_data = filter_data_by_role('regularUser')
    pprint(regular_data, indent=2)
