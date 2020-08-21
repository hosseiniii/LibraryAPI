from datetime import datetime

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'books_db'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/books_db'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sshosseini98@gmail.com'
app.config['MAIL_PASSWORD'] = '*****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

mongo = PyMongo(app)


@app.route('/', methods=['GET'])
def index():
    return 'hi'


@app.route('/books', methods=['GET'])
def get_all_books():
    all_books = mongo.db.book
    log = mongo.db.log

    output = []
    for book in all_books.find():
        output.append(
            {
                'name': book['name'],
                'author': book['author'],
                'price': book['price'],
                'code': book['code'],
                'available_count': book['available_count'],
                'borrow': book['borrow'],
                'description': book['description']
            }
        )

    log.insert_one(
        {
            'type': 'get all books',
            'status': 'success',
            'time': datetime.now(),
        }
    )

    return jsonify(output)


@app.route('/book/<int:code>', methods=['GET'])
def get_book(code):
    b = mongo.db.book
    log = mongo.db.log

    book = b.find_one(
        {
            'code': code
        }
    )

    if book:
        output = {
            'name': book['name'],
            'author': book['author'],
            'price': book['price'],
            'code': book['code'],
            'available_count': book['available_count'],
            'borrow': book['borrow'],
            'description': book['description']
        }
    else:
        output = {
            'error': 'this book is not available'
        }

    log.insert_one(
        {
            'type': 'get book',
            'status': 'success',
            'time': datetime.now(),
        }
    )

    return jsonify(
        {
            'result': output
        }
    )


@app.route('/book', methods=['POST'])
def add_book():
    books = mongo.db.book
    log = mongo.db.log

    name = request.json['name']
    author = request.json['author']
    price = request.json['price']
    code = request.json['code']
    available_count = request.json['available_count']
    borrow = request.json['borrow']
    description = request.json['description']

    book_id = books.insert(
        {
            'name': name,
            'author': author,
            'price': price,
            'code': code,
            'available_count': available_count,
            'borrow': borrow,
            'description': description,
        }
    )

    code_id = code.find_one(
        {
            'code': code
        }
    )

    new_code = {"$set": {"taken": 'true'}}

    code.update_one(code_id, new_code)

    new_book = books.find_one(
        {
            '_id': book_id
        }
    )

    output = {
        'name': new_book['name'],
        'author': new_book['author'],
        'price': new_book['price'],
        'code': new_book['code'],
        'available_count': new_book['available_count'],
        'borrow': new_book['borrow'],
        'description': new_book['description']
    }

    log.insert_one(
        {
            'type': 'add book',
            'status': 'success',
            'time': datetime.now(),
        }
    )

    return jsonify(
        {
            'result': output,
            'status': 'success'
        }
    )


@app.route('/code', methods=['POST'])
def add_code():
    codes = mongo.db.code
    log = mongo.db.log

    code = request.json['code']
    time = datetime.now()
    taken = False

    if codes.find_one({'code': code}):

        log.insert_one(
            {
                'type': 'add code',
                'status': 'duplicate',
                'time': time,
            }
        )

        return jsonify(
            {
                'status': 'duplicate'
            }
        )

    code_id = codes.insert_one(
        {
            'code': code,
            'time': time,
            'taken': taken,
        }
    )

    new_code = codes.find_one(
        {
            '_id': code_id
        }
    )

    output = {
        'code': new_code['code'],
        'time': new_code['time'],
        'taken': new_code['taken'],
    }

    log.insert_one(
        {
            'type': 'add code',
            'status': 'success',
            'time': time,
        }
    )

    return jsonify(
        {
            'result': output,
            'status': 'success'
        }
    )


@app.route('/book/<int:code>/borrow', methods=['GET'])
def borrow_book(code):
    b = mongo.db.book
    log = mongo.db.log

    book = b.find_one(
        {
            'code': code
        }
    )

    if book:
        new_borrow = {"$set": {"borrow": not book['borrow']}}

        b.update_one(book, new_borrow)

        output = {
            'borrow': not book['borrow']
        }

        log.insert_one(
            {
                'type': 'borrow_book',
                'status': 'success',
                'time': datetime.now(),
            }
        )

        if not book['borrow']:
            state = "امانت گرفته شده"
        else:
            state = "موجود"

        msg = Message('تغییر وضعیت کتاب', sender='sshosseini98@gmail.com', recipients=['sshosseini98@gmail.com'])
        msg.body = "وضعیت کتاب " + book['name'] + " به " + state + "تغییر یافت."
        mail.send(msg)

    else:
        output = {
            'error': 'this book is not available'
        }
        log.insert_one(
            {
                'type': 'borrow_book',
                'status': 'fail',
                'time': datetime.now(),
            }
        )

    return jsonify(
        {
            'result': output
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
