import json

from src.app import app

from .requests.login_requests import client, LoginRequests, resource
from .requests.admin_requests import AdminRequests
from .requests.basic_requests import BasicRequests


class TestLoginRoutes:
    """ Class contain tests for login routes """

    def test_login_logout(self, client):
        """Make sure login and logout works."""

        # register new user
        BasicRequests.register(client, app.config['EMAIL'], app.config['USERNAME'], app.config['PASSWORD'],
                               app.config['FIRST_NAME'], app.config['LAST_NAME'], app.config['PHONE'])
        # login as new user
        rv = LoginRequests.login(client, app.config['EMAIL'], app.config['PASSWORD'])
        assert bytes(f'You are LOGGED IN as {app.config["EMAIL"]}', encoding='utf-8') in rv.data in rv.data

        # get user id - user_id used in the end of test for delete user
        rv = AdminRequests.get_user_by_username(client, app.config['USERNAME'])

        user = json.loads(str(rv.data, encoding='utf-8'))
        user_id = user['id']

        rv = BasicRequests.smoke(client)
        assert b'OK' in rv.data

        rv = AdminRequests.delete_user(client, str(user_id))
        assert bytes(f'User ID:{user_id} has been DELETED.', encoding='utf-8') in rv.data

        rv = BasicRequests.smoke(client)
        assert b'You are not allowed to use this resource without logging in!' in rv.data

        rv = LoginRequests.login(client, app.config['EMAIL'] + 'x', app.config['PASSWORD'])
        assert b'Could not verify your login!' in rv.data

        rv = LoginRequests.login(client, app.config['EMAIL'], app.config['PASSWORD'] + 'x')
        assert b'Could not verify your login!' in rv.data

    def test_logout(self, client):
        BasicRequests.register(client, app.config['EMAIL'], app.config['USERNAME'], app.config['PASSWORD'],
                               app.config['FIRST_NAME'], app.config['LAST_NAME'], app.config['PHONE'])
        LoginRequests.login(client, app.config['EMAIL'], app.config['PASSWORD'])
        rv = AdminRequests.get_user_by_username(client, app.config['USERNAME'])
        user = json.loads(str(rv.data, encoding='utf-8'))
        user_id = user['id']
        rv = LoginRequests.logout(client)
        assert b'Dropped' in rv.data
        LoginRequests.login(client, app.config['EMAIL'], app.config['PASSWORD'])
        AdminRequests.delete_user(client, str(user_id))
