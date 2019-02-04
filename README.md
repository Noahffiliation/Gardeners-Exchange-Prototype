# Gardener's Exchange Project

Information Systems Design - S2018

We are developing a "Gardener's Exchange" application that will connect local farmers and gardeners to buy, sell and trade goods.

# About Gardener's Exchange
We exist to provide a food sharing service to connect and build up our local community. Through our platform, we make trading and sharing our own healthy and organicly grown foods accessible to our towns. Join our community and make your mark on Grant County.

This application was developed as part of the Information Systems Design class at Taylor University in the Spring of 2018. It was intended to provide experience in an agile development environment. We worked in a team of 5, passing the roles of project manager and product manager around for each of 4 two-week sprints.


## Configuration Instructions

Setup Database Configuration
1. Create a file named "db_config.py". _DO NOT COMMIT THIS FILE_ 
2. On one line write: data_source_name = 'YOUR DATABASE CONFIG STUFF HERE'
   Example: data_source_name = 'host=faraday.cse.taylor.edu dbname=dunky user=brungus password=batmen'
3. Once the db_config.py file is created, connect as PostgreSQL database and run the create_db.sql file.
4. If you want to have sample data in your database you can run the init_db.sql file to generate some sample data.