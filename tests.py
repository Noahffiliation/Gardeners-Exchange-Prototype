import unittest
from unittest.mock import patch, MagicMock
import sys
import sqlite3
import os
import datetime

# db_config is gone, no need to mock it.

import db
from application import app, Account
from flask import g

# Schema script path
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'db', 'schema.sql')

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['WTF_CSRF_ENABLED'] = False
        app.testing = True
        self.client = app.test_client()
        self.app_context = app.test_request_context()
        self.app_context.push()

        # Patch sqlite3.connect to avoid real DB access in Controller tests
        self.connect_patcher = patch('sqlite3.connect')
        self.mock_connect = self.connect_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Ensure row_factory doesn't crash mock
        self.mock_conn.row_factory = None

        # Allow tests to mock g.connection/cursor if needed, though patching sqlite3 covers it
        g.connection = self.mock_conn
        g.cursor = self.mock_cursor

    def tearDown(self):
        self.connect_patcher.stop()
        self.app_context.pop()

class ApplicationTestCase(FlaskTestCase):

    def test_login(self):
        # Mock authenticate to return True (email)
        with patch('application.authenticate', return_value='test@example.com'), \
             patch('db.all_accounts', return_value=[]):

            response = self.client.post('/login', data=dict(
                email='test@example.com',
                password='test_password'
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
        # Mock return data as Dicts (to match sqlite3.Row behavior or DictCursor)
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
            password='test_password',
            confirm='test_password'
        ), follow_redirects=True)
        self.assertIn(b'Account new@test.com created', response.data)

        # Case 3: Account exists
        mock_find.return_value = {'email': 'exists@test.com'}
        response = self.client.post('/all_accounts/create', data=dict(
            email='exists@test.com',
            first_name='New',
            last_name='User',
            password='test_password',
            confirm='test_password'
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
        # Mocking generic dict access, must return datetime objects for templates
        from datetime import datetime
        mock_fetch.return_value = [
            {'id': 1, 'name': 'Item 1', 'price': 10, 'unit': 'lb', 'description': 'Desc', 'file_path': 'path', 'time_posted': datetime(2023, 1, 1)},
             {'id': 2, 'name': 'Item 2', 'price': 20, 'unit': 'kg', 'description': 'Desc 2', 'file_path': 'path', 'time_posted': datetime(2023, 1, 2)}
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
    def setUp(self):
        # Create an in-memory database with type detection
        self.db_conn = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_conn.row_factory = sqlite3.Row

        # Load Schema
        with open(SCHEMA_FILE, 'r') as f:
            self.db_conn.executescript(f.read())

        # Patch sqlite3.connect to return our shared in-memory connection
        self.connect_patcher = patch('sqlite3.connect')
        self.mock_connect = self.connect_patcher.start()
        self.mock_connect.return_value = self.db_conn

        self.app_context = app.app_context()
        self.app_context.push()

        # Initialize g.connection via db.open_db_connection (which calls mocked connect)
        db.open_db_connection()

    def tearDown(self):
        db.close_db_connection()
        self.app_context.pop()
        self.connect_patcher.stop()
        self.db_conn.close()

    def test_all_accounts(self):
        # Insert test data
        db.create_account('a@test.com', 'A', 'User', 'pass')
        db.create_account('b@test.com', 'B', 'User', 'pass')

        accounts = db.all_accounts()
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]['email'], 'a@test.com')

    def test_find_account(self):
        db.create_account('test@test.com', 'First', 'Last', 'pass')
        account = db.find_account('test@test.com')
        self.assertIsNotNone(account)
        self.assertEqual(account['email'], 'test@test.com')

    def test_create_account(self):
        count = db.create_account('new@test.com', 'New', 'User', 'pass')
        self.assertEqual(count, 1) # execute() return value is mostly rowcount/cursor, here db returns rowcount
        # Verify in DB
        acc = db.find_account('new@test.com')
        self.assertIsNotNone(acc)

    def test_create_listing(self):
        db.create_account('user@test.com', 'User', 'Name', 'pass')
        lid = db.create_listing('Item', 5, 'Desc', 10, 'user@test.com', 'lb')
        self.assertIsNotNone(lid)

        # Verify
        listing = db.find_listing(lid)
        self.assertEqual(listing['name'], 'Item')

    def test_fetch_feed(self):
        db.create_account('seller@test.com', 'Seller', 'One', 'pass')
        db.create_account('buyer@test.com', 'Buyer', 'Two', 'pass')
        db.create_listing('Item 1', 10, 'Details', 5, 'seller@test.com', 'lb')

        feed = db.fetch_feed(10, 'buyer@test.com')
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]['name'], 'Item 1')

        # Test my listings excluded
        feed_self = db.fetch_feed(10, 'seller@test.com')
        self.assertEqual(len(feed_self), 0)

    def test_update_listing(self):
        db.create_account('user@test.com', 'User', 'Name', 'pass')
        lid = db.create_listing('Old Name', 5, 'Desc', 10, 'user@test.com', 'lb')

        db.update_listing(lid, 'New Name', 10, 'New Desc', 20, 'kg')

        updated = db.find_listing(lid)
        self.assertEqual(updated['name'], 'New Name')

    def test_buy_listing(self):
        db.create_account('user@test.com', 'User', 'Name', 'pass')
        lid = db.create_listing('Item', 100, 'Desc', 10, 'user@test.com', 'lb')

        db.buy_listing(lid, 10)

        updated = db.find_listing(lid)
        self.assertEqual(updated['quantity'], 90)

    def test_get_first_photo_path(self):
        db.create_account('user@test.com', 'User', 'Name', 'pass')
        lid = db.create_listing('Item', 5, 'Desc', 10, 'user@test.com', 'lb')

        # Test that we can update the photo path
        photo_row = db.init_listing_photo(lid)
        db.set_photo(photo_row['id'], 'real.jpg')
        path_row = db.get_first_photo_path(lid)

        # Verify
        self.assertEqual(path_row['file_path'], 'real.jpg')

    def test_find_password(self):
        db.create_account('test@test.com', 'U', 'N', 'pass')
        pwd = db.find_password('test@test.com')
        self.assertEqual(pwd['password'], 'pass')

    def test_all_listings(self):
        db.create_account('u@t.com', 'F', 'L', 'p')
        db.create_listing('L1', 1, 'D', 1, 'u@t.com', 'u')
        db.create_listing('L2', 1, 'D', 1, 'u@t.com', 'u')
        listings = db.all_listings()
        self.assertEqual(len(listings), 2)

    def test_update_account(self):
        db.create_account('u@t.com', 'F', 'L', 'p')
        # Update with password
        db.update_account('u@t.com', 'NewF', 'NewL', 'Bio', 'newpass')
        acc = db.find_account('u@t.com')
        self.assertEqual(acc['first_name'], 'NewF')
        self.assertEqual(acc['password'], 'newpass')

        # Update without password
        db.update_account('u@t.com', 'NewF2', 'NewL2', 'Bio2', '')
        acc = db.find_account('u@t.com')
        self.assertEqual(acc['first_name'], 'NewF2')
        self.assertEqual(acc['password'], 'newpass') # Should remain unchanged

    def test_favorites(self):
        db.create_account('a@t.com', 'A', 'A', 'p')
        db.create_account('b@t.com', 'B', 'B', 'p')
        db.mark_favorite('a@t.com', 'b@t.com')
        favs = db.list_favorites('a@t.com')
        self.assertEqual(len(favs), 1)
        self.assertEqual(favs[0]['favorites_email'], 'b@t.com')

    def test_messages(self):
        # We need to manually insert messages since there is no helper create_message function in db.py exposed (check schema)
        # Schema: message (id, body, recipient, author, time, parent)
        # Actually there IS NO create_message function in db.py? Let's check db.py again later.
        # But fetch_messages exists.
        # Let's insert manually using cursor for now to test fetch.
        g.cursor.execute("INSERT INTO message (body, recipient, author, parent) VALUES ('Body', 'b@t.com', 'a@t.com', 1)")
        g.connection.commit()
        msgs = db.fetch_messages('a@t.com', 'b@t.com')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['body'], 'Body')

    def test_id_helpers(self):
        db.create_account('u@t.com', 'F', 'L', 'p')
        lid = db.create_listing('Item', 1, 'D', 1, 'u@t.com', 'u')

        uid = db.get_id_from_email('u@t.com')
        self.assertIsNotNone(uid)

        email = db.get_email_from_listing(lid)
        self.assertEqual(email, 'u@t.com')

    def test_photo_helpers(self):
        db.create_account('u@t.com', 'F', 'L', 'p')
        lid = db.create_listing('Item', 1, 'D', 1, 'u@t.com', 'u')

        # Test add_listing_photo_path (updates listing table)
        db.add_listing_photo_path(lid, 'test.jpg')
        l = db.find_listing(lid)
        self.assertEqual(l['file_path'], 'test.jpg')

        # Test last_photo_seq (uses photo table)
        # Need to insert a photo to test sequence logic if it relies on max(id)
        db.init_listing_photo(lid)
        seq = db.last_photo_seq()
        self.assertTrue(seq > 0)

    def test_expiration_logic(self):
        db.create_account('u@t.com', 'F', 'L', 'p')

        # Test 1: Not expired (posted now)
        lid1 = db.create_listing('Fresh', 1, 'D', 1, 'u@t.com', 'u')
        db.check_expire_listing(lid1)
        l1 = db.find_listing(lid1)
        self.assertEqual(l1['expired'], 0)

        # Test 2: Expired (posted 11 days ago)
        # We need to manually insert with old time because create_listing uses DEFAULT CURRENT_TIMESTAMP
        # or we update it.
        old_date = datetime.datetime.now() - datetime.timedelta(days=12)
        # We need to insert directly to override default, or update.
        # Update is easier but update_listing doesn't touch time_posted.
        # Let's insert manually with a specific ID to track it.
        g.cursor.execute('''INSERT INTO listing (name, quantity, description, price, unit, account_email, time_posted)
                            VALUES ('Old', 1, 'D', 1, 'u', 'u@t.com', :time)''', {'time': old_date})
        lid2 = g.cursor.lastrowid
        g.connection.commit()

        db.check_expire_listing(lid2)
        l2 = db.find_listing(lid2)
        self.assertEqual(l2['expired'], 1)

        # Test 3: String date handling (simulate legacy data or SQLite string returns without converter)
        # However, with converter registered, it usually comes back as datetime.
        # Use a raw insert of a string to bypass adapter if possible?
        # Or just trust the logic handles strings if they somehow exist.
        # To force a string check in check_expire_listing, we might need to mock the row return
        # but that tests the mock, not the DB logic.
        # If we insert a string that DOESN'T match ISO, check_expire_listing returns early.
        g.cursor.execute("INSERT INTO listing (name, quantity, description, price, unit, account_email, time_posted) VALUES ('BadDate', 1, 'D', 1, 'u', 'u@t.com', 'not-a-date')")
        lid3 = g.cursor.lastrowid
        g.connection.commit()

        db.check_expire_listing(lid3)
        l3 = db.find_listing(lid3)
        self.assertEqual(l3['expired'], 0) # Should not explode, just return

        # Test 4: check_expire_all
        # Reset lid2 to not expired manually to test check_expire_all
        g.cursor.execute("UPDATE listing SET expired = 0 WHERE id = :id", {'id': lid2})
        g.connection.commit()

        db.check_expire_all()
        l2_again = db.find_listing(lid2)
        self.assertEqual(l2_again['expired'], 1)

if __name__ == '__main__':
    unittest.main()


# Mock db_config before db is imported to prevent checks for real credentials or missing file
mock_db_config = MagicMock()
mock_db_config.data_source_name = "dbname=test user=mock password=mock_value host=localhost"
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
                password='test_password'
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
            password='test_password',
            confirm='test_password'
        ), follow_redirects=True)
        self.assertIn(b'Account new@test.com created', response.data)

        # Case 3: Account exists
        mock_find.return_value = {'email': 'exists@test.com'}
        response = self.client.post('/all_accounts/create', data=dict(
            email='exists@test.com',
            first_name='New',
            last_name='User',
            password='test_password',
            confirm='test_password'
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


if __name__ == '__main__':
    unittest.main()
