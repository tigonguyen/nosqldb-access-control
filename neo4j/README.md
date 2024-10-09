# neo4j
## 1. Fine-Grained Access Control Problem
Neo4j Community Edition does not natively support this level of fine-grained control, which can lead to over-permissioning (where a user has access to more data than they should).

Let’s assume we have an Employee node and a Salary node, and we want to allow certain users (e.g., managers) to view salary information, while regular users should only be able to see basic employee information (name, department, etc.). In Neo4j Community Edition, it’s not possible to enforce such fine-grained control where specific properties or relationships are restricted based on user roles.

We’ll set up a scenario where:
- Managers should be able to access both employee and salary information.
- Regular users should only be able to access employee information (without salary details).

### Set Up Neo4j in Docker
Docker Compose for Neo4j
```
version: '3'
services:
  neo4j:
    image: neo4j:latest
    container_name: neo4j
    environment:
      NEO4J_AUTH: neo4j/password  # Default username and password
    ports:
      - "7474:7474"  # HTTP access
      - "7687:7687"  # Bolt protocol access
```
Start the Neo4j instance:
```
docker-compose up -d
```
Access Neo4j via the browser at http://localhost:7474 and log in with the default credentials (`neo4j`/`password`).
### Create Example Data in Neo4j
We will create a simple graph with employees, departments, and salary information.
```
CREATE 
       (Alice:Employee {name: 'Alice', role: 'Manager'}),
       (Bob:Employee {name: 'Bob', role: 'Employee'}),
       (Charlie:Employee {name: 'Charlie', role: 'Employee'}),
       (David:Employee {name: 'David', role: 'Manager'}),

       (HR:Department {name: 'HR'}),
       (Finance:Department {name: 'Finance'}),

       (Salary1:Salary {amount: 100000}),
       (Salary2:Salary {amount: 90000}),
       (Salary3:Salary {amount: 85000}),
       (Salary4:Salary {amount: 75000}),

       (Alice)-[:WORKS_IN]->(HR),
       (David)-[:WORKS_IN]->(HR),
       (Bob)-[:WORKS_IN]->(Finance),
       (Charlie)-[:WORKS_IN]->(Finance),

       (Alice)-[:HAS_SALARY]->(Salary1),
       (Bob)-[:HAS_SALARY]->(Salary2),
       (Charlie)-[:HAS_SALARY]->(Salary3),
       (David)-[:HAS_SALARY]->(Salary4);
```
If we query all employees, a regular user will be able to see both employee and salary information, which violates our fine-grained access control requirement.
```
MATCH (e:Employee)-[:HAS_SALARY]->(s:Salary)
RETURN e.name, e.role, s.amount;

╒═════════╤══════════╤════════╕
│e.name   │e.role    │s.amount│
╞═════════╪══════════╪════════╡
│"Alice"  │"Manager" │100000  │
├─────────┼──────────┼────────┤
│"Bob"    │"Employee"│90000   │
├─────────┼──────────┼────────┤
│"Charlie"│"Employee"│85000   │
├─────────┼──────────┼────────┤
│"David"  │"Manager" │75000   │
└─────────┴──────────┴────────┘
```
### Implementing a Basic Workaround in Application Code
Example Python Code for Role-Based Access Control:
```
from neo4j import GraphDatabase
class EmployeeAccessControl:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    def close(self):
        self.driver.close()
    def get_employee_data(self, user_role):
        with self.driver.session() as session:
            if user_role == "Manager":
                # Manager gets all data, including salary
                result = session.run("""
                    MATCH (e:Employee)-[:HAS_SALARY]->(s:Salary)
                    RETURN e.name, e.role, s.amount
                """)
            else:
                # Regular user gets only employee details without salary
                result = session.run("""
                    MATCH (e:Employee)-[:WORKS_IN]->(d:Department)
                    RETURN e.name, e.role, d.name
                """)
            for record in result:
                print(record)
if __name__ == "__main__":
    # Create the access control object
    ac = EmployeeAccessControl("bolt://localhost:7687", "neo4j", "password")

    # Regular User Query
    print("Regular User Data:")
    ac.get_employee_data("Employee")  # Simulate regular user role

    # Manager Query
    print("\nManager Data:")
    ac.get_employee_data("Manager")  # Simulate manager role

    ac.close()
```
Expected Result:
```
Regular User Data:
<Record e.name='Alice' e.role='Manager' d.name='HR'>
<Record e.name='David' e.role='Manager' d.name='HR'>
<Record e.name='Bob' e.role='Employee' d.name='Finance'>
<Record e.name='Charlie' e.role='Employee' d.name='Finance'>

Manager Data:
<Record e.name='Alice' e.role='Manager' s.amount=100000>
<Record e.name='Bob' e.role='Employee' s.amount=90000>
<Record e.name='Charlie' e.role='Employee' s.amount=85000>
<Record e.name='David' e.role='Manager' s.amount=75000>
```
## 2. NoSQL Injection
### Example of a Vulnerable Query in Neo4j
Assume we have a web application where a query is constructed dynamically using input provided by the user. For example:
```
def search_employee_by_name(user_input):
    query = f"MATCH (e:Employee {{name: '{user_input}'}}) RETURN e.name, e.role"
    return query
```
If the user inputs the name directly, the application constructs a query like:
```
MATCH (e:Employee {name: 'Bob'}) RETURN e.name, e.role
```
However, if the user provides malicious input, such as `Alice' RETURN e LIMIT 1; MATCH (n) DETACH DELETE n; //`, the query becomes:
```
MATCH (e:Employee {name: 'Alice'}) RETURN e LIMIT 1; MATCH (n) DETACH DELETE n;
```
This query:
- Finds "Alice" and returns her record.
- Deletes all nodes in the database (`MATCH (n) DETACH DELETE n`).

The application doesn’t sanitize input, which allows this injection to happen. If you try querying the employees again, you’ll find that the database has been wiped out.
```
MATCH (e:Employee) RETURN e;
(Empty result set, because all nodes were deleted)
```
### Fixing NoSQL Injection in Neo4j
To prevent NoSQL injection in Neo4j, you need to:
- Use parameterized queries to ensure that input is properly escaped and sanitized.
- Validate user input to ensure that only valid names (or other types of input) are accepted.

In Neo4j, the safest way to execute queries with user input is to use parameterized queries. This approach binds user inputs as parameters, ensuring they are safely handled.
```
from neo4j import GraphDatabase
class EmployeeSearch:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    def close(self):
        self.driver.close()
    # Safely search for an employee using parameterized query
    def search_employee_by_name(self, user_input):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Employee {name: $name}) RETURN e.name, e.role",
                name=user_input  # Pass user input as a parameter
            )
            return result
# Usage example
if __name__ == "__main__":
    searcher = EmployeeSearch("bolt://localhost:7687", "neo4j", "password")
    # This input is safe now
    user_input = "Alice"
    result = searcher.search_employee_by_name(user_input)
    for record in result:
        print(f"Name: {record['e.name']}, Role: {record['e.role']}")
    searcher.close()
```
Now that we’ve secured the query, if an attacker tries to inject a malicious string, it will be treated as a safe parameter rather than executed as part of the query.
```
$ python3 injectionNeo4j.py
Enter employee name: Alice' RETURN e LIMIT 1; MATCH (n) DETACH DELETE n;
No employee found with the name Alice' RETURN e LIMIT 1; MATCH (n) DETACH DELETE n;
```
The query will safely escape it and will not delete any data.
```
$ python3 injectionNeo4j.py
Enter employee name: Alice
Name: Alice, Role: Manager
```
## 3. Audit is not Available by Default
Neo4j audit logging is an important feature for tracking access, queries, and other actions in the database. However, in Neo4j Community Edition, audit logging is not available by default. Audit logging is a feature that comes with Neo4j Enterprise Edition, and it allows administrators to track important actions performed on the database, such as:
- Who accessed the database
- What queries were run
- What data was accessed or modified

If you're using Neo4j Community Edition, you'll face a limitation: there is no built-in audit logging capability, which makes it difficult to track user actions for security or compliance purposes.
### Enable Query Logging
Change the `docker-compose.yaml` for Neo4j to below:
```
version: '3'
services:
  neo4j:
    image: neo4j:enterprise
    container_name: neo4j
    environment:
      - NEO4J_AUTH=neo4j/password  # Set the default username and password
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes  # You must accept the license for Enterprise Edition
    ports:
      - "7474:7474"  # HTTP access
      - "7687:7687"  # Bolt protocol access
```
Then, we stop the old version and spin up the database again:
```
docker compose down
docker compose up -d
```
Now, to access the container, we can run:
```
docker exec -it neo4j bash
```
Then, we run these commands to edit the configuration to enable query audit:
```
apt update
apt install vim
vim conf/neo4j.conf
```
Find the below line and configure as enabled:
```
db.logs.query.enabled=INFO
db.logs.query.threshold=0
```
Then, log out and restart the container.
```
docker restart neo4j
```
### Test the audit logs
Now, we can create some example data on the neo4j:
```
CREATE 
       (Alice:Employee {name: 'Alice', role: 'Manager'}),
       (Bob:Employee {name: 'Bob', role: 'Employee'}),
       (Charlie:Employee {name: 'Charlie', role: 'Employee'}),
       (David:Employee {name: 'David', role: 'Manager'}),

       (HR:Department {name: 'HR'}),
       (Finance:Department {name: 'Finance'}),

       (Salary1:Salary {amount: 100000}),
       (Salary2:Salary {amount: 90000}),
       (Salary3:Salary {amount: 85000}),
       (Salary4:Salary {amount: 75000}),

       (Alice)-[:WORKS_IN]->(HR),
       (David)-[:WORKS_IN]->(HR),
       (Bob)-[:WORKS_IN]->(Finance),
       (Charlie)-[:WORKS_IN]->(Finance),

       (Alice)-[:HAS_SALARY]->(Salary1),
       (Bob)-[:HAS_SALARY]->(Salary2),
       (Charlie)-[:HAS_SALARY]->(Salary3),
       (David)-[:HAS_SALARY]->(Salary4);
```
Then, query it
```
MATCH (e:Employee)-[:HAS_SALARY]->(s:Salary)
RETURN e.name, e.role, s.amount;
```
To access the query logs from the container, we can run below command. Then, we can see the audit logs have been captured there.
```
docker exec -it neo4j bash
# In the container bash
cd ./logs
cat query.log
```