from neo4j import GraphDatabase

class EmployeeSearch:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    def close(self):
        self.driver.close()
    # Safely search for an employee using parameterized query
    def search_employee_by_name(self, user_input):
        # Ensure that user input is a non-empty string
        if not user_input or not isinstance(user_input, str):
            raise ValueError("User input must be a non-empty string.")
        with self.driver.session() as session:
            # Run the query and store the results in a list
            result = session.run(
                "MATCH (e:Employee {name: $name}) RETURN e.name, e.role",
                name=user_input  # Pass user input as a parameter
            )
            # Fetch all records before consuming the result
            return [record for record in result]

if __name__ == "__main__":
    searcher = EmployeeSearch("bolt://localhost:7687", "neo4j", "password")
    try:
        # Input from user in the console
        user_input = input("Enter employee name: ")
        # Call the safe method to query employee
        records = searcher.search_employee_by_name(user_input)
        # Display the result
        if records:
            for record in records:
                print(f"Name: {record['e.name']}, Role: {record['e.role']}")
        else:
            print(f"No employee found with the name {user_input}")
    except ValueError as e:
        print(e)
    finally:
        searcher.close()

