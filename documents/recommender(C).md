MATCH (c:Conference)<-[:PART_OF]-(:Edition)<-[:BELONGS_TO]-(pr:Proceedings)
WHERE c.name CONTAINS "Int. Conf. on Seven" 
MATCH (p:Paper)-[:PUBLISHED_AT]->(pr)
MATCH (p)-[:HAS_KEYWORD]->(t:Topic)
WHERE t.name = "Computer Science"
MATCH (author:Author)-[:WRITES]->(p)
WITH author, count(DISTINCT p) AS expertise_score, collect(DISTINCT p.title) AS publications
RETURN author.name AS potential_reviewer, 
       expertise_score, 
       publications
ORDER BY expertise_score DESC
LIMIT 10