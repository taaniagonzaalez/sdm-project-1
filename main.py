from neo4j import GraphDatabase, RoutingControl

# Replace these with your actual credentials from the lab or Aura instance
URI = "neo4j://localhost:7687"  # Use "neo4j+s://" for Aura (cloud)
AUTH = ("neo4j", "your_password")
DATABASE = "neo4j"

class Neo4jApp:
    def __init__(self, uri, auth):
        # The driver holds the details to establish connections
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        # Close the driver connection to release resources
        self.driver.close()

    def verify_connection(self):
        # Force the driver to verify connectivity immediately
        self.driver.verify_connectivity()
        print("Successfully connected to Neo4j!")

    def run_sample_query(self, person_name):
        # execute_query is the modern, recommended way to run transactions
        query = "MERGE (p:Person {name: $name}) RETURN p.name AS name"
        records, summary, keys = self.driver.execute_query(
            query,
            name=person_name,
            database_=DATABASE,
            routing_=RoutingControl.WRITE  # Use WRITE for updates, READ for fetches
        )
        for record in records:
            print(f"Node found/created: {record['name']}")

if __name__ == "__main__":
    app = Neo4jApp(URI, AUTH)
    try:
        app.verify_connection()
        app.run_sample_query("Alice")
    finally:
        app.close()