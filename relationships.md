# Relationships between Nodes

## Paper Relationships:

1. (:Paper)--[:Cites]--->(:Paper)
2. (:Paper)--[:Contains]--->(:Topics)
3. (:Paper)--[:Starts_with]--->(:Abstract)
4. (:Paper)--[:Published_at]--->(:Edition)
5. (:Paper)--[:Published_at]--->(:Volume)
6. (:Paper)--[:Appear_in]--->(:Proceedings)

## Author Relationships:

1. (:Author)-[:WRITES {role: 'main', is_corresponding: true}]->(:Paper)
2. (:Author)-[:WRITES {role: 'co-author', is_corresponding: false}]->(:Paper)

## Edition Relationships:

1. (:Editions)--[:Part_of]--->(:Workshop)
2. (:Editions)--[:Part_of]--->(:Conference)
3. (:Editions)--[:Dated_in]--->(:Year)
4. (:Editions)--[:Placed_at]--->(:City)
5. (:Editions)--[:Has_proceedings]--->(:Proceedings)

## Volumes Relationships

1. (:Volumes)--[:Dated_in]--->(:Year)
2. (:Volumes)--[:Part_of]--->(:Journal)


