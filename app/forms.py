from flask_wtf import Form
from wtforms import StringField, DateField, DecimalField, HiddenField, BooleanField, TextAreaField, validators
from wtforms.fields.html5 import TelField
from app.models import Customer, Order
import decimal

class Item():
	def __init__(self, quanity, article, price):
		self.quantity = quantity
		self.article = article
		self.price = price

class ItemForm(Form):
	item_choices = ['dress', 'suit - 2pc', 'suit - 3pc', 'trousers', 'shorts', 't-shirt', 'shirt', 'other'] # fill in
	item_choices = [(choice, choice) for choice in item_choices]
	quantity = IntegerField('Qt.', validators = [validators.DataRequired()])
	article = SelectField('Type', choices = item_choices, validators = [validators.DataRequired()])
	price = DecimalField('Price', validators = [validators.DataRequired()])

	def __str__(self):
		return ' -- '.join([str(self.quantity.data), self.article.data, str(self.price.data)])

class TransactionForm(Form):
	type_choices = ['discount', 'payment']
	type_choices = [(choice, choice) for choice in type_choices] # conform to _choices format

	amount = DecimalField('Amount', validators = [validators.DataRequired()])
	description = SelectField('Type', choices = type_choices, validators = [validators.DataRequired()])
	date = DateField('Date', validators = [validators.DataRequired()])
	error_field = HiddenField('errors')
	id = IntegerField(widget = HiddenInput(), validators = [validators.Optional()])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.transaction = None

	def add_transaction(self, order):
		self.transaction = Transaction(amount = self.amount.data, description = self.description.data, date = self.date.data, order_id = order.id)

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		if self.id.data:
			self.transaction = Transaction.query.filter_by(id = self.id.data).first()
			if self.transaction:
				transaction.amount = self.amount.data
				transaction.description = self.description.data
				transaction.date = self.date.data
			else:
				error_field.errors.append('Invalid Transaction ID. Delete Transaction.')
				return False
		return True

class OrderForm(Form):
	locations = ['cleaners', 'delivered', 'plant']
	locations = [(location, location) for location in locations]

	first_name = StringField('First Name', validators = [
		validators.DataRequired(),
		validators.Length(min = 1, max = 25)
	])
	last_name = StringField('Last Name', validators = [
		validators.DataRequired(),
		validators.Length(min = 1, max= 25)
	])
	phone = TelField('Phone', validators = [validators.DataRequired(), validators.Length(min = 10, max = 10)])
	order_num = IntegerField('Order Number', validators = [validators.DataRequired()])
	order_date = DateField('Order Date', validators = [validators.DataRequired()])
	est_pickup_date = DateField('Est Pickup Date', validators = [validators.DataRequired()])
	pickup_date = DateField('Pickup Date', validators = [validators.Optional()])
	location = SelectField('Location', choices = locations, validators = [validators.DataRequired()])
	items_field = FieldList(FormField(ItemForm), min_entries = 1)
	price = DecimalField('Price', validators = [validators.DataRequired()])
	transactions_field = FieldList(FormField(TransactionForm), min_entries = 0, validators = [validators.Optional()])
	paid = DecimalField('Amount Paid', default = 0, validators = [validators.Optional()])
	paid_all = BooleanField('Paid', default = False, validators = [validators.Optional()])
	comments = TextAreaField('Comments', render_kw={"rows": 70, "cols": 11}, validators = [validators.Optional()])
	error_field = HiddenField('errors')
	id = IntegerField(widget = HiddenInput(), validators = [validators.Optional()])

	def __init__(self, *args, **kwargs):
		if 'items_field' in kwargs:
			items = kwargs['items_field']
			items = items.split(', ')
			items = [OrderForm.populate_item(item) for item in items]
			kwargs['items_field'] = items
		Form.__init__(self, *args, **kwargs)
		self.customer = None
		self.order = None

		# set default dates
		if not self.order_date.data:
			today = datetime.date.today()
			self.order_date.data = today
			self.est_pickup_date.data = today + datetime.timedelta(days = 2)

	@staticmethod
	def populate_item(item_string):
		item_list = item_string.split(' -- ')
		quantity = int(item_list[0])
		article = item_list[1]
		price = decimal.Decimal(item_list[2])
		return Item(quantity, article, price)

	def stringify_items(self):
		item_string = ', '.join([str(entry) for entry in self.items_field.entries])
		return item_string

	def add_transactions(self):
		for transaction_field in self.transactions.entries:
			if not transaction_field.transaction:
				transaction_field.add_transaction(self.order)

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		# validate phone stuff
		if self.paid_all.data and self.paid.data < self.price.data:
			self.paid.data = self.price.data

		if self.id.data:
			self.order = Order.query.filter_by(id = self.id.data).first()
			if self.order:
				customer = self.order.customer
				customer.remove_order(self.order)
				self.order.location = self.location.data
				self.order.est_pickup_date = self.est_pickup_date.data
				self.order.pickup_date = self.pickup_date.data
				self.order.items = self.stringify_items()
				self.add_transactions()
				self.order.update_balance()
				self.order.comments = self.comments.data
				customer.add_order(self.order)

			return True

		customer = Customer.query.filter_by(first_name = self.first_name.data, last_name = self.last_name.data, phone = self.phone.data).first()
		if customer:
			self.customer = customer
		else:
			# add new customer to database
			self.customer = Customer(first_name = self.first_name.data, last_name = self.last_name.data, phone = self.phone.data, balance = 0)
		self.order = Order(order_num = self.order_num.data, order_date = self.order_date.data, est_pickup_date = self.est_pickup_date.data, pickup_date = self.pickup_date.data, location = self.location.data, items = self.stringify_items(), price = self.price.data, paid = self.paid.data, comments = self.comments.data, customer_id = self.customer.id)
		self.add_transactions()
		self.order.calculate_paid()
		self.customer.add_order(self.order)
		return True

class FindOrderForm(Form):
	order_num = IntegerField('Order Number', validators = [validators.Optional()])
	order_date = DateField('Order Date', validators = [validators.Optional()])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.orders = None
		self.customers = None
		self.customer_id = None

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		if self.order_num.data:
			self.orders = Order.query.filter_by(order_num = self.order_num.data).all()
		elif self.order_date.data:
			self.orders = Order.query.filter_by(order_date = self.order_date.data).all()
		else:
			return False
		
		return True

class FindCustomerForm(Form):
	last_name = StringField('Last Name', validators = [validators.Optional()])
	phone = TelField('Phone', validators = [validators.Optional(), validators.Length(min = 10, max = 10)])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.customers = None

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		if self.last_name.data:
			self.customers = Customer.query.filter_by(last_name = self.last_name.data).all()
		elif self.phone.data:
			self.customers = Customer.query.filter_by(phone = self.phone.data).all()
		else:
			return False
		
		return True

class CustomerForm(Form):
	comments = TextAreaField('Comment', render_kw={"rows": 70, "cols": 11})
	id = IntegerField(widget = HiddenInput(), validators = [validators.DataRequired()])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.customer = None

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		self.customer = Customer.query.filter_by(id = self.id.data).first()
		if self.customer:
			self.customer.comments = self.comments.data
		else:
			return False
		
		return True