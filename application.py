import os
from pathlib import PurePath

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, SelectField, FloatField, PasswordField, ValidationError, TextAreaField, IntegerField
from wtforms.validators import Email, Length, DataRequired, NumberRange, InputRequired, EqualTo, Optional
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, AnonymousUserMixin

import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Bagel Boiz Bun Roasting Bonanza'


@app.before_request
def before_request():
    db.open_db_connection()


@app.teardown_request
def teardown_request(exception):
    db.close_db_connection()


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.email = 'Guest'


# Init Login Manager
login_mgr = LoginManager(app)
login_mgr.anonymous_user = Anonymous


def authenticate(email, password):
    for account in db.all_accounts():
        if email == account[1] and password == account[4]:
            return email
    return None


class Account(object):
    def __init__(self, email):
        self.email = email
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return self.email

    def __repr__(self):
        return "<User '{}' {} {} {}>".format(self.email, self.is_authenticated, self.is_active, self.is_anonymous)


@login_mgr.user_loader
def load_account(id):
    return Account(id)


@login_mgr.unauthorized_handler
def unauthorized():
    flash("You must be logged in to proceed")
    return redirect(url_for('login'))


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if authenticate(form.email.data, form.password.data):
            account = Account(form.email.data)
            login_user(account)
            flash('Logged in successfully as {}'.format(form.email.data))
            return redirect(url_for('index'))
        else:
            flash('Invalid email address or password')
    return render_template('login.html', form=form, hacker_news=db.all_accounts())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('index'))


# Routes site to Main index page
@app.route('/')
def index():
    return redirect(url_for('render_feed'))


# Routes to a testing page
@app.route('/testing')
def testing():
    return render_template('testing.html')


@app.route('/all_accounts')
def all_accounts():
    # print(db.all_accounts())
    return render_template('all-accounts.html', accounts=db.all_accounts())


@app.route('/about')
def about():
    # print(db.all_accounts())
    return render_template('about.html', accounts=db.all_accounts())


@app.route('/find_account/<email>')
def find_account(email):
    account = db.find_account(email)

    if account is None:
        flash('404 Account not found')
        return redirect(url_for('render_feed'))
    else:
        listings = db.listings_by_account(email)
        return render_template('account.html', account=account, listings=listings)


class AccountForm(FlaskForm):
    if current_user is not None:
        passwordValidator = [Optional()]
    else:
        passwordValidator = [Length(min=6), EqualTo('confirm', message='Passwords must match')]

    email = StringField("Email", validators=[Email()])
    first_name = StringField('First Name', validators=[Length(min=1, max=40), InputRequired()])
    last_name = StringField('Last Name', validators=[Length(min=1, max=40), InputRequired()])
    bio = TextAreaField('Bio', validators=[Length(max=2000)])

    password = PasswordField('Password',
                             validators=passwordValidator)
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Submit')


class ListingForm(FlaskForm):
    name = StringField('Listing Name', validators=[Length(min=1, max=40)])
    quantity = FloatField('Quantity', validators=[NumberRange(min=1, max=2000)])
    description = StringField('Listing Description', validators=[Length(min=1, max=500)])
    photo = FileField('Photo', validators=[])
    price = FloatField('Price/unit', validators=[NumberRange(min=0.0, max=5000)])
    unit = SelectField('Unit', choices=[('lb', 'pound'), ('pc', 'piece'), ('oz', 'ounce'),
                                        ('kg', 'kilogram'), ('g', 'gram'), ('other', 'other')])
    submit = SubmitField('Save Listing')


class BuyForm(FlaskForm):
    id = IntegerField('id', validators=[NumberRange(min=0, max=99999)])
    amount = FloatField('Amount', validators=[NumberRange(min=0, max=2000)])
    buy = SubmitField('Buy!')


@app.route('/all_accounts/create', methods=['GET', 'POST'])
def create_account():
    account_form = AccountForm()

    if account_form.validate_on_submit():
        account = db.find_account(account_form.email.data)

        if account is not None:
            flash("Account {} already exists".format(account_form.email.data))
        else:
            rowcount = db.create_account(account_form.email.data,
                                         account_form.first_name.data,
                                         account_form.last_name.data,
                                         account_form.password.data)

            if rowcount == 1:
                flash("Account {} created".format(account_form.email.data))
                account = Account(account_form.email.data)
                login_user(account)
                return redirect(url_for('render_feed'))
            else:
                flash("New member not created")
    return render_template('account-form.html', form=account_form, mode='create')


@app.route('/all_accounts/update/<email>', methods=['GET', 'POST'])
@login_required
def update_account(email):
    row = db.find_account(email)

    if row is None:
        flash("Member {} doesn't exist".format(email))
        return redirect(url_for('all_accounts'))

    account_form = AccountForm(email=row['email'],
                               first_name=row['first_name'],
                               last_name=row['last_name'],
                               bio=row['bio'])

    if account_form.validate_on_submit():
        rowcount = db.update_account(email,
                                     account_form.first_name.data,
                                     account_form.last_name.data,
                                     account_form.bio.data,
                                     account_form.password.data)

        if rowcount == 1:
            flash("Account {} updated".format(email))
            return redirect(url_for('find_account', email=email))
        else:
            flash('Account not updated')
    return render_template('account-form.html', form=account_form, mode='update')


@app.route('/all_listings/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    listing_form = ListingForm()

    if listing_form.submit():
        print(listing_form.photo.data)

    if listing_form.validate_on_submit():
        if current_user is not None:
            listing_id = db.create_listing(listing_form.name.data,
                                           listing_form.quantity.data,
                                           listing_form.description.data,
                                           listing_form.price.data,
                                           current_user.email,
                                           listing_form.unit.data)

            if listing_id is not 0:
                if listing_form.photo.data is not None:
                    uploaded_photo = listing_form.photo.data

                    file_name = "file{:04d}".format(int(listing_id))
                    print("FILE NAME", file_name)

                    extension = PurePath(uploaded_photo.filename).suffix
                    file_name += extension
                    print("FILE+EXT", file_name)

                    file_path = 'photos/' + file_name
                    print("FILE PATH", file_path)

                    save_path = os.path.join(app.static_folder, file_path)
                    print("SAVE PATH", save_path)
                    uploaded_photo.save(save_path)
                    db.add_listing_photo_path(listing_id, '/static/' + file_path)

                flash("Listing {} created".format(listing_form.name.data))
                return redirect(url_for('find_account', email=current_user.email))
            else:
                flash("Listing {} was not created".format(listing_form.name.data))
        else:
            flash("Email {} does not exist".format(listing_form.account.data))

    return render_template('listing_form.html', form=listing_form, mode='create')


@app.route('/all_listings/update/<id>', methods=['GET', 'POST'])
@login_required
def update_listing(id):
    row = db.find_listing(id)

    if row is None:
        flash("Listing {} doesn't exist".format(id))
        return redirect(url_for('all_listings'))

    listing_form = ListingForm(name=row['name'],
                               quantity=row['quantity'],
                               description=row['description'],
                               price=row['price'],
                               unit=row['unit'])

    if listing_form.validate_on_submit():
        rowcount = db.update_listing(id,
                                     listing_form.name.data,
                                     listing_form.quantity.data,
                                     listing_form.description.data,
                                     listing_form.price.data,
                                     listing_form.unit.data)
        if listing_form.photo.data is not None:
            uploaded_photo = listing_form.photo.data

            file_name = "file{:04d}".format(int(id))
            print("FILE NAME", file_name)

            extension = PurePath(uploaded_photo.filename).suffix
            file_name += extension
            print("FILE+EXT", file_name)

            file_path = 'photos/' + file_name
            print("FILE PATH", file_path)

            save_path = os.path.join(app.static_folder, file_path)
            print("SAVE PATH", save_path)
            uploaded_photo.save(save_path)
            db.add_listing_photo_path(id, '/static/' + file_path)

        if rowcount == 1:
            flash("Listing {} updated".format(listing_form.name.data))
            return redirect(url_for('find_account', email=db.get_email_from_listing(id)))
        else:
            flash("Listing not updated")
    return render_template('listing_form.html', form=listing_form)


@app.route('/feed/buy/<listing_id>/<amount>', methods=['POST'])
@login_required
def buy_listing(listing_id, amount):
    if amount <= db.find_listing(listing_id)['quantity']:
        rowcount = db.buy_listing(listing_id, amount)
        flash("You bought {} {} of {}".format('amount', db.find_listing(listing_id)['unit'], db.find_listing(listing_id)['name']))
    else:
        flash('Invalid amount')
    return render_template(url_for('render_feed'))


# Render 'feed' as homepage
@app.route('/feed')
def render_feed():
    buy_form = BuyForm()
    if buy_form.validate_on_submit():
        print("IM TRYING")
        return render_template(url_for('buy_listing', listing_id=buy_form.id.data, amount=buy_form.amount.data))
    db.check_expire_all()
    num_items = 100
    if current_user:
        return render_template('feed.html', feedItems=db.fetch_feed(num_items, current_user.email), form=buy_form)
    else:
        return render_template('feed.html', feedItems=db.fetch_feed(num_items), form=buy_form)


# View Message
@app.route('/view_message')
def render_message():

    messages = db.fetch_messages(me, you)
    return render_template('view_message.html', messages=messages)


@app.route('/mark_favorite', methods=['POST'])
def mark_favorite():
    db.mark_favorite(current_user.email, request.form["favorite_email"])
    return "OK"


@app.route('/favorites/<email>')
@login_required
def favorites(email):
    account = db.find_account(email)

    if account is None:
        flash('404 Account not found')
        return redirect(url_for('render_feed'))
    return render_template('favorites.html', account=account, favorites=db.list_favorites(email))


# Make this the last line in the file!
if __name__ == '__main__':
    app.run(debug=True)
