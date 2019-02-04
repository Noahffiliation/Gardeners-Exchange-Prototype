-- Insert data into account table
INSERT INTO account (email, first_name, last_name, password, id, bio)
VALUES
  ('fred@ziffle.com', 'Fred', 'Ziffle', 'freddyZ', 1, DEFAULT),
  ('zelda@ziffle.com', 'Zelda', 'Ziffle', 'zeldaZ', 2, 'Hey! I''m Zelda Ziffle! I have a garden in my backyard and I get a lot more tomoatoes than I can use. My garden is non-gmo and we do not use any pesticides on our plants.'),
  ('santa@claus.com', 'Santa', 'Claus', 'hoHoHO', 3, DEFAULT),
  ('father@christmas.com', 'Father', 'Christmas', 'hopeful', 4, DEFAULT),
  ('chungly@cabs.com', 'Chungus', 'Chungleton', 'grambly', 5, DEFAULT),
  ('maggie@road.com', 'Maggie', 'Road', 'maggieR', 6, DEFAULT),
  ('barb@milton.com', 'Barb', 'Milton', 'barbM', 7, DEFAULT),
  ('tim@ramsey.com', 'Tim', 'Ramsey', 'timeR', 8, DEFAULT),
  ('grant@smith.com', 'Grant', 'Smith', 'grantS', 9, DEFAULT),
  ('jim@brandle.com', 'Jim', 'Brandle', 'jimB', 10, DEFAULT),
  ('randy@singer.com', 'Randy', 'Singer', 'randyS', 11, DEFAULT),
  ('payton@hunter.com', 'Payton', 'Hunter', 'paytonH', 12, DEFAULT),
  ('matt@collins.com', 'Matt', 'Collins', 'mattC', 13, DEFAULT),
  ('macey@rae.com', 'Macey', 'Rae', 'maceyR', 14, DEFAULT),
  ('ben@simpson.com', 'Ben', 'Simpson', 'benS', 15, DEFAULT),
  ('ripley@not.com', 'Ribley', 'Krampus', 'rigly96', 16, DEFAULT);


-- Insert data into listing table
INSERT INTO listing (name, quantity, price, unit, account_email, description, time_posted, file_path)
VALUES
  ('Oranges', 90, 26, 'pc', 'fred@ziffle.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0001.jpg'),
  ('Watermelon', 10, 50, 'pc', 'fred@ziffle.com', 'test data and other stuff is here for gnarly',  DEFAULT, '/static/photos/file0002.jpg'),
  ('Tomatoes', 85, 25, 'g', 'zelda@ziffle.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0003.jpg'),
  ('Mushrooms', 81, 49, 'pc', 'maggie@road.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0004.jpg'),
  ('Lettuce', 78, 85, 'pc', 'barb@milton.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0005.jpg'),
  ('Broccoli', 37, 15, 'kg', 'grant@smith.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0006.jpg'),
  ('Cucumbers', 25, 90, 'pc', 'ben@simpson.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0007.jpg'),
  ('Brussel Sprouts', 6, 3, 'kg', 'macey@rae.com', ' test data and other stuff is here for gnarly', DEFAULT, '/static/photos/file0008.jpg'),
  ('Apples', 10, 4, 'oz', 'zelda@ziffle.com', 'Testing old stuff', '1999-01-08 04:05:06', DEFAULT);


INSERT INTO account_favorites (account_email, favorites_email)
VALUES
  ('zelda@ziffle.com', 'fred@ziffle.com'),
  ('zelda@ziffle.com', 'jim@brandle.com'),
  ('fred@ziffle.com', 'zelda@ziffle.com'),
  ('fred@ziffle.com', 'jim@brandle.com'),
  ('father@christmas.com', 'santa@claus.com'),
  ('grant@smith.com', 'fred@ziffle.com');


-- Insert data into transaction table
/*INSERT INTO transaction (cost, time, listing_id, buyer_id, seller_id)
VALUES
  (3.14, '2018-03-23 09:32:15', 102, 5, 9),
  (5.00, '2018-02-19 23:19:11', 101, 16, 3);
*/
--Insert data into message table
INSERT INTO message (body, recipient, author, parent)
VALUES
  ('May I come pick up the oranges after hours?', '1','4','1'),
  ('Are these tomatoes organic?', '2', '3', '2'),
  ('What color watermelons do you offer?', '1', '11', '1'),
  ('How long do your tomatoes last?', '2', '11', '2'),
  ('Are the shapes of your mushrooms all consistent?', '6', '15', '6'),
  ('How many people does a head of lettuce feed?', '7', '11', '7'),
  ('What time of day would be best to come pick up the broccoli?', '9', '14', '9'),
  ('What is the max quantity of cucumbers I can purchase?', '15', '10', '15'),
  ('How would you suggest storing brussels sprouts?', '14', '2', '14'),
  ('What is the best type of apple for cooking?', '2', '11', '2'),
  ('May I come pick up the oranges after hours?', '1','6','1'),
  ('Are these tomatoes organic?', '2', '14', '2'),
  ('What color watermelons do you offer?', '1', '9', '1'),
  ('How long do your tomatoes last?', '2', '9', '2'),
  ('Are the shapes of your mushrooms all consistent?', '6', '1', '6'),
  ('How many people does a head of lettuce feed?', '7', '6', '7'),
  ('What time of day would be best to come pick up the broccoli?', '9', '1', '9'),
  ('What is the max quantity of cucumbers I can purchase?', '15', '2', '15'),
  ('How would you suggest storing brussels sprouts?', '14', '6', '14'),
  ('What is the best type of apple for cooking?', '2', '7', '2'),

--test conversation!!
  ('Hi (1)?', '2', '1', '2'),
  ('Hello! (2)', '1', '2', '2'),
  ('How have you been? (3)', '2', '1', '2'),
  ('I have been well (4)', '1', '2', '2'),
  ('That is nice! (5)', '2', '1', '2'),
  ('Thank''s for asking (6)', '1', '2', '2'),
  ('So how about those beans? (7)', '2', '1', '2'),
  ('The beans are fresh! what else can I say? (8)', '1', '2', '2'),
  ('Are the beans cheese flavored? (9)', '2', '1', '2'),
  ('No they are not!! You imbecile (10)', '1', '2', '2'),
  ('Don''t talk to me like that! I will never buy from you again! (11)', '2', '1', '2'),
  ('See if I care you hick!!!!!!! (12)', '1', '2', '2');



--INSERT INTO message (body, recipient, author, parent)
