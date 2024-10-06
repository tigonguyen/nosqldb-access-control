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