import unittest

from api.helper_tests import APITestCase

from api.database import fetch_query_string, rowify


class TestInternalTasksStartView(APITestCase):
    ""

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_non_existing_task(self):
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name="abc",),
                    json={"player": 2},
                )
                self.assertEqual(404, rv.status_code)
                self.assertEqual(
                    {"msg": "Task does not exist", "status_code": 404}, rv.json
                )

    def test_update_user_points_and_m_date_task(self):
        task_name = "update_user_points_and_m_date"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"bogus": 1},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"player": 2, "points": 20, "score": 2},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 1, "msg": "Executed", "status_code": 200}, rv.json
                )

    def test_update_bit_icon_expiration_task(self):
        task_name = "update_bit_icon_expiration"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"bogus": 1},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"player": 2},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": -1, "msg": "Executed", "status_code": 200}, rv.json
                )

    def test_update_points_to_minimum_for_all_users_task(self):
        task_name = "update_points_to_minimum_for_all_users"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"bogus": 1},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"minimum": 2000},
                )
                self.assertEqual(200, rv.status_code)
                # By default there is an admin user and anonymous user.
                self.assertEqual(
                    {"rowcount": 2, "msg": "Executed", "status_code": 200}, rv.json
                )

    def test_update_user_name_approved_for_approved_date_due_task(self):
        task_name = "update_user_name_approved_for_approved_date_due"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                    json={"bogus": 1},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data should be sent", "status_code": 400}, rv.json,
                )

                rv = c.post(
                    "/internal/tasks/{task_name}/start/".format(task_name=task_name,),
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 0, "msg": "Executed", "status_code": 200}, rv.json
                )


if __name__ == "__main__":
    unittest.main()
