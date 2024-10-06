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
