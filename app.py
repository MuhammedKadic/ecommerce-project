from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import datetime
import stripe

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://python@localhost/ecommerce'  # URI to connec to database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # removes annoying WARNING messages from console
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # This secures the session and keeps it from being accessible

db = SQLAlchemy(app)

stripe.api_key = 'sk_test_cirOEcSBSK4OB5ZGFITjiFPR004IvlkSUG'


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

    def __init__(self, item_id, assoID, price, quantity, size, dateStarted, name):
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
    rank = db.Column(db.Integer, nullable=False)
    orders = db.relationship('Orders', backref='user')

    def __init__(self, name, email, rank, password, dateCreated,
                 orders):  # This constructer is for easy access of the User class
        self.name = name
        self.email = email
        self.rank = rank
        self.dateCreated = dateCreated
        self.password = password
        self.orders = orders


class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    itemID = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(90), nullable=False)
    price = db.Column(db.String(90), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(55), nullable=False)
    isActive = db.Column(db.Boolean, nullable=False)
    productImage = db.Column(db.String(55), nullable=False)
    percentDiscount = db.Column(db.String(50), nullable=False)

    def __init__(self, id, name, price, description, category, isactive, productimage,
                 percentdiscount):  # This constructer is for easy access of the orders class
        self.itemID = id
        self.name = name
        self.price = price
        self.description = description
        self.category = category
        self.isActive = isactive
        self.productImage = productimage
        self.percentDiscount = percentdiscount


class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    transactionNumber = db.Column(db.String(255), nullable=False)
    trackingNumber = db.Column(db.String(90), nullable=False)
    products = db.Column(db.String(255), nullable=False)
    orderStatus = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    def __init__(self, trackingNumber, orderStatus,
                 user_id):  # This constructer is for easy access of the orders class
        self.trackingNumber = trackingNumber
        self.orderStatus = orderStatus
        self.user_id = user_id


db.create_all()  # This creates all the classes references above
db.session.commit()  # This commit's all the changes


# noinspection PyInterpreter
@app.route('/updateCart', methods=['POST'])
def updateCart():
    if "loggedIN" not in session:
        return redirect(url_for('login'))

    sizeFound = Cart.query.filter_by(size=request.form.get('size'))
    itemFound = Cart.query.filter_by(item_id=request.form.get('item_id'))
    # noinspection PyInterpreter
    print(request.form.get('size'))
    if 'userID' in session:
        for items in sizeFound:
            print('part1')
            if items.item_id == int(request.form.get('item_id')):
                product = Products.query.filter_by(itemID=items.item_id).first()
                price = float(product.price) * int(request.form.get('quantity'))
                fixed_price = round(price, 2)
                items.price = fixed_price
                items.quantity = request.form.get('quantity')
                db.session.commit()
                return jsonify({'result': 'updatedQuantity'})
            else:
                continue

    if 'userID' in session:
        print('hit')
        for items in itemFound:
            if items.item_id == int(request.form.get('item_id')):
                product = Products.query.filter_by(itemID=items.item_id).first()
                if items.size != request.form.get('size'):
                    # Add's new item to cart because of the new size selection
                    price = float(product.price) * int(request.form.get('quantity'))
                    fixed_price = round(price, 2)
                    db.session.add(
                        Cart(request.form.get('item_id'), session['userID'], fixed_price, request.form.get('quantity'),
                             request.form.get('size'), datetime.datetime.today(), product.name))
                    db.session.commit()
                    return jsonify({'result': 'addedNewItem'})
            else:
                product = Products.query.filter_by(itemID=request.form.get('item_id')).first()
                price = float(product.price) * int(request.form.get('quantity'))
                fixed_price = round(price, 2)
                ## This line below runs if the item is not in the cart essentially creating a brand new item in the cart
                db.session.add(
                    Cart(request.form.get('item_id'), session['userID'], fixed_price, request.form.get('quantity'),
                         request.form.get('size'), datetime.datetime.today(), product.name))
                db.session.commit()
                return jsonify({'result': 'addedNewItem'})

        print('new')
        product = Products.query.filter_by(itemID=request.form.get('item_id')).first()
        price = float(product.price) * int(request.form.get('quantity'))
        fixed_price = round(price, 2)
        ## This line below runs if the item is not in the cart essentially creating a brand new item in the cart
        db.session.add(Cart(request.form.get('item_id'), session['userID'], fixed_price, request.form.get('quantity'),
                            request.form.get('size'), datetime.datetime.today(), product.name))
        db.session.commit()
        return jsonify({'result': 'addedNewItem'})
    return jsonify({'result': 'failure'})


@app.route('/removeFromCart', methods=['POST'])
def removeFromCart():
    itemsFound = Cart.query.filter_by(assoID=request.form.get('session'))


    for item in itemsFound:
        if item.item_id == int(request.form.get('item_id')):
            if item.size == request.form.get('size'):
                db.session.delete(item)
                db.session.commit()

    for price in itemsFound:
        TotalCaluclatedPrice += float(price.price)
    SubTotal = round(TotalCaluclatedPrice, 2)
    TotalCaluclatedPrice = (TotalCaluclatedPrice * TotalCaluclatedTaxRate) + TotalCaluclatedPrice
    TotalCaluclatedPrice = round(TotalCaluclatedPrice, 2)
    TotalTaxCaluclated = round((TotalCaluclatedPrice * TotalCaluclatedTaxRate), 2)
    return jsonify({'result': 'success','newPrice': AdjustedPrice, 'CaluclatedPrice': TotalCaluclatedPrice,
                                'TotalTaxCaluclated': TotalTaxCaluclated, 'Subtotal': SubTotal})


@app.route('/quantityUpdateToCart', methods=['POST'])
def updateQuantity():
    itemsFound = Cart.query.filter_by(assoID=request.form.get('session'))
    TotalCaluclatedPrice = 0
    TotalCaluclatedTaxRate = .10

    for item in itemsFound:
        if int(request.form.get('item_id')) == item.item_id:
            if item.size == request.form.get('size'):
                product = Products.query.filter_by(itemID=request.form.get('item_id')).first()
                item.quantity = request.form.get('quantity')
                price = float(product.price) * float(item.quantity)
                AdjustedPrice = round(price, 2)
                item.price = AdjustedPrice
                db.session.commit()
                for price in itemsFound:
                    TotalCaluclatedPrice += float(price.price)
                SubTotal = round(TotalCaluclatedPrice, 2)
                TotalCaluclatedPrice = (TotalCaluclatedPrice * TotalCaluclatedTaxRate) + TotalCaluclatedPrice
                TotalCaluclatedPrice = round(TotalCaluclatedPrice, 2)
                TotalTaxCaluclated = round((TotalCaluclatedPrice * TotalCaluclatedTaxRate), 2)
                return jsonify({'result': 'success', 'newPrice': AdjustedPrice, 'CaluclatedPrice': TotalCaluclatedPrice,
                                'TotalTaxCaluclated': TotalTaxCaluclated, 'Subtotal': SubTotal})
    return jsonify({'result': 'success'})


@app.route('/checkout')
def checkout():
    itemsFound = Cart.query.filter_by(assoID=session['userID'])
    item_data = []
    TotalCaluclatedPrice = 0
    TotalCaluclatedTaxRate = .10
    for item in itemsFound:
        TotalCaluclatedPrice += float(item.price)

        current_item = {
            'id': item.item_id,
            'assoID': item.assoID,
            'price': item.price,
            'quantity': item.quantity,
            'dateStarted': item.dateStarted,
            'size': item.size,
            'name': item.name,
        }
        item_data.append(current_item)

    SubTotal = round(TotalCaluclatedPrice, 2)
    TotalCaluclatedPrice = (TotalCaluclatedPrice * TotalCaluclatedTaxRate) + TotalCaluclatedPrice
    Tax = (TotalCaluclatedPrice * TotalCaluclatedTaxRate)
    Tax = round(Tax, 2)

    return render_template('store/checkout.html', items=item_data, CaluclatedPrice=round(TotalCaluclatedPrice, 2),
                           Tax=Tax, SubTotal=SubTotal)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/shop')
def StoreCatalogFile():
    itemsFound = Products.query.all()
    item_data = []

    for item in itemsFound:
        current_item = {
            'id': item.itemID,
            'name': item.name,
            'price': item.price,
            'description': item.description,
            'category': item.category,
            'isactive': item.isActive,
            'productimage': item.productImage,
            'percentdiscount': item.percentDiscount

        }
        item_data.append(current_item)
    return render_template("store/shop.html", items=item_data)


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
            session['userID'] = users.id
            session['rank'] = users.rank
            return redirect(url_for('index'))

    return render_template("authentication/login.html")


@app.route('/checksomething')
def check():
    return str(session['loggedIN'])


@app.route('/logout')
def logout():
    session.pop('loggedIN')
    session.pop('userID')
    session.pop('rank')
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if "loggedIN" in session == True:
        return redirect(url_for('index'))

    if request.method == "POST":
        db.session.add(User(request.form.get('username'), request.form.get('email'), 0, request.form.get("password"),
                            datetime.datetime.today(), []))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("authentication/register.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html")


if __name__ == '__main__':
    app.run(debug=True)
