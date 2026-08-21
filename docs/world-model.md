# The World Model Substrate

We need a richer substrate for the world model. 

Fundamental concepts:

Entity: an instance of something abstract or concrete
Relationship: an instance of something that ties together entities or relationships. A relationship has roles and entities participating in a relationship are bound to that roles.

Dimension: something that has positions, so that entities and relationships can be placed in dimensions, either relatively one to another, or absolute. Numbers are a particular kind of dimension. Time is another dimension. Size is another dimension. E.g. bigger or smaller mean "before" or "after" on the size dimension. An absolute position is an entity. A relative position is a relationship over a dimension

List, Bag, Set, All, Some, count, greater, smaller: fundamental concepts (greater and smaller refer to dimensions)

Query: a criterion or set of criteria to match something.

narrower / wider. Applicable to query. A query could be said to be narrower or wider w.r.t. another. (substitution principle).

Span: an identified set of entities and relationships that can be treated as an entity.

Request: a "gravitational force" that pulls an action.

Python snippet:

class Instantiable:
    # just an empty python object

class Entity extends Instantiable: 
    positions: list[]

class Relationship:
    participants: list[str, Instantiable]    # str is the role

class Dimension:
    def compare(d: Dimension)

class Position