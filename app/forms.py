from flask_wtf import Form
from wtforms import StringField, DateField, DecimalField, HiddenField, BooleanField, TextAreaField, IntegerField, SelectField, FieldList, FormField, validators
from wtforms.widgets import HiddenInput, html_params, HTMLString
import decimal, datetime

class Item():
	def __init__(self, quantity, article, price):
		self.quantity = quantity
		self.article = article
		self.price = price

class ItemForm(Form):
	item_choices = ['dress', 'suit - 2pc', 'suit - 3pc', 'trousers', 'shorts', 't-shirt', 'shirt', 'other'] # fill in
	item_choices = [(choice, choice) for choice in item_choices]
	quantity = IntegerField('Qt.', validators = [validators.DataRequired()])
	article = SelectField('Type', choices = item_choices, validators = [validators.DataRequired()])
	price = DecimalField('Price', places = 2, validators = [validators.DataRequired()])

	field_classes = {
		'Qt.': "item_quantity form-control",
		'Type': "item_article form-control",
		"Price": "item_price form-control"
	}

	def __str__(self):
		return ' -- '.join([str(self.quantity.data), self.article.data, str(self.price.data)])

class DatePickerWidget(object):
	html_params = staticmethod(html_params)

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)
		kwargs.setdefault('data-name', field.name)
		value = kwargs.get('value')
		if value:
			del kwargs['value']
		else:
			value = field.data
			if not value:
				value = ''
			kwargs['data-date'] = value
		return HTMLString('<div class="bfh-datepicker" data-format="y-m-d" %s>\
			</div>' % self.html_params(**kwargs))

class PhoneWidget(object):
	html_params = staticmethod(html_params)

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)
		kwargs.setdefault('name', field.name)
		kwargs.setdefault('value', field.data)
		return HTMLString('<input type="text" class="form-control bfh-phone" data-format="(ddd) ddd-dddd" %s>' % self.html_params(**kwargs))

class TransactionForm(Form):
	type_choices = ['payment', 'discount']
	type_choices = [(choice, choice) for choice in type_choices]

	amount = DecimalField('Amount', places = 2, validators = [validators.DataRequired()])
	description = SelectField('Type', choices = type_choices, validators = [validators.DataRequired()])
	date = DateField('Date', widget = DatePickerWidget(), validators = [validators.DataRequired()])
	error_field = HiddenField('errors')
	id_field = IntegerField('Id', widget = HiddenInput(), validators = [validators.Optional()])

	field_classes = {
		'Amount': "transaction_amount form-control",
		'Type': "transaction_type form-control",
		"Date": "transaction_date form-control"
	}

	def __init__(self, *args, **kwargs):
		if 'obj' in kwargs:
			transaction = kwargs['obj']
			if transaction:
				kwargs['id_field'] = transaction.id
		Form.__init__(self, *args, **kwargs)
		
		if not self.date.data:
			self.date.data = datetime.date.today()

	@property
	def kwargs(self):
		return dict(amount = self.amount.data, description = self.description.data, date = self.date.data, id = self.id_field.data)

	def populate_obj(self, transaction):
		transaction.amount = self.amount.data
		transaction.description = self.description.data
		transaction.date = self.date.data

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
	phone = StringField('Phone', widget = PhoneWidget(), validators = [validators.DataRequired(), validators.Length(min = 14, max = 14)])
	order_num = IntegerField('Order #', validators = [validators.DataRequired()])
	order_date = DateField('Order Date', widget = DatePickerWidget(), validators = [validators.DataRequired()])
	est_pickup_date = DateField('Est Pickup Date', widget = DatePickerWidget(), validators = [validators.DataRequired()])
	pickup_date = DateField('Pickup Date', widget = DatePickerWidget(), validators = [validators.Optional()])
	location = SelectField('Location', choices = locations, validators = [validators.DataRequired()])
	items_field = FieldList(FormField(ItemForm), min_entries = 1)
	pieces = IntegerField('Pieces', validators = [validators.DataRequired()])
	price = DecimalField('Price', places = 2, validators = [validators.DataRequired()])
	transactions_field = FieldList(FormField(TransactionForm), min_entries = 0, validators = [validators.Optional()])
	paid = DecimalField('Amount Paid', default = 0, places = 2, validators = [validators.Optional()])
	paid_all = BooleanField('Paid', default = False, validators = [validators.Optional()])
	comments = TextAreaField('Comments', render_kw = {"rows": 11, "cols": 70}, validators = [validators.Optional(), validators.Length(max = 250)])
	error_field = HiddenField('errors')
	id_field = IntegerField('Id', widget = HiddenInput(), validators = [validators.Optional()])

	def __init__(self, *args, **kwargs):
		transactions = None
		if 'obj' in kwargs:
			order = kwargs['obj']
			kwargs['first_name'] = order.customer.first_name
			kwargs['last_name'] = order.customer.last_name
			kwargs['phone'] = order.customer.phone
			kwargs['id_field'] = order.id
			transactions = order.transactions.all()
			items = order.items
			items = items.split(', ')
			items = [OrderForm.populate_item(item) for item in items]
			kwargs['items_field'] = items
		Form.__init__(self, *args, **kwargs)

		if transactions:
			for transaction in transactions:
				self.transactions_field.append_entry(data = dict(obj = transaction))

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

	def populate_obj(self, order):
		order.order_num = self.order_num.data
		order.order_date = self.order_date.data
		order.est_pickup_date = self.est_pickup_date.data
		order.pickup_date = self.pickup_date.data
		order.location = self.location.data
		order.items = self.stringify_items()
		order.pieces = self.pieces.data
		order.price = self.price.data
		order.paid = self.paid.data
		order.comments = self.comments.data

	def populate_customer(self, customer):
		customer.first_name = self.first_name.data
		customer.last_name = self.last_name.data
		customer.phone = self.phone.data

	@property
	def customer_kwargs(self):
		return dict(first_name = self.first_name.data, last_name = self.last_name.data, phone = self.phone.data)

	def stringify_items(self):
		item_string = ', '.join([str(entry.form) for entry in self.items_field.entries])
		return item_string

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		if self.paid_all.data and self.paid.data < self.price.data:
			self.paid.data = self.price.data
		return True

class FindOrderForm(Form):
	locations = ['', 'cleaners', 'delivered', 'plant', 'inventory']
	locations = [(location, location) for location in locations]
	
	order_num = IntegerField('Order Number', validators = [validators.Optional()])
	order_date = DateField('Order Date', widget = DatePickerWidget(), validators = [validators.Optional()])
	location = SelectField('Location', choices = locations, validators = [validators.Optional()])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.order_kwargs = None

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		order_kwargs = dict()
		if self.order_num.data:
			order_kwargs['order_num'] = self.order_num.data
		if self.order_date.data:
			order_kwargs['order_date'] = self.order_date.data
		if self.location.data:
			order_kwargs['location'] = self.location.data
		if order_kwargs:
			self.order_kwargs = order_kwargs
			return True
		self.order_kwargs = None
		return False

class FindCustomerForm(Form):
	last_name = StringField('Last Name', validators = [validators.Optional()])
	phone = StringField('Phone', widget = PhoneWidget(), validators = [validators.Optional(), validators.Length(min = 14, max = 14)])

	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		customer_kwargs = dict()
		if self.last_name.data:
			customer_kwargs['last_name'] = self.last_name.data
		if self.phone.data:
			customer_kwargs['phone'] = self.phone.data
		if customer_kwargs:
			self.customer_kwargs = customer_kwargs
			return True
		self.customer_kwargs = None

		return False

class CustomerForm(Form):
	comments = TextAreaField('Comment', render_kw={"rows": 11, "cols": 70}, validators = [validators.DataRequired(), validators.Length(max = 250)])