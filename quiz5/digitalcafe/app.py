from flask import Flask,redirect
from flask import render_template
from flask import request
from flask import session
import database as db
import authentication
import logging
import pymongo
import ordermanagement as om

app = Flask(__name__)

# Set the secret key to some random bytes.
# Keep this really secret!
app.secret_key = b's@g@d@c0ff33!'

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', page="Privacy")

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('products.html', page="Products",product_list=product_list)

@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    return render_template('productdetails.html', code=code,product=product)

@app.route('/branches')
def branches():
    branch_list = db.get_branches()
    return render_template('branches.html', page="Branches",branch_list=branch_list)

@app.route('/branchdetails')
def branchdetails():
    code = request.args.get('code', '')
    print(code)
    branch = db.get_branch(int(code))
    print(branch)
    return render_template('branchdetails.html', code=code,branch=branch)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', page="About Us")


@app.route( '/login' , methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    
    is_successful, user = authentication.login(username, password)
    app.logger.info('%s', is_successful)
    if(is_successful):
        session["user"] = user
        return redirect('/')
    else:
        #return redirect('/tryagain')
        return  render_template('tryagain.html', page="Try Again")
    
@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')


@app.route('/addtocart', methods = ['POST', ])
def addtocart():
    code = request.form.get('code')
    quantity = int(request.form.get('quantity'))
    product = db.get_product(int(code))
    item=dict()
# A click to add a product translates to a quantity of 1 for now
    item["qty"] = quantity
    item["code"] = code
    item["name"] = product["name"]
    item["subtotal"] = product["price"]*item["qty"]
    
    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart
    return redirect('/cart')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/updatecart', methods = ['POST', ])
def updatecart():
    
    request_type = request.form.get('submit')
    code = request.form.get('code')
    product = db.get_product(int(code))
    cart = session["cart"]
    
    #Update quantity of item in cart
    if request_type == "Update":
        quantity = int(request.form.get("quantity"))
        cart[code]["qty"] = quantity
        cart [code]["subtotal"] = quantity * product["price"]
        
    elif request_type == 'Remove':
        del cart[code]
        
    session["cart"] = cart
    
    return redirect('/cart')

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')


@app.route('/orderhistory')
def orderhistory():
    user = session["user"]
    username = user["username"]
    
    arethereorders = om.check_user(username)
    
    if arethereorders == True:
        order_list = db.get_orders(username)
        return render_template('orderhistory.html', page="Orders", order_list=order_list)
    
    else:
        return render_template('orderempty.html')

    
@app.route('/changepassword')
def changepassword():
    return render_template('changepassword.html')

@app.route('/change', methods = ['GET', 'POST'])
def change():
    oldpass = request.form.get("old")
    newpass1 = request.form.get("new1")
    newpass2 = request.form.get("new2")
    user = session["user"]
    username = user["username"]
    userpass = user["password"]

    if oldpass == userpass and newpass1 == newpass2:
        change_now = db.change_db(username, newpass1)
        change_error = "Password successfully changed."
        return render_template('changepassword.html', change_error=change_error)
    
    elif oldpass != userpass:
        change_error = "The current password is incorrect."
        return render_template('changepassword.html', change_error=change_error)
    
    else:
        change_error = "The passwords entered do not match."
        return  render_template('changepassword.html', change_error=change_error)