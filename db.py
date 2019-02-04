from flask import g
import psycopg2
import psycopg2.extras
import datetime

import db_config


def open_db_connection():
    g.connection = psycopg2.connect(db_config.data_source_name)
    g.cursor = g.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)


def close_db_connection():
    g.cursor.close()
    g.connection.close()


def all_accounts():
    g.cursor.execute('SELECT * FROM account ORDER BY email')
    return g.cursor.fetchall()


def find_account(email):
    g.cursor.execute('SELECT * FROM account WHERE email = %(emailParam)s', {'emailParam': email})
    return g.cursor.fetchone()


def find_password(email):
    g.cursor.execute('SELECT password FROM account WHERE email = %(emailParam)s', {'emailParam': email})
    return g.cursor.fetchone()


def all_listings():
    g.cursor.execute('SELECT * FROM listing ORDER BY id')
    return g.cursor.fetchall()


def find_listing(id):
    g.cursor.execute('SELECT * FROM listing WHERE id = %(id)s', {'id': id})
    return g.cursor.fetchone()


def get_first_photo_path(listing_id):
    g.cursor.execute('SELECT file_path FROM photo WHERE listing_id = %(listing_id)s', {'listing_id': listing_id})
    return g.cursor.fetchone()


def create_account(email, first_name, last_name, password):
    query = '''INSERT INTO account (email, first_name, last_name, password)
               VALUES (%(email)s, %(first_name)s, %(last_name)s, %(password)s)'''
    g.cursor.execute(query, {'email': email, 'first_name': first_name, 'last_name': last_name, 'password': password})
    g.connection.commit()
    return g.cursor.rowcount


def update_account(email, first_name, last_name, bio, password):
    if password:
        query = '''UPDATE account SET first_name = %(first)s, last_name = %(last)s, password = %(pass)s, bio = %(bio)s
                   WHERE email = %(email)s'''
        g.cursor.execute(query, {'email': email, 'first': first_name, 'last': last_name, 'pass': password, 'bio': bio})
        g.connection.commit()
    else:
        query = '''UPDATE account SET first_name = %(first)s, last_name = %(last)s, bio = %(bio)s
                           WHERE email = %(email)s'''
        g.cursor.execute(query, {'email': email, 'first': first_name, 'last': last_name, 'bio': bio})
        g.connection.commit()
    return g.cursor.rowcount


def create_listing(name, quantity, description, price, account_email, unit):
    query = '''INSERT INTO listing (name, quantity, description, price, account_email, unit)
               VALUES (%(name)s, %(quantity)s, %(description)s, %(price)s, %(account_email)s, %(unit)s) RETURNING id'''
    g.cursor.execute(query, {'name': name, 'quantity': quantity, 'description': description, 'price': price,
                             'account_email': account_email, 'unit': unit})

    g.connection.commit()
    new_listing_id = g.cursor.fetchone()[0]
    return new_listing_id


def update_listing(id, name, quantity, description, price, unit):
    query = '''UPDATE listing SET name = %(name)s, quantity = %(quantity)s, description = %(description)s, 
               price = %(price)s, unit = %(unit)s WHERE id = %(id)s'''
    g.cursor.execute(query, {'id': id, 'name': name, 'quantity': quantity, 'description': description, 'price': price,
                             'unit': unit})
    g.connection.commit()
    return g.cursor.rowcount


def buy_listing(id, quantity):
    query = '''UPDATE listing SET quantity = quantity-%(quantity)s WHERE ID = %(id)s'''
    g.cursor.execute(query, {'id': id, 'quantity': quantity})
    g.connection.commit()
    return g.cursor.rowcount


def get_id_from_email(emailParam):
    g.cursor.execute('SELECT id FROM account WHERE email = %(emailParam)s', {'emailParam': emailParam})
    return g.cursor.fetchone()[0]


def get_email_from_listing(id):
    g.cursor.execute('SELECT account_email FROM listing WHERE id = %(id)s', {'id': id})
    return g.cursor.fetchone()[0]


def listings_by_account(account_email):
    check_expire_all()
    g.cursor.execute('SELECT * FROM listing WHERE account_email = %(account_email)s AND expired = FALSE',
                     {'account_email': account_email})
    return g.cursor.fetchall()


def add_listing_photo_path(listing_id, file_path):
    g.cursor.execute("UPDATE listing SET file_path = %(file_path)s WHERE id = %(listing_id)s",
                     {'file_path': file_path, 'listing_id': listing_id})
    g.connection.commit()


def init_listing_photo(listing_id):
    """Create a photo record and return its ID"""
    query_dictionary = {'listing_id': listing_id}
    g.cursor.execute("INSERT INTO photo (listing_id) VALUES (%(listing_id)s)", query_dictionary)
    g.connection.commit()

    g.cursor.execute("SELECT * FROM photo WHERE listing_id = (%(listing_id)s)", query_dictionary)
    return g.cursor.fetchone()


def set_photo(photo_id, file_path):
    """Update a photo record with the proper file name"""
    query = """
    UPDATE photo SET file_path = %(file_path)s
    WHERE id = %(id)s
    """
    g.cursor.execute(query, {'file_path': file_path, 'id': photo_id})
    g.connection.commit()
    return g.cursor.rowcount


def last_photo_seq():
    g.cursor.execute('SELECT last_value FROM photo_id_seq')
    return g.cursor.fetchone()[0]


def fetch_feed(num_listings, email=None):
    # print("fetch feed being ran")

    g.cursor.execute('SELECT * '
                     'FROM listing '
                     'WHERE quantity > 0 AND NOT expired AND %(email)s != listing.account_email '
                     'ORDER BY time_posted '
                     'LIMIT %(num_listings)s', {'num_listings': num_listings, 'email': email})

    return g.cursor.fetchall()


def check_expire_listing(listing_id):
    g.cursor.execute('SELECT time_posted FROM listing WHERE id = %(listing_id)s', {'listing_id': listing_id})
    time_posted = g.cursor.fetchone()[0]
    tdelta = datetime.datetime.now() - time_posted
    if tdelta.days > 10:
        g.cursor.execute('UPDATE listing SET expired = TRUE WHERE id = %(listing_id)s', {'listing_id': listing_id})
        g.connection.commit()


def check_expire_all():
    g.cursor.execute('SELECT id FROM listing WHERE expired = FALSE')
    ids = g.cursor.fetchall()
    for x in ids:
        check_expire_listing(x[0])


def mark_favorite(account_email, favorites_email):
    query = '''INSERT INTO account_favorites (account_email, favorites_email) 
               VALUES (%(account_email)s, %(favorites_email)s)'''
    g.cursor.execute(query, {'account_email': account_email, 'favorites_email': favorites_email})
    g.connection.commit()


def list_favorites(email):
    g.cursor.execute('SELECT * FROM account_favorites WHERE account_email = %(email)s', {'email': email})
    return g.cursor.fetchall()


# Fetch_messages takes in the recipient and listing and renders
def fetch_messages(me, you):
    # g.cursor.execute('SELECT * FROM message WHERE author = %{me}s AND recepient = %{you}s OR WHERE author=%{you}% AND recepient=%{me}%')
    g.cursor.execute('SELECT * '
                     'FROM message '
                     'WHERE author = %(me)s AND recipient = %(you)s OR author=%(you)s AND recipient=%(me)s', {'me': me, 'you': you})
    return g.cursor.fetchall()
