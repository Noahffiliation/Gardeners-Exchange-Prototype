import unittest
import db
from application import app, Account, login_user, logout_user, AccountForm
from flask import g, url_for


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True

        self.client = app.test_client(use_cookies=True)

        self.app_context = app.test_request_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()


class ApplicationTestCase(FlaskTestCase):
    @staticmethod
    def execute_sql(resource_name):
        with app.open_resource(resource_name, mode='r') as f:
            g.cursor.execute(f.read())
        g.connection.commit()

    def setUp(self):
        super(ApplicationTestCase, self).setUp()
        db.open_db_connection()
        self.execute_sql('DB/create-db.sql')

    def tearDown(self):
        db.close_db_connection()
        super(ApplicationTestCase, self).tearDown()

    # Application test functions go here
    # login
    def test_login(self):
        self.assertTrue(login_test_user(), "Login Failed")

    # logout
    def test_logout(self):
        login_test_user()
        self.assertTrue(logout_user(), "Logout Failed")

    # all_accounts
    def test_all_accounts(self):
        resp = self.client.get('/all_accounts')
        self.assertTrue(b'All Accounts' in resp.data, "Didn't find all accounts page")

    # find_account
    def test_find_account(self):
        db.create_account('test@example.com', 'First', 'Last', 'password')
        resp = self.client.get(url_for('find_account', email='test@example.com'))
        self.assertTrue(b"First's listings" in resp.data, "Could not find profile page")

    # create_account
    def test_create_account(self):
        account_form = AccountForm()
        account_form.email.data = 'test@example.com'
        account_form.first_name.data = 'First'
        account_form.last_name.data = 'Last'
        account_form.password.data = 'password'
        account_form.confirm.data = 'password'
        print(account_form)

        db.create_account(account_form.email.data, account_form.first_name.data, account_form.last_name.data,
                          account_form.password.data)
        account = Account(account_form.email.data)
        self.assertTrue(login_user(account))

        resp = self.client.get(url_for('create_account'))
        self.assertTrue(b'Create a new account' in resp.data)

    # update_account
    def test_update_account(self):
        login_test_user()
        db.update_account('test@example.com', 'Second', 'Third', 'A basic biography', 'password')

        resp = self.client.get(url_for('update_account', email='test@example.com'))
        self.assertTrue(b'Update account' in resp.data)

        resp = self.client.get(url_for('find_account', email='test@example.com'))
        self.assertTrue(b'A basic biography' in resp.data)

    # create_listing
    def test_create_listing(self):
        login_test_user()
        db.create_listing('test', 5, 'junk text', 10, 'test@example.com', 'pc')
        resp = self.client.get(url_for('render_feed'))
        self.assertTrue(b'test' in resp.data)

        resp = self.client.get(url_for('create_listing'), follow_redirects=True)
        self.assertTrue(b'Log In' in resp.data)

    # render_feed
    def test_render_feed(self):
        db.create_account('test1@example.com', 'First', 'Last', 'password')
        db.create_account('test2@example.com', 'First', 'Last', 'password')

        db.create_listing('Potatoes', 5, 'Some form of description', 5, 'test1@example.com', 'grams')
        db.create_listing('Bananas', 5, 'Some form of description', 5, 'test1@example.com', 'grams')
        db.create_listing('Tomatoes', 5, 'Some form of description', 5, 'test2@example.com', 'grams')
        db.create_listing('Apples', 5, 'Some form of description', 5, 'test2@example.com', 'grams')

        resp = self.client.get(url_for('render_feed'))
        self.assertTrue(b'Potatoes' in resp.data)
        self.assertTrue(b'Tomatoes' in resp.data)
        self.assertTrue(b'Bananas' in resp.data)
        self.assertTrue(b'Apples' in resp.data)


class DatabaseTestCase(FlaskTestCase):
    @staticmethod
    def execute_sql(resource_name):
        with app.open_resource(resource_name, mode='r') as f:
            g.cursor.execute(f.read())
        g.connection.commit()

    def setUp(self):
        super(DatabaseTestCase, self).setUp()
        db.open_db_connection()
        self.execute_sql('DB/create-db.sql')

    def tearDown(self):
        db.close_db_connection()
        super(DatabaseTestCase, self).tearDown()

    # db test functions go here
    # all_accounts
    def test_all_accounts(self):
        for i in range(1, 11):
            row_count = db.create_account('test{0}@example.com'.format(i), 'First', 'Last', 'password')
            self.assertEqual(row_count, 1)

            test_account = db.find_account('test{0}@example.com'.format(i))
            self.assertIsNotNone(test_account)

    # find_account
    def test_find_account(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

    # find_password
    def test_find_password(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

        test_password = db.find_password('test@example.com')
        self.assertIsNotNone(test_password)

        self.assertEqual(test_account['password'], 'password')

    # all_listings
    def test_all_listings(self):
        for i in range(1, 11):
            row_count = db.create_account('test{0}@example.com'.format(i), 'First', 'Last', 'password')
            self.assertEqual(row_count, 1)

            test_account = db.find_account('test{0}@example.com'.format(i))
            self.assertIsNotNone(test_account)

            listing_id = db.create_listing('Potatoes', 4, 'Basic description', 5,
                                          'test{0}@example.com'.format(i), 'pounds')
            print(listing_id)
            self.assertEqual(listing_id, 99+i)

            test_listing = db.find_listing(99 + i)
            print(test_listing)
            self.assertIsNotNone(test_listing)

    # find_listing
    def test_find_listing(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

        listing_id = db.create_listing('Potatoes', 5, 'Some form of description', 5, 'test@example.com', 'grams')
        self.assertEqual(listing_id, 100)

        test_listing = db.find_listing(100)
        print(test_listing)
        self.assertIsNotNone(test_listing)

    # create_account
    def test_create_account(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

        self.assertEqual(test_account['first_name'], 'First')
        self.assertEqual(test_account['last_name'], 'Last')

    # update_account
    def test_update_account(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        row_count = db.update_account('test@example.com', 'NewFirst', 'NewLast', 'A test bio', 'newpassword')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

        self.assertEqual(test_account['first_name'], 'NewFirst')
        self.assertEqual(test_account['last_name'], 'NewLast')

    # create_listing
    def test_create_listing(self):
        test_account = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertIsNotNone(test_account)

        listing_id = db.create_listing('Potatoes', 5, 'Some form of description', 5, 'test@example.com', 'grams')
        self.assertEqual(listing_id, 100)

        test_listing = db.find_listing(100)
        self.assertIsNotNone(test_listing)

        self.assertEqual(test_listing['name'], 'Potatoes')
        self.assertEqual(test_listing['quantity'], 5)
        self.assertEqual(test_listing['description'], 'Some form of description')
        self.assertEqual(test_listing['price'], 5)
        self.assertEqual(test_listing['account_email'], 'test@example.com')
        self.assertEqual(test_listing['unit'], 'grams')

    # get_id_from_email
    def test_get_id_from_email(self):
        row_count = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('test@example.com')
        self.assertIsNotNone(test_account)

        test_id = db.get_id_from_email('test@example.com')
        self.assertIsNotNone(test_id)

        self.assertEqual(test_id, 100)

    # listings_by_account
    def test_listings_by_account(self):
        row_count = db.create_account('one@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        row_count = db.create_account('two@example.com', 'First', 'Last', 'password')
        self.assertEqual(row_count, 1)

        test_account = db.find_account('one@example.com')
        self.assertIsNotNone(test_account)

        test_account = db.find_account('two@example.com')
        self.assertIsNotNone(test_account)

        listing_id = db.create_listing('Potatoes', 5, 'Some form of description', 5, 'one@example.com', 'grams')
        self.assertEqual(listing_id, 100)

        listing_id = db.create_listing('Watermelons', 1, 'Some form of description', 5, 'one@example.com', 'pounds')
        self.assertEqual(listing_id, 101)

        listing_id = db.create_listing('Potatoes', 5, 'Some form of description', 5, 'two@example.com', 'grams')
        self.assertEqual(listing_id, 102)

        test_listing = db.find_listing(100)
        self.assertIsNotNone(test_listing)

        test_listing = db.find_listing(101)
        self.assertIsNotNone(test_listing)

        test_listing = db.find_listing(102)
        self.assertIsNotNone(test_listing)

        test_listings = db.listings_by_account('one@example.com')
        self.assertEqual(test_listings[0][0], 100)
        self.assertEqual(test_listings[1][0], 101)

    # fetch_feed
    def test_fetch_feed(self):
        test_account = db.create_account('test@example.com', 'First', 'Last', 'password')
        self.assertIsNotNone(test_account)

        listing_id = db.create_listing('Potatoes', 0, 'Some form of description', 5, 'test@example.com', 'grams')
        self.assertEqual(listing_id, 100)

        listing_id = db.create_listing('Watermelons', 5, 'Some form of description', 5, 'test@example.com', 'pounds')
        self.assertEqual(listing_id, 101)

        listing_id = db.create_listing('Potatoes', 0, 'Some form of description', 5, 'test@example.com', 'grams')
        self.assertEqual(listing_id, 102)

        test_listing = db.find_listing(100)
        self.assertIsNotNone(test_listing)

        test_listing = db.find_listing(101)
        self.assertIsNotNone(test_listing)

        test_listing = db.find_listing(102)
        self.assertIsNotNone(test_listing)

        test_feed = db.fetch_feed(6)
        self.assertIsNotNone(test_feed)
        self.assertEqual(test_feed[0][0], 101)


def login_test_user():
    db.create_account('test@example.com', 'First', 'Last', 'password')
    account = Account('test@example.com')
    return login_user(account)


# Do the right thing if this file is run standalone
if __name__ == '__main__':
    unittest.main()
