import requests
import unittest
from portal.engine import models, get_db


class TestRoutes(unittest.TestCase):
    BASE_URL = "http://localhost:8000/portal"

    @classmethod
    def setUpClass(cls):
        cls.db = next(get_db())

    def setUp(self):
        """ Create A User A Account And Login"""

        self.user_data = {
            'username': 'testuser1',
            'email': 'testuser1@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        self.user_response = requests.post(
            f"{self.BASE_URL}/register/", json=self.user_data)

        # Right Login Data
        self.login_data = {'email': 'testuser1@test.com',
                           'password': 'password123'}
        self.login_response = requests.post(
            f"{self.BASE_URL}/login/", json=self.login_data)
        self.cookies = self.login_response.cookies

        # Wrong Login Data
        self.wrong_login_data = {'email': 'testuser5@test.com',
                                 'password': 'password12'}
        self.wrong_login_response = requests.post(
            f"{self.BASE_URL}/login/", json=self.wrong_login_data)

    def tearDown(self):
        """ Delete A User Account"""

        delete_user = self.db.query(models.User).filter(
            models.User.username == self.user_data['username']).first()

        if delete_user:
            self.db.delete(delete_user)
            self.db.commit()

    def test_user_registration(self):
        self.assertEqual(self.user_response.status_code, 200)

    def test_user_login(self):
        self.assertEqual(self.login_response.status_code, 200)
        self.assertEqual(self.wrong_login_response.status_code, 401)
        # Check if access token is set in cookies
        # cookies = self.login_response.cookies
        # print(cookies['access_token'])
        # self.assertIn('access_token', cookies)

    def test_user_logout(self):
        logout_response = requests.get(f"{self.BASE_URL}/logout/")
        self.assertEqual(logout_response.status_code, 200)

    def test_home_route(self):
        """ Test Home Route Response """

        home_response = requests.get(f"{self.BASE_URL}")
        self.assertEqual(home_response.status_code, 200)

    def test_profile_route(self):
        """ Test Profile Route Data And Response """

        profile_response = requests.get(
            f"{self.BASE_URL}/profile/")
        self.assertEqual(profile_response.status_code, 200)

    def test_history_route(self):
        """Test History Route Data And Response"""

        history_response = requests.get(
            f"{self.BASE_URL}/history",
            cookies=self.cookies
        )
        self.assertEqual(history_response.status_code, 200)
