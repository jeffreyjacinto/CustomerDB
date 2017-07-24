import os
import unittest
import datetime, decimal

from config import basedir
from app import app, db
from app.models import Customer, Order, Transaction
from app.views import customer_query, order_query, transaction_query
from app.forms import TransactionForm, OrderForm

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
# add tests
    # def test_avatar(self):
    #     u = User(nickname='john', email='john@example.com')
    #     avatar = u.avatar(128)
    #     expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
    #     assert avatar[0:len(expected)] == expected

    # def test_make_unique_nickname(self):
    #     u = User(nickname='john', email='john@example.com')
    #     db.session.add(u)
    #     db.session.commit()
    #     nickname = User.make_unique_nickname('john')
    #     assert nickname != 'john'
    #     u = User(nickname=nickname, email='susan@example.com')
    #     db.session.add(u)
    #     db.session.commit()
    #     nickname2 = User.make_unique_nickname('john')
    #     assert nickname2 != 'john'
    #     assert nickname2 != nickname

    def test_order(self):
        c = Customer()
        c.first_name = 'Edwin'
        c.last_name = 'Jacinto'
        c.phone = '3108485115'
        assert c.balance == 0
        db.session.add(c)
        db.session.commit()

        assert c == customer_query(phone = '3108485115').first()

        today = datetime.date.today()
        o1 = Order()
        o1.order_num = 716
        o1.order_date = today
        o1.est_pickup_date = today + datetime.timedelta(days = 2)
        o1.location = 'cleaners'
        o1.items = '2 -- pants -- 6.00'
        o1.price = decimal.Decimal(5)
        o1.paid = 0
        o1.comments = None

        c.orders.append(o1)
        db.session.add(c)
        o1.calculate_price()

        c.add_order(o1)
        db.session.commit()

        assert o1 == order_query(order_num = 716).first()
        assert o1.price == 6
        assert c.balance == -o1.price

        o2 = Order()
        o2.order_num = 717
        o2.order_date = today
        o2.price = decimal.Decimal(12)
        c.orders.append(o2)

        t1 = Transaction()
        t1.amount = 5
        t1.date = today
        t1.description = 'payment'
        o2.transactions.append(t1)
        o2.calculate_paid()
        c.add_order(o2)

        db.session.add(c)
        db.session.commit()

        assert o2.paid == t1.amount
        assert c.balance == o2.paid - o2.price - o1.price

        transactions = transaction_query(date = today).all()
        assert t1 in transactions

        t2 = Transaction()
        t2.description = 'payment'
        t2.amount = 6
        t2.date = today + datetime.timedelta(days = 1)

        c.remove_order(o2)
        o2.transactions.append(t2)
        o2.calculate_paid()
        c.add_order(o2)

        db.session.add(c)
        db.session.commit()

        orders = c.orders.all()
        orders_balance = sum([order.balance for order in orders])
        assert c.balance == orders_balance

if __name__ == '__main__':
    unittest.main()