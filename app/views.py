import datetime, os
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory, abort
from app import app, db
from .models import Customer, Order, Transaction
from .forms import OrderForm, FindOrderForm, FindCustomerForm, CustomerForm

def customer_query(**kwargs):
	return Customer.query.filter_by(**kwargs)

def order_query(**kwargs):
	return Order.query.filter_by(**kwargs)

def transaction_query(**kwargs):
	return Transaction.query.filter_by(**kwargs)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/static/<path:path>')
def send_css(path):
    return send_from_directory(app.static_folder, path)

@app.route('/new-order', methods = ['GET', 'POST'])
def order():
	form = OrderForm(request.form)
	if request.method == 'POST' and form.validate():
		customer = customer_query(**form.customer_kwargs).first()
		print(customer)
		if not customer:
			customer = Customer()
			form.populate_customer(customer)

		order = Order()
		form.populate_obj(order)
		customer.orders.append(order)
		db.session.add(customer)

		for transaction_entry in form.transactions_field.entries:
			transaction_form = transaction_entry.form
			transaction = Transaction()
			transaction_form.populate_obj(transaction)
			order.transactions.append(transaction)

		# handle balances
		# order.update_balance() // only necessary when calculating price and paid
		customer.add_order(order)


		db.session.commit()
		flash('Order Added', 'success')
		return redirect(url_for('order'))
	return render_template('new_order.html',
						   title = 'Order',
						   form = form)

@app.route('/order/id/<int:order_id>', methods = ['GET'])
def show_order(order_id):
	order = order_query(id = order_id).first()
	if not order:
		flash('Order #%i not found' % order_id, 'danger')
		return redirect(url_for('find_orders'))
	order_forms = [OrderForm(obj = order)]
	return render_template('orders.html',
							order_forms = order_forms)

@app.route('/orders', methods = ['GET', 'POST'])
def find_orders():
	order_ids = request.args.getlist('id')
	if order_ids:
		orders = []
		for order_id in order_ids:
			try:
				order = order_query(id = int(order_id)).first()
				if not order:
					flash('Order #%i not found' % order_id, 'danger')
				else:
					orders.append(order)
			except:
				flash('Order ID #%s invalid' % order_id, 'danger')
		if not orders:
			flash('No Orders Found', 'danger')
			return redirect(url_for('find_orders'))
		order_forms = [OrderForm(obj = order) for order in orders]
		return render_template('orders.html',
								title = 'Order Results',
								order_forms = order_forms)

	form = FindOrderForm(request.form)
	if request.method == 'POST' and form.validate():
		search_inventory = False
		if 'location' in form.order_kwargs and form.order_kwargs['location'] == 'inventory':
			del form.order_kwargs['location']
			search_inventory = True
		orders_query = order_query(**form.order_kwargs)
		if search_inventory:
			orders_query = orders_query.filter(Order.location != 'delivered')
		orders = orders_query.all()
		if not orders:
			flash('Order(s) not found', 'info')
			return redirect(url_for('find_orders'))

		order_forms = [OrderForm(formdata = None, obj = order) for order in orders]

		sum_price = sum([order.price for order in orders])
		sum_paid = sum([order.paid for order in orders])
		sum_balance = sum([order.balance for order in orders])

		return render_template('orders.html',
								title = 'Order Results',
								order_forms = order_forms,
								sum_price = sum_price,
								sum_paid = sum_paid,
								sum_balance = sum_balance)
	return render_template('find_order.html',
						   title = 'Find Order',
						   form = form)

@app.route('/edit-order/<int:order_id>', methods=['POST'])
def edit_order(order_id):
	form = OrderForm(request.form)
	if form.validate():
		order = order_query(id = order_id).first()
		if order:
			# handle balances
			customer = order.customer
			customer.remove_order(order)
			form.populate_obj(order)

			for transaction_entry in form.transactions_field.entries:
				transaction_form = transaction_entry.form
				transaction_id = transaction_form.kwargs.get('id')
				transaction = None
				if transaction_id:
					transaction = transaction_query(id = transaction_id).first()
					transaction_form.populate_obj(transaction)
				else:
					transaction = Transaction()
					order.transactions.append(transaction)
				if transaction:
					transaction_form.populate_obj(transaction)
				else:
					flash('Invalid transaction #%s' % transaction_id, 'danger')

			customer.add_order(order)
			db.session.add(customer)
			db.session.commit()
			return jsonify({'success': True}), 200, {'ContentType':'application/json'}

	return jsonify({'success': False}), 400, {'ContentType': 'application/json'}

@app.route('/customer/id/<int:customer_id>', methods = ['GET'])
def show_customer(customer_id):
	customer = customer_query(id = customer_id).first()
	if not customer:
		flash('Customer #%i not found' % customer_id, 'danger')
		return abort(404)
	form = CustomerForm(comments = customer.comments)
	return render_template('customers.html',
							title = 'Customer #%i' % customer_id,
							form = form,
							customers = [customer])


@app.route('/customers', methods = ['GET', 'POST'])
def find_customers():
	customer_ids = request.args.getlist('id')
	if customer_ids:
		customers = []
		for customer_id in customer_ids:
			try:
				customer_id = int(customer_id)
				customer = customer_query(id = customer_id).first()
				if not customer:
					flash('Customer #%i not found' % customer_id, 'danger')
				else:
					customers.append(customer)
			except:
				flash('Customer ID #%s invalid' % customer_id, 'danger')
		if not customers:
			flash('No Customers Found', 'danger')
			return abort(404)
		return render_template('customers.html',
								title = 'Customer Results',
								customers = customers)

	form = FindCustomerForm(request.form)
	if request.method == 'POST' and form.validate():
		customers = customer_query(**form.customer_kwargs).all()
		if not customers:
			flash('Customer(s) not found', 'info')
			return redirect(url_for('find_customers'))
		return render_template('customers.html',
									title = 'Customer Results',
									customers = customers)
	return render_template('find_customer.html',
							title = 'Find Customer',
							form = form)

@app.route('/customer/<int:customer_id>/orders/<location>', methods = ['GET'])
def customer_orders(customer_id, location):
	customer = customer_query(id = customer_id).first()
	if customer:
		orders = []
		if location == 'all':
			orders = customer.orders.all()
		if location in ['cleaners', 'delivered', 'plant']:
			orders = customer.orders.filter_by(location = location).all()
		if orders:
			order_forms = [OrderForm(obj = order) for order in orders]
			form = CustomerForm(comments = customer.comments)
			return render_template('customer_orders.html',
										customer = customer,
										form = form,
										order_forms = order_forms)
	return abort(404)

@app.route('/customer/<int:customer_id>/comment', methods = ['POST'])
def customer_comments(customer_id):
	form = CustomerForm(request.form)
	if form.validate():
		customer = customer_query(id = customer_id).first()
		if customer:
			form.populate_obj(customer)
			db.session.add(customer)
			db.session.commit()
			flash('Customer comment added', 'success')
			return redirect(url_for('show_customer', customer_id = customer_id))
		return abort(404)
	return request.render_template('customer.html',
									customer = customer,
									form = form)

@app.route('/transactions/<int:year>/<int:month>/<int:day>', methods = ['GET'])
def transactions(year, month, day):
	date = datetime.date(year, month, day)
	transactions = transaction_query(date = date).all()
	return render_template('transactions.html',
							title = 'Transactions',
							date = date,
							transactions = transactions)

@app.errorhandler(404)
def not_found_error(error = None):
	return render_template('404.html', error = error), 404

@app.errorhandler(500)
def internal_error(error = None):
	db.session.rollback()
	return render_template('500.html', error = error), 500