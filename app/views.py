from flask import render_template, flash, redirect, url_for, request
from app import app, db
from .models import Customer, Order
from .forms import OrderForm, FindOrderForm, FindCustomerForm, CustomerForm

# find order
# 	order number
#	customer name + telephone
# create order
#	order number
#	customer name
#	customer telephone
#	price
#	date
#	return date
#	number of pieces, subtotals

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/new-order', methods = ['GET', 'POST'])
def order():
	form = OrderForm(request.form)
	if request.method == 'POST' and form.validate():
		order = form.order
		customer = form.customer
		db.session.add(order)
		# check if relationships are added
		for transaction in order.transactions:
			db.session.add(transaction)
		db.session.add(customer)
		db.session.commit()
		flash('Adding order')
		return redirect(url_for('order'))
	return render_template('new_order.html',
						   title = 'Order',
						   form = form)


@app.route('/order', methods = ['GET', 'POST'])
@app.route('/order/<int:order_id>', methods = ['GET'])
def find_orders(order_id = None):
	if order_id:
		order = Order.query.filter_by(id = order_id).first()
		if not order:
			flash('Order #%i not found' % order_id)
			return redirect(url_for('find_orders'))
		order_forms = [OrderForm(obj = order, first_name = order.customer.first_name, last_name = order.customer.last_name, phone = order.customer.phone, items_field = order.items, transactions_field = order.transactions.all())]
		return render_template('orders.html',
								order_forms = order_forms)

	order_ids = request.args.getlist('id')
	if order_ids:
		orders = []
		for order_id in order_ids:
			try:
				order = Order.query.filter_by(id = int(order_id)).first()
				if not order:
					flash('Order #%i not found' % order_id)
				else:
					orders.append(order)
			except:
				flash('Order ID #%s invalid' % order_id)
		if not orders:
			flash('No Orders Found')
			return redirect(url_for('find_orders'))
		order_forms = [OrderForm(obj = order, first_name = order.customer.first_name, last_name = order.customer.last_name, phone = order.customer.phone, items_field = order.items, transactions_field = order.transactions.all()) for order in orders]
		return render_template('orders.html',
								title = 'Order Results',
								order_forms = order_forms)

	form = FindOrderForm(request.form)
	if request.method == 'POST' and form.validate():
		orders = form.orders
		if not orders:
			flash('Order(s) not found')
			return redirect(url_for('find_orders'))
		order_forms = [OrderForm(obj = order, first_name = order.customer.first_name, last_name = order.customer.last_name, phone = order.customer.phone, items_field = order.items, transactions_field = order.transactions.all()) for order in orders]
		return render_template('orders.html',
								order_forms = order_forms)
	return render_template('find_order.html',
						   title = 'Find Order',
						   form = form)

@app.route('/edit-order', methods=['POST'])
def edit_order():
	form = OrderForm(request.form)
	if form.validate():
		order = form.order
		if order:
			db.session.add(order)
			# check if relationships are added
			for transaction in order.transactions:
				db.session.add(transaction)
			db.session.commit()
			flash('Changes have been saved')
			return json.dumps({'success': True}), 200, {'ContentType':'application/json'}
	flash('Changes not saved')
	return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
	
@app.route('/customers', methods = ['GET', 'POST'])
@app.route('/customer/<int:customer_id>', methods = ['GET'])
def customer(customer_id = None):
	if customer_id:
		customer = Customer.query.filter_by(id = customer_id).first()
		if not customer:
			flash('Customer #%i not found' % customer_id)
			return redirect(url_for('not_found_error'))
		form = CustomerCommentForm(comments = customer.comments)
		return render_template('customers.html',
								title = 'Customer #%i' % customer_id,
								form = form,
								customers = [customer])

	customer_ids = request.args.getlist('id')
	if customer_ids:
		customers = []
		for customer_id in customer_ids:
			try:
				customer_id = int(customer_id)
				customer = Customer.query.filter_by(id = int(customer_id)).first()
				if not customer:
					flash('Customer #%i not found' % customer_id)
				else:
					customers.append(customer)
			except:
				flash('Customer ID #%s invalid' % customer_id)
		if not customers:
			flash('No Customers Found')
			return redirect(url_for('not_found_error'))
		return render_template('customers.html',
								title = 'Customer Results',
								customers = customers)
	
	form = FindCustomerForm(request.form)
	if request.method == 'POST' and form.validate():
		customers = form.customers
		if not customers:
			flash('Customer(s) not found')
			return redirect(url_for('customer'))
		return render_template('customers.html',
								title = 'Customer Results',
								customers = customers)
	return render_template('find_customer.html',
							title = 'Find Customer',
							form = form)

@app.route('/customer/<int:customer_id>/orders/<location>', methods = ['GET'])
def customer_orders(customer_id, location):
	customer = Customer.query.filter_by(customer_id = customer_id).first()
	if customer:
		orders = []
		if location == 'all':
			orders = customer.orders.all()
		if location in ['cleaners', 'delivered', 'plant']:
			orders = customer.orders.filter_by(location = location).all()
		if orders:
			order_forms = [OrderForm(obj = order, first_name = order.customer.first_name, last_name = order.customer.last_name, phone = order.customer.phone, items_field = order.items, transactions_field = order.transactions.all()) for order in orders]
			form = CustomerCommentForm(comments = customer.comments)
			return render_template('customer_orders.html',
										customer = customer,
										form = form,
										order_forms = order_forms)
	return redirect(url_for('not_found_error'))

@app.route('/customer/<int:customer_id>/comment', methods = ['POST'])
def customer_comments(customer_id):
	form = CustomerForm(request.form)
	if form.validate():
		customer = form.customer
		if customer:
			db.session.add(customer)
			db.session.commit()
			flash('Customer comment added')
			return redirect(url_for('customer', customer_id = customer_id))
		return redirect(url_for('not_found_error'))
	return request.render_template('customer.html',
									customer = customer,
									form = form)

@app.errorhandler(404)
def not_found_error(error = None):
	return render_template('404.html', error = error), 404

@app.errorhandler(500):
def internal_error(error = None):
	db.session.rollback()
	return render_template('500.html', error = error), 500