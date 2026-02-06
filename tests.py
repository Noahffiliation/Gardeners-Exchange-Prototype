import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock db_config before db is imported to prevent checks for real credentials or missing file
mock_db_config = MagicMock()
mock_db_config.data_source_name = "dbname=test user=mock password=mock host=localhost"
sys.modules['db_config'] = mock_db_config

import db
from application import app, Account
from flask import g

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing
        app.testing = True
        self.client = app.test_client()
        self.app_context = app.test_request_context()
        self.app_context.push()

        # Patch db connection management globally for the lifecycle of the test
        self.open_patcher = patch('db.open_db_connection')
        self.close_patcher = patch('db.close_db_connection')
        self.mock_open = self.open_patcher.start()
        self.mock_close = self.close_patcher.start()

        # Mock g.cursor/connection to prevent AttributeError if code accesses it strictly
        g.connection = MagicMock()
        g.cursor = MagicMock()

    def tearDown(self):
        self.open_patcher.stop()
        self.close_patcher.stop()
        self.app_context.pop()

class ApplicationTestCase(FlaskTestCase):

    def test_login(self):
        # Mock authenticate to return True (email)
        with patch('application.authenticate', return_value='test@example.com'), \
             patch('db.all_accounts', return_value=[]):

            response = self.client.post('/login', data=dict(
                email='test@example.com',
                password='password'
            ), follow_redirects=True)
            self.assertIn(b'Logged in successfully', response.data)

    @patch('application.logout_user')
    def test_logout(self, mock_logout):
        with self.client.session_transaction() as sess:
           sess['_user_id'] = 'test@example.com'

        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Logged out', response.data)

    @patch('db.all_accounts')
    def test_all_accounts(self, mock_all_accounts):
        # Mock return data as Dicts (to match DictCursor)
        mock_all_accounts.return_value = [
            {'id': 1, 'email': 'one@test.com', 'first_name': 'One', 'last_name': 'User', 'password': 'pass', 'bio': 'Bio 1'},
            {'id': 2, 'email': 'two@test.com', 'first_name': 'Two', 'last_name': 'User', 'password': 'pass', 'bio': 'Bio 2'}
        ]

        response = self.client.get('/all_accounts')
        self.assertIn(b'One', response.data)
        self.assertIn(b'Two', response.data)

    @patch('db.find_account')
    @patch('db.listings_by_account')
    def test_find_account(self, mock_listings, mock_find):
        # Mock account found
        mock_find.return_value = {'email': 'test@example.com', 'first_name': 'First', 'last_name': 'Last', 'bio': 'Bio'}
        mock_listings.return_value = []

        response = self.client.get('/find_account/test@example.com')
        self.assertIn(b'First', response.data)
        self.assertIn(b'Bio', response.data)

        # Test 404
        mock_find.return_value = None
        response = self.client.get('/find_account/missing@example.com', follow_redirects=True)
        self.assertIn(b'404 Account not found', response.data)

    @patch('db.create_account')
    @patch('db.find_account')
    def test_create_account(self, mock_find, mock_create):
        # Case 1: GET request
        response = self.client.get('/all_accounts/create')
        self.assertIn(b'Create a new account', response.data)

        # Case 2: POST success
        mock_find.return_value = None
        mock_create.return_value = 1

        response = self.client.post('/all_accounts/create', data=dict(
            email='new@test.com',
            first_name='New',
            last_name='User',
            password='password',
            confirm='password'
        ), follow_redirects=True)
        self.assertIn(b'Account new@test.com created', response.data)

        # Case 3: Account exists
        mock_find.return_value = {'email': 'exists@test.com'}
        response = self.client.post('/all_accounts/create', data=dict(
            email='exists@test.com',
            first_name='New',
            last_name='User',
            password='password',
            confirm='password'
        ), follow_redirects=True)
        self.assertIn(b'Account exists@test.com already exists', response.data)

    @patch('db.update_account')
    @patch('db.find_account')
    def test_update_account(self, mock_find, mock_update):
        mock_find.return_value = {'email': 'test@test.com', 'first_name': 'Old', 'last_name': 'Name', 'bio': 'Old Bio', 'password': 'pass'}

        with self.client.session_transaction() as sess:
           sess['_user_id'] = 'test@test.com'

        response = self.client.get('/all_accounts/update/test@test.com')
        self.assertIn(b'Update account', response.data)

        mock_update.return_value = 1
        response = self.client.post('/all_accounts/update/test@test.com', data=dict(
            email='test@test.com',
            first_name='Unknown',
            last_name='Name',
            bio='Old Bio',
            password='pass',
            confirm='pass'
        ), follow_redirects=True)
        self.assertIn(b'Account test@test.com updated', response.data)

    @patch('db.fetch_feed')
    def test_render_feed(self, mock_fetch):
        mock_fetch.return_value = [
            {'id': 1, 'name': 'Item 1', 'price': 10, 'unit': 'lb', 'description': 'Desc', 'file_path': 'path', 'time_posted': MagicMock(strftime=lambda x: 'Date')},
             {'id': 2, 'name': 'Item 2', 'price': 20, 'unit': 'kg', 'description': 'Desc 2', 'file_path': 'path', 'time_posted': MagicMock(strftime=lambda x: 'Date')}
        ]

        response = self.client.get('/feed')
        self.assertIn(b'Item 1', response.data)
        self.assertIn(b'Item 2', response.data)

    @patch('db.create_listing')
    @patch('db.add_listing_photo_path')
    @patch('werkzeug.datastructures.FileStorage.save')
    def test_create_listing_route(self, mock_save, mock_add_photo, mock_create):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 'test@example.com'

        # Test GET
        response = self.client.get('/all_listings/create')
        self.assertEqual(response.status_code, 200)

        # Test POST
        mock_create.return_value = 1

        with open('tests.py', 'rb') as f:
            data = {
                'name': 'Test Item',
                'quantity': 1,
                'description': 'Desc',
                'price': 10,
                'unit': 'kg',
                'photo': (f, 'tests.py')
            }
            response = self.client.post('/all_listings/create', data=data, follow_redirects=True, content_type='multipart/form-data')
            self.assertIn(b'Listing Test Item created', response.data)

    @patch('db.update_listing')
    @patch('db.find_listing')
    @patch('db.get_first_photo_path')
    @patch('db.get_email_from_listing')
    def test_update_listing_route(self, mock_email, mock_photo, mock_find, mock_update):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 'test@example.com'

        mock_find.return_value = {'id': 1, 'account_email': 'test@example.com', 'name': 'Old', 'price': 5, 'unit': 'lb', 'description': 'desc', 'quantity': 5}
        mock_photo.return_value = ['path.jpg']
        mock_email.return_value = 'test@example.com'

        # Test GET
        response = self.client.get('/all_listings/update/1')
        self.assertEqual(response.status_code, 200)

        mock_update.return_value = 1

        # Test POST
        response = self.client.post('/all_listings/update/1', data={
            'name': 'New',
            'quantity': 10,
            'description': 'New D',
            'price': 20,
            'unit': 'kg'
            # photo optional
        }, follow_redirects=True)
        self.assertIn(b'Listing New updated', response.data)

    @patch('db.buy_listing')
    @patch('db.find_listing')
    def test_buy_listing_route(self, mock_find, mock_buy):
        with self.client.session_transaction() as sess:
           sess['_user_id'] = 'test@example.com'

        mock_find.return_value = {'id': 1, 'quantity': 100, 'unit': 'lb', 'name': 'Item'}
        mock_buy.return_value = 1

        # Test valid buy
        response = self.client.post('/feed/buy/1/10', follow_redirects=True)
        self.assertIn(b'You bought 10 lb of Item', response.data)

        # Test invalid buy
        response = self.client.post('/feed/buy/1/200', follow_redirects=True)
        self.assertIn(b'Invalid amount', response.data)

    @patch('db.list_favorites')
    @patch('db.find_account')
    def test_favorites_route(self, mock_find, mock_favs):
        with self.client.session_transaction() as sess:
             sess['_user_id'] = 'test@example.com'

        mock_find.return_value = {'email': 'target@test.com'}
        mock_favs.return_value = []

        response = self.client.get('/favorites/target@test.com')
        self.assertIn(b'Favorites', response.data)

        # Test 404
        mock_find.return_value = None
        response = self.client.get('/favorites/missing@test.com', follow_redirects=True)
        self.assertIn(b'404 Account not found', response.data)

    def test_about(self):
        with patch('db.all_accounts', return_value=[]):
            response = self.client.get('/about')
            self.assertIn(b'About', response.data)


class DatabaseTestCase(unittest.TestCase):
    @patch('psycopg2.connect')
    def setUp(self, mock_connect):
        self.mock_connect = mock_connect
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        self.app_context = app.app_context()
        self.app_context.push()

        db.open_db_connection()

    def tearDown(self):
        db.close_db_connection()
        self.app_context.pop()

    def test_all_accounts(self):
        db.all_accounts()
        self.mock_cursor.execute.assert_called_with('SELECT * FROM account ORDER BY email')

    def test_find_account(self):
        db.find_account('test@test.com')
        self.mock_cursor.execute.assert_called_with('SELECT * FROM account WHERE email = %(emailParam)s', {'emailParam': 'test@test.com'})

    def test_create_account(self):
        db.create_account('test@test.com', 'First', 'Last', 'pass')
        args, kwargs = self.mock_cursor.execute.call_args
        self.assertIn('INSERT INTO account', args[0])
        self.assertEqual(args[1], {'email': 'test@test.com', 'first_name': 'First', 'last_name': 'Last', 'password': 'pass'})
        self.mock_conn.commit.assert_called()

    def test_create_listing(self):
        self.mock_cursor.fetchone.return_value = [101]
        lid = db.create_listing('Item', 5, 'Desc', 10, 'user@test.com', 'lb')
        args, kwargs = self.mock_cursor.execute.call_args
        self.assertIn('INSERT INTO listing', args[0])
        self.assertEqual(args[1]['name'], 'Item')
        self.assertEqual(lid, 101)

    def test_fetch_feed(self):
        db.fetch_feed(10, 'user@test.com')
        args, kwargs = self.mock_cursor.execute.call_args
        self.assertIn('SELECT * FROM listing', args[0])
        self.assertEqual(args[1]['num_listings'], 10)
        self.assertEqual(args[1]['email'], 'user@test.com')

    def test_update_listing(self):
        db.update_listing(1, 'New Name', 10, 'New Desc', 20, 'kg')
        args, kwargs = self.mock_cursor.execute.call_args
        self.assertIn('UPDATE listing', args[0])
        self.assertEqual(args[1]['name'], 'New Name')

    def test_buy_listing(self):
        db.buy_listing(1, 1)
        args, kwargs = self.mock_cursor.execute.call_args
        self.assertIn('UPDATE listing SET quantity', args[0])

    def test_find_listing(self):
        db.find_listing(1)
        self.mock_cursor.execute.assert_called_with('SELECT * FROM listing WHERE id = %(id)s', {'id': 1})

    def test_get_first_photo_path(self):
        db.get_first_photo_path(1)
        self.mock_cursor.execute.assert_called_with('SELECT file_path FROM photo WHERE listing_id = %(listing_id)s', {'listing_id': 1})

if __name__ == '__main__':
    unittest.main()
