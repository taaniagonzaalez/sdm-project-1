# Relationships between Nodes

## Paper Relationships:

(:Paper)--[:Cites]--->(:Paper)
(:Paper)--[:Contains]--->(:Topics)
(:Paper)--[:Starts_with]--->(:Abstract)
(:Paper)--[:Published_at]--->(:Edition)
(:Paper)--[:Published_at]--->(:Volume)
(:Paper)--[:Appear_in]--->(:Proceedings)

## Author Relationships:

(:Author)-[:WRITES {role: 'main', is_corresponding: true}]->(:Paper)
(:Author)-[:WRITES {role: 'co-author', is_corresponding: false}]->(:Paper)

## Edition Relationships:

(:Editions)--[:Part_of]--->(:Workshop)
(:Editions)--[:Part_of]--->(:Conference)
(:Editions)--[:Dated_in]--->(:Year)
(:Editions)--[:Placed_at]--->(:City)
(:Editions)--[:Has_proceedings]--->(:Proceedings)

## Volumes Relationships

(:Volumes)--[:Dated_in]--->(:Year)
(:Volumes)--[:Part_of]--->(:Journal)


