from flask import g
import sqlite3
import datetime
import os


DB_FILENAME = 'gardeners.db'


def adapt_datetime(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 string."""
    return val.isoformat(" ")


def convert_timestamp(val):
    """Convert ISO 8601 string to datetime.datetime."""
    return datetime.datetime.fromisoformat(val.decode())


sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_timestamp)


def open_db_connection():
    g.connection = sqlite3.connect(DB_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
    g.connection.row_factory = sqlite3.Row
    g.cursor = g.connection.cursor()


def close_db_connection():
    g.cursor.close()
    g.connection.close()


def all_accounts():
    g.cursor.execute('SELECT * FROM account ORDER BY email')
    return g.cursor.fetchall()


def find_account(email):
    g.cursor.execute('SELECT * FROM account WHERE email = :email', {'email': email})
    return g.cursor.fetchone()


def find_password(email):
    g.cursor.execute('SELECT password FROM account WHERE email = :email', {'email': email})
    return g.cursor.fetchone()


def all_listings():
    g.cursor.execute('SELECT * FROM listing ORDER BY id')
    return g.cursor.fetchall()


def find_listing(id):
    g.cursor.execute('SELECT * FROM listing WHERE id = :id', {'id': id})
    return g.cursor.fetchone()


def get_first_photo_path(listing_id):
    g.cursor.execute('SELECT file_path FROM photo WHERE listing_id = :listing_id', {'listing_id': listing_id})
    return g.cursor.fetchone()


def create_account(email, first_name, last_name, password):
    query = '''INSERT INTO account (email, first_name, last_name, password)
               VALUES (:email, :first_name, :last_name, :password)'''
    g.cursor.execute(query, {'email': email, 'first_name': first_name, 'last_name': last_name, 'password': password})
    g.connection.commit()
    return g.cursor.rowcount


def update_account(email, first_name, last_name, bio, password):
    if password:
        query = '''UPDATE account SET first_name = :first, last_name = :last, password = :pass, bio = :bio
                   WHERE email = :email'''
        g.cursor.execute(query, {'email': email, 'first': first_name, 'last': last_name, 'pass': password, 'bio': bio})
    else:
        query = '''UPDATE account SET first_name = :first, last_name = :last, bio = :bio
                           WHERE email = :email'''
        g.cursor.execute(query, {'email': email, 'first': first_name, 'last': last_name, 'bio': bio})
    g.connection.commit()
    return g.cursor.rowcount


def create_listing(name, quantity, description, price, account_email, unit):
    query = '''INSERT INTO listing (name, quantity, description, price, account_email, unit)
               VALUES (:name, :quantity, :description, :price, :account_email, :unit)'''
    g.cursor.execute(query, {'name': name, 'quantity': quantity, 'description': description, 'price': price,
                             'account_email': account_email, 'unit': unit})

    g.connection.commit()
    return g.cursor.lastrowid


def update_listing(id, name, quantity, description, price, unit):
    query = '''UPDATE listing SET name = :name, quantity = :quantity, description = :description,
               price = :price, unit = :unit WHERE id = :id'''
    g.cursor.execute(query, {'id': id, 'name': name, 'quantity': quantity, 'description': description, 'price': price,
                             'unit': unit})
    g.connection.commit()
    return g.cursor.rowcount


def buy_listing(id, quantity):
    query = '''UPDATE listing SET quantity = quantity - :quantity WHERE id = :id'''
    g.cursor.execute(query, {'id': id, 'quantity': quantity})
    g.connection.commit()
    return g.cursor.rowcount


def get_id_from_email(email):
    g.cursor.execute('SELECT id FROM account WHERE email = :email', {'email': email})
    row = g.cursor.fetchone()
    return row['id'] if row else None


def get_email_from_listing(id):
    g.cursor.execute('SELECT account_email FROM listing WHERE id = :id', {'id': id})
    row = g.cursor.fetchone()
    return row['account_email'] if row else None


def listings_by_account(account_email):
    check_expire_all()
    # BOOL in SQLite is 0/1, so expired = 0 (False)
    g.cursor.execute('SELECT * FROM listing WHERE account_email = :account_email AND expired = 0',
                     {'account_email': account_email})
    return g.cursor.fetchall()


def add_listing_photo_path(listing_id, file_path):
    g.cursor.execute("UPDATE listing SET file_path = :file_path WHERE id = :listing_id",
                     {'file_path': file_path, 'listing_id': listing_id})
    g.connection.commit()


def init_listing_photo(listing_id):
    """Create a photo record and return its ID"""
    query_dictionary = {'listing_id': listing_id}
    g.cursor.execute("INSERT INTO photo (listing_id) VALUES (:listing_id)", query_dictionary)
    g.connection.commit()

    # Return the new photo row (using lastrowid to fetch it)
    photo_id = g.cursor.lastrowid
    g.cursor.execute("SELECT * FROM photo WHERE id = :id", {'id': photo_id})
    return g.cursor.fetchone()


def set_photo(photo_id, file_path):
    """Update a photo record with the proper file name"""
    query = """
    UPDATE photo SET file_path = :file_path
    WHERE id = :id
    """
    g.cursor.execute(query, {'file_path': file_path, 'id': photo_id})
    g.connection.commit()
    return g.cursor.rowcount


def last_photo_seq():
    # SQLite uses `sqlite_sequence` for AUTOINCREMENT counters, but best to just use MAX(id) or similar if needed.
    # Postgres sequence logic: "SELECT last_value FROM photo_id_seq"
    # Replacing with MAX(id) from photo table
    g.cursor.execute('SELECT MAX(id) FROM photo')
    val = g.cursor.fetchone()[0]
    return val if val is not None else 0


def fetch_feed(num_listings, email=None):
    # print("fetch feed being ran")

    g.cursor.execute('SELECT * '
                     'FROM listing '
                     'WHERE quantity > 0 AND expired = 0 AND :email != listing.account_email '
                     'ORDER BY time_posted '
                     'LIMIT :num_listings', {'num_listings': num_listings, 'email': email})

    return g.cursor.fetchall()


def check_expire_listing(listing_id):
    g.cursor.execute('SELECT time_posted FROM listing WHERE id = :listing_id', {'listing_id': listing_id})
    row = g.cursor.fetchone()
    if not row:
        return

    time_posted = row['time_posted']
    if not time_posted:
        return

    if isinstance(time_posted, str):
        try:
            time_posted = datetime.datetime.strptime(time_posted, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return

    tdelta = datetime.datetime.now() - time_posted
    if tdelta.days > 10:
        g.cursor.execute('UPDATE listing SET expired = 1 WHERE id = :listing_id', {'listing_id': listing_id})
        g.connection.commit()


def check_expire_all():
    g.cursor.execute('SELECT id FROM listing WHERE expired = 0')
    ids = g.cursor.fetchall()
    for x in ids:
        check_expire_listing(x['id'])


def mark_favorite(account_email, favorites_email):
    query = '''INSERT INTO account_favorites (account_email, favorites_email)
               VALUES (:account_email, :favorites_email)'''
    g.cursor.execute(query, {'account_email': account_email, 'favorites_email': favorites_email})
    g.connection.commit()


def list_favorites(email):
    g.cursor.execute('SELECT * FROM account_favorites WHERE account_email = :email', {'email': email})
    return g.cursor.fetchall()


# Fetch_messages takes in the recipient and listing and renders
def fetch_messages(me, you):
    g.cursor.execute('SELECT * '
                     'FROM message '
                     'WHERE (author = :me AND recipient = :you) OR (author = :you AND recipient = :me)', {'me': me, 'you': you})
    return g.cursor.fetchall()
