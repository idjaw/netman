import unittest
from multiprocessing.pool import ThreadPool

from hamcrest import assert_that
from hamcrest import is_
from tests.system_tests import NetmanTestApp, get_available_switch, create_session


class LockingTest(unittest.TestCase):

    def test_starting_a_session_on_the_same_switch_waits_for_previous_session_to_finish(self):
        with NetmanTestApp(session_inactivity_timeout=2) as partial_client:
            client = partial_client(get_available_switch("cisco"))

            pool = ThreadPool(processes=1)

            result = create_session(client, "my_session")
            session_id = result.json()['session_id']
            client.post("/switches-sessions/" + session_id + "/actions", data='start_transaction')

            async_result = pool.apply_async(create_session, (client, "my_session2"))

            result = client.post("/switches-sessions/my_session/actions", data='commit')
            assert_that(result.status_code, is_(204), result.text)

            assert_that(async_result.ready(), is_(False))

            client.post("/switches-sessions/" + session_id + "/actions", data='end_transaction')
            result = client.delete("/switches-sessions/{}".format(session_id))
            assert_that(result.status_code, is_(204), result.text)

            result = async_result.get(timeout=2)
            assert_that(result.status_code, is_(201), result.text)

