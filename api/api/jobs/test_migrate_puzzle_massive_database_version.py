import unittest

from api.app import db
from api.database import rowify, read_query_file

from api.helper_tests import APITestCase
from api.jobs.migrate_puzzle_massive_database_version import (
    MigrateError,
    MigrateGapError,
    get_next_migrate_script
)
from api.tools import version_number, get_latest_version_based_on_migrate_scripts


class PuzzleMassiveDatabaseVersionTest(APITestCase):
    def test_connection(self):
        "Connection to db"
        with self.app.app_context():
            with self.app.test_client():
                cursor = db.cursor()
                result = cursor.execute("select 'test' as test")
                (result, col_names) = rowify(result, cursor.description)
                assert result[0]["test"] == "test"

    def test_version_number(self):
        "Parse version number from script file path"
        script_files = [
            "some/path/to/migrate_puzzle_massive_database_version_021.py",
            "some/path/to/migrate_puzzle_massive_database_version_901.py",
            "some/path/to/migrate_puzzle_massive_database_version_001.py",
            "some/path/to/migrate_puzzle_massive_database_version_000.py",
        ]

        version_numbers = list(map(version_number, script_files))

        assert version_numbers == [21, 901, 1, 0]

    def test_get_latest_version_based_on_migrate_scripts(self):
        "Get latest version based on migrate scripts"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                db.commit()
                script_files = [
                    "some/path/to/migrate_puzzle_massive_database_version_021.py",
                    "some/path/to/migrate_puzzle_massive_database_version_901.py",
                    "some/path/to/migrate_puzzle_massive_database_version_001.py",
                    "some/path/to/migrate_puzzle_massive_database_version_000.py",
                    "some/path/to/migrate_puzzle_massive_database_version_002.py",
                ]

                latest_version = get_latest_version_based_on_migrate_scripts(script_files)

                assert latest_version == 902

    def test_get_latest_version_when_no_migrate_scripts(self):
        "Get latest version when no migrate scripts"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                db.commit()
                script_files = []

                self.assertRaises(Exception, get_latest_version_based_on_migrate_scripts, script_files)

    def test_next_migrate_script_when_none_are_found(self):
        "Get next migrate script when none are found"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                db.commit()
                script_files = []

                self.assertRaises(MigrateError, get_next_migrate_script, script_files)

    def test_next_migrate_script_for_initial_migration(self):
        "Get next migrate script to run for the initial migration"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                db.commit()
                script_files = [
                    "some/path/to/migrate_puzzle_massive_database_version_021.py",
                    "some/path/to/migrate_puzzle_massive_database_version_901.py",
                    "some/path/to/migrate_puzzle_massive_database_version_001.py",
                    "some/path/to/migrate_puzzle_massive_database_version_000.py",
                    "some/path/to/migrate_puzzle_massive_database_version_002.py",
                ]

                migrate_script = get_next_migrate_script(script_files)

                # The initial one should be migrate_puzzle_massive_database_version_000.py
                assert migrate_script == "some/path/to/migrate_puzzle_massive_database_version_000.py"

    def test_next_migrate_script(self):
        "Get next migrate script to run"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                cur.execute(read_query_file("upsert_puzzle_massive.sql"), {
                    "key": "database_version",
                    "label": "Database Version",
                    "description": "something",
                    "intvalue": 1,
                    "textvalue": None,
                    "blobvalue": None
                })
                db.commit()
                script_files = [
                    "some/path/to/migrate_puzzle_massive_database_version_021.py",
                    "some/path/to/migrate_puzzle_massive_database_version_901.py",
                    "some/path/to/migrate_puzzle_massive_database_version_001.py",
                    "some/path/to/migrate_puzzle_massive_database_version_000.py",
                    "some/path/to/migrate_puzzle_massive_database_version_002.py",
                ]

                migrate_script = get_next_migrate_script(script_files)

                # The initial one should be migrate_puzzle_massive_database_version_000.py
                assert migrate_script == "some/path/to/migrate_puzzle_massive_database_version_002.py"

    def test_next_migrate_script_when_at_latest(self):
        "Get next migrate script to run when at latest version"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                cur.execute(read_query_file("upsert_puzzle_massive.sql"), {
                    "key": "database_version",
                    "label": "Database Version",
                    "description": "something",
                    "intvalue": 901,
                    "textvalue": None,
                    "blobvalue": None
                })
                db.commit()
                script_files = [
                    "some/path/to/migrate_puzzle_massive_database_version_021.py",
                    "some/path/to/migrate_puzzle_massive_database_version_901.py",
                    "some/path/to/migrate_puzzle_massive_database_version_001.py",
                    "some/path/to/migrate_puzzle_massive_database_version_000.py",
                    "some/path/to/migrate_puzzle_massive_database_version_002.py",
                ]

                migrate_script = get_next_migrate_script(script_files)

                assert migrate_script is None

    def test_next_migrate_script_when_a_gap_exists(self):
        "Get next migrate script to run when a gap in version numbers exist"
        with self.app.app_context():
            with self.app.test_client():
                cur = db.cursor()
                cur.execute(read_query_file("create_table_puzzle_massive.sql"))
                cur.execute(read_query_file("upsert_puzzle_massive.sql"), {
                    "key": "database_version",
                    "label": "Database Version",
                    "description": "something",
                    "intvalue": 21,
                    "textvalue": None,
                    "blobvalue": None
                })
                db.commit()
                script_files = [
                    "some/path/to/migrate_puzzle_massive_database_version_021.py",
                    "some/path/to/migrate_puzzle_massive_database_version_901.py",
                    "some/path/to/migrate_puzzle_massive_database_version_001.py",
                    "some/path/to/migrate_puzzle_massive_database_version_000.py",
                    "some/path/to/migrate_puzzle_massive_database_version_002.py",
                ]

                self.assertRaises(MigrateGapError, get_next_migrate_script, script_files)


if __name__ == "__main__":
    unittest.main()
