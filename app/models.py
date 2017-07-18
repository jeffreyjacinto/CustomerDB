from app import db
import decimal

class Customer(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	first_name = db.Column(db.String(25), nullable = True)
	last_name = db.Column(db.String(25), nullable = False)
	phone = db.Column(db.String(10), nullable = False)
	comments = db.Column(db.String(250), nullable = True)
	orders = db.relationship('Order', backref = 'customer', lazy = dynamic)
	balance = db.Column(db.Numeric)

	def get_id(self):
		return str(self.id)

	def update_balance(self, amount):
		self.balance += amount

	def add_order(self, order):
		self.balance += order.balance

	def remove_order(self, order):
		self.balance -= order.balance

	def __str__(self):
		return '<Customer %s %s>' % (self.first_name, self.last_name)

	@property
	def serialize(self):
		return {
			'first_name': self.first_name,
			'last_name': self.last_name,
			'phone': self.phone,
			'id': self.id
		}

class Order(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	order_num = db.Column(db.Integer, nullable = False)
	order_date = db.Column(db.Date, nullable = False)
	est_pickup_date = db.Column(db.Date, nullable = False)
	pickup_date = db.Column(db.Date, nullable = True)
	location = db.Column(db.String(10), nullable = False)
	items = db.Column(db.String(250), nullable = False)
	price = db.Column(db.Numeric, nullable = False)
	paid = db.Column(db.Numeric, nullable = False)
	comments = db.Column(db.String(250), nullable = True)
	transactions = db.relationship('Order', backref = 'order', lazy = dynamic)
	customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

	def __str__(self):
		return '<Order %s %i>' % (str(self.order_date), self.order_num) # check

	@property
	def balance(self):
		return self.paid - self.price

	def calculate_price(self):
		items_list = self.items.split(', ')
		price_list = list(map((lambda item: decimal.Decimal(item.split(' -- ')[-1])), items_list))
		self.price = sum(price_list)
		self.price -= sum([transaction.amount for transaction in self.transactions.filter_by(description == 'discount').all()])

	def calculate_paid(self):
		self.paid = sum([transaction.amount for transaction in self.transactions.filter_by(description == 'payment').all()])

	def update_balance(self):
		self.calculate_price()
		self.calculate_paid()

	@property
	def is_active(self):
		return self.location != "delivered"

	@property
	def serialize(self):
		return {
			'order_num': self.order_num
			'order_date': self.order_date,
			'location': self.location,
			'items': self.items,
			'est_pickup_date': self.est_pickup_date,
			'pickup_date': self.pickup_date,
			'transactions': [trans.serialize() for trans in self.transactions.all()],
			'price': self.price,
			'paid': self.paid,
			'comments': self.comments,
			'customer_id': self.customer_id,
			'id': self.id
		}

class Transaction(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	amount = db.Column(db.Numeric)
	date = db.Column(db.Date)
	description = db.Column(db.String(10))
	order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

	def __str__(self):
		return '<Transaction %s %s %i>' % (self.order_date, self.description, self.amount)

	@property
	def is_active(self):
		return self.location != "delivered"

	@property
	def serialize(self):
		return {
			'amount': self.amount
			'date': self.date,
			'description': self.description,
			'order_id': self.customer_id,
			'id': self.id
		}