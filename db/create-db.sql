DROP TABLE IF EXISTS transaction;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS photo, listing_tag, tag, listing;
DROP TABLE IF EXISTS account_favorites, account;

CREATE TABLE account
(
  id         SERIAL      NOT NULL
    CONSTRAINT account_id_pk
    PRIMARY KEY,
  email      VARCHAR2(128) NOT NULL UNIQUE,
  first_name VARCHAR2(64),
  last_name  VARCHAR2(64),
  password   VARCHAR2(64) NOT NULL,
  bio        VARCHAR2(2048) DEFAULT NULL
);

CREATE TABLE account_favorites
(
  account_email   VARCHAR2(128) NOT NULL REFERENCES account (email),
  favorites_email VARCHAR2(128) NOT NULL REFERENCES account (email)
);

CREATE TABLE listing
(
  id     SERIAL      NOT NULL
    CONSTRAINT  listing_id_pk
    PRIMARY KEY,
  name        VARCHAR2(64) NOT NULL,
  quantity    DOUBLE PRECISION,
  description VARCHAR2(512),
  price       FLOAT       NOT NULL,
  time_posted TIMESTAMP DEFAULT (now() at time zone 'ast'),
  unit        VARCHAR2(32),
  account_email  VARCHAR2(128)     NOT NULL  REFERENCES account (email),
  expired     BOOLEAN     NOT NULL DEFAULT FALSE,
  file_path   VARCHAR2(255) DEFAULT 'bogus_path'
);


CREATE TABLE transaction
(
  id       SERIAL           NOT NULL
    CONSTRAINT transaction_pkey
    PRIMARY KEY,
  cost     DOUBLE PRECISION NOT NULL,
  status   VARCHAR2(32),
  time     TIMESTAMP        NOT NULL,
  listing_id  SERIAL           NOT NULL  REFERENCES listing (id),
  buyer_id SERIAL           NOT NULL  REFERENCES account (id),
  seller_id SERIAL          NOT NULL  REFERENCES account (id)
);

CREATE UNIQUE INDEX transaction_id_uindex
  ON transaction (id);

CREATE TABLE photo
(

  id          SERIAL NOT NULL
    CONSTRAINT photo_pk
    PRIMARY KEY,
  file_path   VARCHAR2(255) DEFAULT 'bogus_path',
  listing_id   INTEGER
    CONSTRAINT photo_listing_id_fk
    REFERENCES listing
);

CREATE TABLE tag
(
  id    SERIAL NOT NULL
    CONSTRAINT tag_pk
    PRIMARY KEY,
  name  VARCHAR2(30)
);

create table listing_tag
(
  listing_id SERIAL NOT NULL
    CONSTRAINT listing_fk
    REFERENCES listing,
  tag_id     SERIAL NOT NULL
    CONSTRAINT tag_fk
    REFERENCES tag,
  CONSTRAINT listing_tag_pk
  PRIMARY KEY (listing_id, tag_id)
);


ALTER SEQUENCE account_id_seq RESTART WITH 100;
ALTER SEQUENCE listing_id_seq RESTART WITH 100;

CREATE TABLE message
(
  id         SERIAL                  NOT NULL
    CONSTRAINT message_pkey
    PRIMARY KEY,
  body       VARCHAR2(2048)           NOT NULL,
  recipient  INTEGER                 NOT NULL,
  author     INTEGER                 NOT NULL
    CONSTRAINT author___fk
    REFERENCES account,
  createdate TIMESTAMP DEFAULT now() NOT NULL,
  parent     INTEGER                 NOT NULL
    CONSTRAINT message_message_id_fk
    REFERENCES message
);

CREATE UNIQUE INDEX message_id_uindex
  ON message (id);

COMMENT ON COLUMN message.recipient IS 'account id of intended recipient';

COMMENT ON COLUMN message.author IS 'account id of author';

COMMENT ON COLUMN message.parent IS 'id of the parent message';
