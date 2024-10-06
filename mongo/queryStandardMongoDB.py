from pymongo import MongoClient
from cassandra.cluster import Cluster

# Define the standard interface for NoSQL databases
class NoSQLDatabase:
    def find_employee_by_department(self, department):
        raise NotImplementedError("This method should be overridden")

# MongoDB implementation of the NoSQLDatabase interface
class MongoDBDatabase(NoSQLDatabase):
    def __init__(self):
        self.client = MongoClient('mongodb://admin:password@localhost:27017/')
        self.db = self.client.companyDB

    def find_employee_by_department(self, department):
        return list(self.db.employees.find({ "department": department }, { "_id": 0, "name": 1, "salary": 1, "department": 1 }))

# Cassandra implementation of the NoSQLDatabase interface
class CassandraDatabase(NoSQLDatabase):
    def __init__(self):
        self.cluster = Cluster(['localhost'])
        self.session = self.cluster.connect('companydb')

    def find_employee_by_department(self, department):
        query = "SELECT name, salary, department FROM employees WHERE department=%s ALLOW FILTERING"
        rows = self.session.execute(query, (department,))
        return [{"name": row.name, "salary": row.salary, "department": row.department} for row in rows]

# Abstraction layer usage
def get_employees_by_department(database: NoSQLDatabase, department):
    return database.find_employee_by_department(department)

if __name__ == "__main__":
    # Choose which database to use
    print("Choose database (1 for MongoDB, 2 for Cassandra):")
    choice = input()

    if choice == '1':
        database = MongoDBDatabase()
    elif choice == '2':
        database = CassandraDatabase()
    else:
        print("Invalid choice.")
        exit()

    # Query the selected database
    department = input("Enter department to query: ")
    employees = get_employees_by_department(database, department)

    print(f"Employees in {department} department:")
    for employee in employees:
        print(employee)
