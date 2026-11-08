from __future__ import annotations

import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path

from database.connection import Database, draw_identifier
from database.migrate import migrate
from database.verify import verify


class DatabaseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "nrc.db"
        migrate(self.path)

    def tearDown(self): self.temp.cleanup()

    def test_migrations_are_idempotent_and_database_is_valid(self):
        self.assertEqual(migrate(self.path), [])
        self.assertEqual(verify(self.path), [])

    def test_foreign_keys_strict_types_and_counters(self):
        db = Database(self.path)
        with db.write() as connection:
            self.assertEqual(draw_identifier(connection, "NRC"), 1)
            self.assertEqual(draw_identifier(connection, "NRC"), 2)
        with self.assertRaises(sqlite3.IntegrityError), db.write() as connection:
            connection.execute("INSERT INTO ref_office(id,office,state,status_reason,row_version) VALUES(?,?,?, ?, ?)", (str(uuid.uuid4()), "Bad", "active", "active", "not-an-int"))

    def test_hierarchy_trigger_rejects_mismatch(self):
        db = Database(self.path)
        goal_id, objective_id = str(uuid.uuid4()), str(uuid.uuid4())
        with db.write() as c:
            c.execute("INSERT INTO plan_goal(id,goal,sequence) VALUES(?,?,?)", (goal_id,"Goal",1))
            c.execute("INSERT INTO plan_objective(id,objective,sequence,goal_id) VALUES(?,?,?,?)", (objective_id,"Objective","1.1",goal_id))
            with self.assertRaisesRegex(sqlite3.IntegrityError, "HIERARCHY_MISMATCH"):
                c.execute("INSERT INTO plan_strategy(id,strategy,sequence,objective_id) VALUES(?,?,?,?)", (str(uuid.uuid4()),"Wrong","2.1.1",objective_id))

    def test_not_applicable_result_is_rejected(self):
        db = Database(self.path)
        with self.assertRaises(sqlite3.IntegrityError), db.write() as c:
            c.execute("PRAGMA defer_foreign_keys=ON")
            c.execute("INSERT INTO perf_pi_result_period(pi_result_id,period,results,not_applicable) VALUES(?,?,?,?)", (str(uuid.uuid4()),"q1",1.0,1))


if __name__ == "__main__": unittest.main()
