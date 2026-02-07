DROP TABLE IF EXISTS transaction_log; -- rename transaction to transaction_log to avoid keyword conflicts if any, though transaction is usually fine in sqlite but let's stick to simple names. Actually 'transaction' is a keyword.
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS photo;
DROP TABLE IF EXISTS listing_tag;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS listing;
DROP TABLE IF EXISTS account_favorites;
DROP TABLE IF EXISTS account;

CREATE TABLE account (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  first_name TEXT,
  last_name TEXT,
  password TEXT NOT NULL,
  bio TEXT DEFAULT NULL
);

CREATE TABLE account_favorites (
  account_email TEXT NOT NULL REFERENCES account (email),
  favorites_email TEXT NOT NULL REFERENCES account (email)
);

CREATE TABLE listing (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quantity REAL,
  description TEXT,
  price REAL NOT NULL,
  time_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  unit TEXT,
  account_email TEXT NOT NULL REFERENCES account (email),
  expired INTEGER NOT NULL DEFAULT 0, -- 0 for False, 1 for True
  file_path TEXT DEFAULT 'bogus_path'
);

CREATE TABLE transaction_log ( -- Renamed from transaction to avoid reserved word issues
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cost REAL NOT NULL,
  status TEXT,
  time TIMESTAMP NOT NULL,
  listing_id INTEGER NOT NULL REFERENCES listing (id),
  buyer_id INTEGER NOT NULL REFERENCES account (id),
  seller_id INTEGER NOT NULL REFERENCES account (id)
);

CREATE TABLE photo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_path TEXT DEFAULT 'bogus_path',
  listing_id INTEGER REFERENCES listing (id)
);

CREATE TABLE tag (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT
);

CREATE TABLE listing_tag (
  listing_id INTEGER NOT NULL REFERENCES listing (id),
  tag_id INTEGER NOT NULL REFERENCES tag (id),
  PRIMARY KEY (listing_id, tag_id)
);

CREATE TABLE message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  body TEXT NOT NULL,
  recipient INTEGER NOT NULL REFERENCES account (id),
  author INTEGER NOT NULL REFERENCES account (id),
  createdate DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  parent INTEGER REFERENCES message (id)
);
