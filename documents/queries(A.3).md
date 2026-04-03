// Update PROVIDES
MATCH (a:Author)-[r:PROVIDES_REVIEW]->(rev:Review)
MERGE (a)-[new_r:PROVIDES]->(rev)
SET new_r = properties(r)
DELETE r;

// Update EVALUATES
MATCH (rev:Review)-[r:EVALUATES_PAPER]->(p:Paper)
MERGE (rev)-[new_r:EVALUATES]->(p)
SET new_r = properties(r)
DELETE r;

// 1. Find all authors that have an affiliation string
MATCH (a:Author)
WHERE a.affiliation IS NOT NULL AND a.affiliation <> ""

// 2. Dynamically create an Organization node based on that string
// MERGE ensures that if multiple authors belong to "MIT", only one "MIT" node is created
MERGE (o:Organization {name: a.affiliation})
ON CREATE SET o.type = "Unknown" // Set a default type since we didn't export organizations.csv

// 3. Draw the relationship between the author and the organization
MERGE (a)-[:AFFILIATED_WITH]->(o);