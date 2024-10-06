# mongodb demo
## 1. Fine-Grained Access Control Problem
MongoDB, like many NoSQL databases, provides access control at the database and collections level but does not naturally provide field-level access control without complex configurations or custom implementation. This limitation means a user can either access the entire collection or none of it, making it difficult to implement access policies at a more granular level (e.g., row or field level).

We will create a dataset in MongoDB and demonstrate how the lack of fine-grained access control can be a problem, then address this issue using access control policies encoding within documents.

### Initilization:
MongoDB Initialization
```
version: '3'
services:
  mongodb:
    image: mongo:latest
    container_name: mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    command: --auth
```
Connect to MongoDB (from the container):
```
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin
```
Create Sample Data
Switch to the desired database (e.g., testDB):
```
use companyDB;
db.createCollection("employees");
```
Insert Sample Data:
```
db.employees.insertMany([
  { _id: 1, name: "Alice", salary: 100000, department: "HR", role: "admin" },
  { _id: 2, name: "Bob", salary: 90000, department: "Finance", role: "manager" },
  { _id: 3, name: "Charlie", salary: 85000, department: "IT", role: "employee" },
  { _id: 4, name: "David", salary: 75000, department: "Marketing", role: "employee" }
]);
```
### Demonstrating Access Control Problem
Create users with basic access control:
```
db.createUser({
  user: "hrUser",
  pwd: "password",
  roles: [{ role: "read", db: "companyDB" }]
});
db.createUser({
  user: "regularUser",
  pwd: "password",
  roles: [{ role: "read", db: "companyDB" }]
});
```
Test access control
`regularUser` should only have access to the name and department fields, but due to MongoDB's lack of field-level access control, they can see everything:
```
docker exec -it mongodb mongosh -u regularUser -p password --authenticationDatabase companyDB

```
Query the collection: 
```
use companyDB;
db.employees.find({});
```
### Resolved by Application-Level Access Control
Update MongoDB documents to include access control policies: 
We will modify the collection to include an `accessPolicy` field, so we can simulate field-level security for `salary`.
```
db.employees.updateMany({}, [
  {
    $set: {
      accessPolicy: {
        salary: { role: ["hrUser"] },  // Only hrUser can see salary
        name: { role: ["hrUser", "regularUser"] },
        department: { role: ["hrUser", "regularUser"] },
        role: { role: ["hrUser"] }  // Remove admin role
      }
    }
  }
]);
```
Application-Level Access Control
Here, the Python script will check the role of the user and filter the fields accordingly.
```
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

    # Example with admin who should see everything
    print("\nData accessible to admin:")
    admin_data = filter_data_by_role('admin')
    pprint(admin_data, indent=2)
```

For `hrUser` (who can see the salary field):
```
Data accessible to hrUser:
[ {'department': 'HR', 'name': 'Alice', 'salary': 100000},
  {'department': 'Finance', 'name': 'Bob', 'salary': 90000},
  {'department': 'IT', 'name': 'Charlie', 'salary': 85000},
  {'department': 'Marketing', 'name': 'David', 'salary': 75000}]
```
For `regularUser` (who cannot see the salary field):
```
Data accessible to regularUser:
[ {'department': 'HR', 'name': 'Alice'},
  {'department': 'Finance', 'name': 'Bob'},
  {'department': 'IT', 'name': 'Charlie'},
  {'department': 'Marketing', 'name': 'David'}]
```
### Alternative Solutions
- Defining an Enforcement Monitor: Using middleware to enforce access control dynamically at the query level.
- Modifying NoSQL Structures: Structuring documents differently to separate sensitive data into different collections.
- Adapting Query Methods: Modifying queries dynamically based on the user's role and the associated access control model.
## 2. NoSQL Injection
### The simulation
In a regular scenario, you might search for an employee named "Bob" like this:
```
db.employees.find({ name: "Bob" });
```
The result would be:
```
[
  {
    _id: 2,
    name: 'Bob',
    salary: 90000,
    department: 'Finance',
    role: 'manager',
    accessPolicy: {
      salary: { role: [ 'hrUser' ] },
      name: { role: [ 'hrUser', 'regularUser' ] },
      department: { role: [ 'hrUser', 'regularUser' ] },
      role: { role: [ 'hrUser' ] }
    }
  }
]
```
If there’s no input sanitization and the query takes user input directly, an attacker could use the following to return all documents:
```
db.employees.find({ name: { "$ne": null } });
```
Result:
```
[
  {
    _id: 1,
    name: 'Alice',
    salary: 100000,
    department: 'HR',
    role: 'admin',
    accessPolicy: {
      salary: { role: [ 'hrUser' ] },
      name: { role: [ 'hrUser', 'regularUser' ] },
      department: { role: [ 'hrUser', 'regularUser' ] },
      role: { role: [ 'hrUser' ] }
    }
  },
  {
    _id: 2,
    name: 'Bob',
    salary: 90000,
    department: 'Finance',
    role: 'manager',
    accessPolicy: {
      salary: { role: [ 'hrUser' ] },
      name: { role: [ 'hrUser', 'regularUser' ] },
      department: { role: [ 'hrUser', 'regularUser' ] },
      role: { role: [ 'hrUser' ] }
    }
  },
  ...
]
```
### Fixing NoSQL Injection via Python Application
To prevent NoSQL injection, you need to sanitize and validate user input before passing it to the database query. We’ll fix the injection by properly validating the input to ensure that only valid names can be used in the query.
```
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
```
## 3. Lack of Standard NoSQL Query Language
### Add Cassandra to Docker Compose
Updated docker-compose.yml:
```
version: '3'
services:
  mongodb:
    image: mongo:latest
    container_name: mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    command: --auth

  cassandra:
    image: cassandra:latest
    container_name: cassandra
    ports:
      - "9042:9042"
    environment:
      CASSANDRA_SEEDS: "cassandra"
```
### Create the Cassandra Table
Connect to the Cassandra container:
```
docker exec -it cassandra cqlsh
```
Inside `cqlsh`, create a keyspace and the `employees` table:
```
CREATE KEYSPACE companyDB WITH REPLICATION = { 'class': 'SimpleStrategy', 'replication_factor': 1 };
USE companyDB;
CREATE TABLE employees (
    id UUID PRIMARY KEY,
    name TEXT,
    salary DECIMAL,
    department TEXT
);
INSERT INTO employees (id, name, salary, department) VALUES (uuid(), 'Alice', 100000, 'HR');
INSERT INTO employees (id, name, salary, department) VALUES (uuid(), 'Bob', 90000, 'Finance');
INSERT INTO employees (id, name, salary, department) VALUES (uuid(), 'Charlie', 85000, 'IT');
INSERT INTO employees (id, name, salary, department) VALUES (uuid(), 'David', 75000, 'Marketing');
```
We can test the new table by querying it:
```
cqlsh:companydb> SELECT * FROM employees;
 id                                   | department | name    | salary
--------------------------------------+------------+---------+--------
 469995c6-fde0-41a7-975f-65ebf005dc4a |    Finance |     Bob |  90000
 3158a3a2-5c0e-4e69-8f0b-b9a70286c230 |         IT | Charlie |  85000
 8cd03e26-1874-4f3d-9284-16e13ba7815c |         HR |   Alice | 100000
 184839db-d5b4-42a1-9f8f-f0e594560ee5 |  Marketing |   David |  75000
```
### Implement Abstraction Layer for Querying
We will use the abstraction layer to query data from either MongoDB or Cassandra.
```
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
```
Here’s how you can query employees by department using either MongoDB or Cassandra:
```
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
```
Expected Output:
```
Choose database (1 for MongoDB, 2 for Cassandra):
1
Enter department to query: IT
Employees in IT department:
{'name': 'Charlie', 'salary': 85000, 'department': 'IT'}

Choose database (1 for MongoDB, 2 for Cassandra):
2
Enter department to query: HR
Employees in HR department:
{'name': 'Alice', 'salary': Decimal('100000'), 'department': 'HR'}
```