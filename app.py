import os
from helpers import apology, login_required, lookup, usd
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
app.secret_key = 'A0AKR5TGD\ R~XHH!jmN]LWX/,?RT'
# app.config['SECRET_KEY'] = os.urandom(24)
# this is important or wont work
app.config['SESSION_COOKIE_NAME'] = "my_session"
# Configure Database
db = SQL(os.getenv("DATABASE_URL"))
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """index page of site"""
    # Get user stock data from Database
    user_stock_dict = db.execute("SELECT * FROM stocks WHERE user_id = ?", session["user_id"])
    
    # Get user current cash balance
    user_balance = ((db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"]))[0]['cash'])
    
    # Store stock info  share, current_price
    stock_data = dict()
    
    # Store stock_data for each symbol 
    stock_dict = dict()

    # Store total amount of stock purchased
    total_current_cost = 0
    
    for stock in user_stock_dict:
        # Check if symbol exist in stock_dict
        if stock['stock_symbol'] not in stock_dict:
            # Store stock name in stock_data
            stock_data['name'] = stock['stock_name']
            # Store stock price in stock_data
            stock_data['price'] = float((lookup(stock['stock_symbol']))['price'])
            # Store user stock shares in stock_data
            stock_data['shares'] = stock['number_shares']
            # Copy the above stock_data dict into stock_dict to avoid over write
            stock_dict[stock['stock_symbol']] = stock_data.copy()
            # Increase total amount of stock purchased
            total_current_cost += float((lookup(stock['stock_symbol']))['price']) * stock['number_shares']
        # If symbol exist in stock_dict 
        else:
            # Increase number of shares
            stock_dict[stock['stock_symbol']]['shares'] += stock['number_shares']
            
            # Increase total amount of stock purchased
            total_current_cost += float((lookup(stock['stock_symbol']))['price']) * stock['number_shares']
        """
        if stock['stock_symbol'] not in stock_dict:
            stock_dict[stock['stock_symbol']]['price'] =  float((lookup(stock['stock_symbol']))['price'])
            total_current_cost += float((lookup(stock['stock_symbol']))['price'])
        else:
            stock_dict[stock['stock_symbol']]['price']
            print("exist")
        """
    return render_template("index.html", balance=float(user_balance), total_cost=usd(total_current_cost), stocks=stock_dict)

    
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    error_type = None
    error_dir = "buy.html"
    try:
        if request.method == "POST":
            # Get purchase time/date:
            purchase_d_t = request.form.get("local_time")
            if not purchase_d_t:
                purchase_d_t = "01/01/1990"
                
            # Get num of share user made
            user_share = request.form.get("shares")
            
            # Get quote name user made
            user_symbol = request.form.get("symbol")
            
            # Verify user entered a quote
            if not user_symbol:
                error_type = "invalid symbol"; raise exception;
                
            # Verify user entered a valid quote
            elif not lookup(user_symbol):
                error_type = "invalid symbol"; raise exception;
                
                
            # Verify user did not enter a non-integer share
            elif not user_share.isdigit():
                error_type = "cannot purchase partial/negative shares ;)"; raise exception;
            
             # Verify user entered a valid share
            elif not user_share and int(user_share) <= 0:
    
                # elif not user_share or not int(user_share) or int(user_share)<=0 or float(user_share):
                error_type = "invalid share"; raise exception;
                     
            # Get the market info("name, price, symbol)" for user quote
            quote_dict = lookup(user_symbol)
            
            # Captalize user_symbol 
            user_symbol = user_symbol.upper()
            
            # Get user cash balance
            user_current_balance = ((db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"]))[0]['cash'])
            user_balance_after = user_current_balance - (quote_dict['price'] * int(user_share))
            
            # Verify user entered a symbol
            if not user_share:
                error_type = "missing shares"; raise exception;
                
            # Verify user have enough money
            elif user_balance_after < 0:
                error_type = "YOU CAN'T AFFORD IT :("; raise exception;
                
            # Deduct cash from user balance
            db.execute("UPDATE users SET cash = ? WHERE id = ?", user_balance_after,  session["user_id"])
            """
            # Check if user already have same stock
            if len(db.execute("SELECT stock_name FROM stocks WHERE user_id = ? AND stock_symbol = ?", session["user_id"], user_symbol)) != 0:
                # Update num of user shares of the quote
                db.execute("UPDATE stocks SET number_shares = number_shares + ? WHERE user_id = ? AND stock_symbol = ?" , user_share, session["user_id"], user_symbol)
            """
    
            db.execute("INSERT INTO stocks (stock_symbol, stock_name , purchase_price, number_shares, user_id, purchase_time) VALUES(?, ?, ?, ?, ?, ?)", 
                       user_symbol, quote_dict['name'],  usd(quote_dict['price']), user_share, session["user_id"], purchase_d_t)
            return redirect("/")
        else:
            return render_template("buy.html")
    except:
        flash(error_type)
        return render_template(error_dir)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    error_type = None
    error_dir = "history.html"
    # Get user stock data from Database
    user_stock_dict = db.execute("SELECT * FROM stocks WHERE user_id = ? ORDER BY order_id DESC", session["user_id"])
    '''
    # Store stock info  share, current_price
    stock_data = dict()
    
    # Store stock_data for each symbol 
    stock_dict = dict()
    '''
    return render_template("history.html", user_data=user_stock_dict)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    error_type = None
    error_dir = "login.html"
    # Forget any user_id
    session.clear()
    try:
            
        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":
    
            # Ensure username was submitted
            if not request.form.get("username"):
                error_type = "must provide username"; raise exception;
    
            # Ensure password was submitted
            elif not request.form.get("password"):
                error_type = "must provide password"; raise exception;
    
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
    
            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                error_type = "invalid username and/or password"; raise exception;
    
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
    
            # Redirect user to home page
            return redirect("/")
    
        # User reached route via GET (as by clicking a link or via redirect)
        else:
            return render_template("login.html")
    except:
        flash(error_type)
        return render_template(error_dir)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    error_type = None
    error_dir = "quote.html"
    try:
            
        if request.method == "POST":
            
            # Get user quote input
            quote_symbol = request.form.get("symbol")
            
            # Match user quote to lookup and get quote data
            dict_quote = lookup(quote_symbol)
            
            # Store name, price, symbol of the quote, if exist
            if dict_quote:
                return render_template("quoted.html", quoted=dict_quote)
            else:
                error_type = "invalid symbol"; raise exception;
            
            return render_template("quoted.html")
        
        else:
            return render_template("quote.html")
    except:
        flash(error_type)
        return render_template(error_dir)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user""" 
    error_type = None
    error_dir = "register.html"
    try:
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            password_confirm = request.form.get('confirmation')
            # Check for valid username
            if not username or not isinstance(username, str):
                error_type = "Please enter a valid user name"; raise Exception;
            # Check for password errors
            elif not password:
                 error_type = "Please enter a valid password"; raise Exception;
            elif password != password_confirm:
                 error_type = "PASSWORDS DON'T MATCH"; raise Exception;
             # Check for matching username in database
            elif db.execute("SELECT * FROM users WHERE username = ?", username):
                 error_type = "USERNAME TAKEN!"; raise Exception;
            # Add user to Database
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))
            return redirect("/")
        else:
            return render_template('register.html')
    except Exception:
        flash(error_type)
        return render_template(error_dir)
        
        
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Allow user to sell stocks"""
    error_type = None
    error_dir = "sell.html"
    try:
        if request.method == "POST":
            
            # Get num of share user chose
            user_share = request.form.get("shares")
            # Get stock’s symbol name user chose
            user_symbol = request.form.get("symbol")
            
            # Verify user did not enter a non-integer share
            if not user_share.isdigit():
                error_type = "cannot sell partial/negative shares ;)"; raise exception;
                
             # Verify user entered a valid share
            elif not user_share and int(user_share) <= 0:
                error_type = "invalid share"; raise exception;
                
            # Verify user entered a  quote
            elif not user_symbol:
                error_type = "invalid symbol"; raise exception;
                
            # Verify user entered a valid quote
            elif not lookup(user_symbol):
                error_type = "invalid symbol"; raise exception;
                    
            # Verify num of user_share
            elif not user_share:
                error_type = "missing shares"; raise exception;
                
            # Get the market info("name, price, symbol)" for user quote
            quote_dict = lookup(user_symbol)
            
            # Total num.user_shares * current stock cost:
            total_share_cost = quote_dict['price'] * int(user_share)
            
            # Get user cash balance
            user_current_balance = ((db.execute("SELECT cash FROM users WHERE id = ?", 
                                     session["user_id"]))[0]['cash'])
            
            # Get user balance after selling
            user_balance_after_selling = user_current_balance + total_share_cost
            
            # Store number of total stock share user own 
            total_user_share_num = 0
            
            # Captalize user_symbol 
            user_symbol = user_symbol.upper()
    
            # Get user number of share of the symbol
            user_share_num = (db.execute("SELECT number_shares FROM stocks WHERE user_id = ? AND stock_symbol = ? ",
                              session["user_id"], user_symbol))
            
            # Verify user own a valid/enough share
            if not user_share_num:
                error_type = "you don't own any share here"; raise exception;
            # If user have more of the same stock -> get total
            elif len(user_share_num) >= 1:
                for share in user_share_num:
                    total_user_share_num += share['number_shares']
                    
            # Assign single stock share to total
            elif not (len(user_share_num) >= 1):
                
                # Assign single stock share to total
                total_user_share_num = user_share_num[0]['number_shares']
                    
            # Check if user have enough num of shares
            if total_user_share_num - int(user_share) < 0:
                error_type = "too many shares"; raise exception;
                
            # Remaining number of share after selling
            remaining_share = total_user_share_num - int(user_share)
    
            # Add balance to user
            db.execute("UPDATE users SET cash = ? WHERE id = ?", user_balance_after_selling, session["user_id"])
            
            # Reduce user number of shares 
            db.execute("UPDATE stocks SET number_shares = ? WHERE user_id = ? AND stock_symbol = ?",
                       remaining_share, session["user_id"], user_symbol)
            
            # Drop user stock from stock database, if zero amount of stock share left
            if remaining_share == 0:
                db.execute("DELETE FROM stocks WHERE user_id = ? AND stock_symbol = ? ", session["user_id"], user_symbol)
                
            return redirect("/")
            
        else:
                    
            # Get user purchased stocks
            user_stocks = (db.execute("SELECT DISTINCT stock_symbol  FROM stocks WHERE user_id = ? ", session["user_id"]))
            
            return render_template("sell.html", stocks=user_stocks)
    except:
        flash(error_type)
        return render_template(error_dir)


def errorhandler(error):
    """Handle error"""
    if not isinstance(error, HTTPException):
        error = InternalServerError()
        error = str(error.name) + str(error.code)
    if error:
        code = str(error.code)
        error = 'Error: ' + code + ' Reported, Please Try again'
        # TO-DO: Create an Error table in database to keep track of user errors
        if code == "500":
            session.clear()
        flash(error)
        return render_template('index.html')
        
        
# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
