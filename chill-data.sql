DROP TABLE if exists Chill;
DROP TABLE if exists Node;
DROP TABLE if exists Node_Node;
DROP TABLE if exists Query;
DROP TABLE if exists Route;
DROP TABLE if exists Template;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Chill (
    version integer
);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Node (
    id integer primary key,
    name varchar(255),
    value text,
    template integer,
    query integer,
    foreign key ( template ) references Template ( id ) on delete set null,
    foreign key ( query ) references Query ( id ) on delete set null
    );
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Node_Node (
    node_id integer,
    target_node_id integer,
    foreign key ( node_id ) references Node ( id ) on delete cascade,
    foreign key ( target_node_id ) references Node ( id ) on delete cascade
);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Query (
    id integer primary key,
    name varchar(255) not null
);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Route (
    id integer primary key,
    path text not null,
    node_id integer,
    weight integer default 0,
    method varchar(10) default 'GET',
    foreign key ( node_id ) references Node ( id ) on delete set null
);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Template (
    id integer primary key,
    name varchar(255) unique not null
);
COMMIT;
