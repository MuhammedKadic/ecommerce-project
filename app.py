from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://python:1234@localhost/ecommerce-01' #URI to connec to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    #removes annoying WARNING messages from console
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' #This secures the session and keeps it from being accessible

db = SQLAlchemy(app)


class OrderStatus(Enum):
    PENDING = 0  # Once order is paid for
    PROCESSING = 1  # Once we are getting ready to ship the order
    SHIPPED = 2  # This is once the order is successfully shipped
    DELIEVERED = 3  # order has been delievered to customers house
    CANCELED = 4  # if user requests to cancel their order or chargesback
    HOLD = 5  # If the user has paid for a product but it is on back order

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    assoID = db.Column(db.Integer, nullable=False)
    price = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    dateStarted = db.Column(db.DateTime, nullable=False)
    size = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)

    def __init__(self,item_id, assoID, price, quantity,size, dateStarted, name):
        self.item_id = item_id
        self.assoID = assoID
        self.price = price
        self.quantity = quantity
        self.size = size
        self.dateStarted = dateStarted
        self.name = name

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(40), nullable=False)
    dateCreated = db.Column(db.DateTime, nullable=False)
    orders = db.relationship('Orders', backref='user')

    def __init__(self, name, email, password, dateCreated, orders):  # This constructer is for easy access of the User class
        self.name = name
        self.email = email
        self.dateCreated = dateCreated
        self.password = password
        self.orders = orders


class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    transactionNumber = db.Column(db.String(255), nullable=False)
    trackingNumber = db.Column(db.String(90), nullable=False)
    products = db.Column(db.String(255), nullable=False)
    orderStatus = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    def __init__(self, id, trackingNumber, orderStatus,
                 user_id):  # This constructer is for easy access of the orders class
        self.id = id
        self.trackingNumber = trackingNumber
        self.orderStatus = orderStatus
        self.user_id = user_id


db.create_all()  # This creates all the classes references above
db.session.commit()  # This commit's all the changes

@app.route('/updateCart', methods=['POST'])
def updateCart():
    if "loggedIN" not in session:
        return redirect(url_for('login'))

    itemsFound = Cart.query.filter_by(assoID=session['userID'])
    if 'userID' in session:
        for items in itemsFound:
            if items.item_id == int(request.form.get('item_id')):
                if items.size != request.form.get('size'):
                    # Add's new item to cart because of the new size selection
                    db.session.add(
                        Cart(request.form.get('item_id'), session['userID'], "35.00", request.form.get('quantity'),
                             request.form.get('size'), datetime.datetime.today(), "PRODUCTEXAMPLE"))
                    db.session.commit()
                    return jsonify({'result': 'addedNewItem'})
                else:
                    # Updates the quantity if the size's are the same
                    items.quantity = request.form.get('quantity')
                    db.session.commit()
                    return jsonify({'result': 'updatedQuantity'})

        # This line below runs if the item is not in the cart essentially creating a brand new item in the cart
        db.session.add(Cart(request.form.get('item_id'), session['userID'], "35.00", request.form.get('quantity'), request.form.get('size'), datetime.datetime.today(), "PRODUCTEXAMPLE"))
        db.session.commit()
        return jsonify({'result': 'addedNewItem'})
    return jsonify({'result': 'failure'})

@app.route('/test')
def test():
    itemsFound = Cart.query.filter_by(assoID=session['userID'])
    item_data = []

    for item in itemsFound:
        current_item = {
            'id': item.id,
            'assoID': item.assoID,
            'price': item.price,
            'quantity': item.quantity,
            'dateStarted': item.dateStarted,
            'size': item.size,
            'name' : item.name
        }
        item_data.append(current_item)

    return render_template('test.html', items=item_data)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/shop')
def StoreCatalogFile():
    return render_template("store/shop.html")


@app.route('/shop/<id>')
def StoreTemplateFile(id):
    id = id
    return render_template("store/template-file.html", id=id)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if "loggedIN" in session and session['loggedIN'] == True:
        return redirect(url_for('index'))

    if request.method == "POST":
        users = User.query.filter_by(email=request.form.get("email")).first()

        if users:
            session['loggedIN'] = True
            print(session['loggedIN'])
            session['userID'] = users.id
            print(session['userID'])
            print('hit')
            return redirect(url_for('index'))


    return render_template("authentication/login.html")

@app.route('/checksomething')
def check():
    return str(session['loggedIN'])

@app.route('/logout')
def logout():
    session.pop('loggedIN')
    session.pop('userID')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if "loggedIN" in session == True:
        return redirect(url_for('index'))

    if request.method == "POST":
        db.session.add(User(request.form.get('username'), request.form.get('email'), request.form.get("password"), datetime.datetime.today(), []))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("authentication/register.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html")


if __name__ == '__main__':
    app.run(debug=True)
