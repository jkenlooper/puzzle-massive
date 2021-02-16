import sqlite3

from api.tools import loadConfig
from api.database import read_query_file, puzzle_features_init_list

if __name__ == "__main__":
    config_file = "site.cfg"
    config = loadConfig(config_file)

    db_file = config["SQLITE_DATABASE_URI"]
    db = sqlite3.connect(db_file)
    cur = db.cursor()

    ## Set puzzle features that are enabled
    puzzle_features = config.get("PUZZLE_FEATURES", set())
    print(f"Enabling puzzle features: {puzzle_features}")
    for query_file in puzzle_features_init_list(puzzle_features):
        cur.execute(read_query_file(query_file))
        db.commit()

    cur.close()
