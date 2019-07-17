#!/bin/bash

if test "$1"; then
    echo "creating chill-data.sql for sqlite3 database: $1";
else
    echo "No db arg";
    exit 1;
fi

# Recreate the chill-data.sql which is used to update database

echo '.dump Chill' | sqlite3 $1 >> chill-data.sql
echo '.dump Node' | sqlite3 $1 >> chill-data.sql
echo '.dump Node_Node' | sqlite3 $1 >> chill-data.sql
echo '.dump Query' | sqlite3 $1 >> chill-data.sql
echo '.dump Route' | sqlite3 $1 >> chill-data.sql
echo '.dump Template' | sqlite3 $1 >> chill-data.sql
