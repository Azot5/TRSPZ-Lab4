from flask import Flask, request, jsonify, abort
from decimal import Decimal

app = Flask(__name__)

users = []
categories = []
records = []
currencies = []
accounts = []

user_id_counter = 1
category_id_counter = 1
record_id_counter = 1
currency_id_counter = 1
account_id_counter = 1

def get_variant(group_number):
    return group_number % 3

@app.route('/currency', methods=['GET'])
def get_currencies():
    return jsonify(currencies)

@app.route('/currency', methods=['POST'])
def create_currency():
    global currency_id_counter
    data = request.get_json()
    if 'name' not in data or 'symbol' not in data:
        abort(400, description="Name and symbol are required")
    currency = {
        'id': currency_id_counter,
        'name': data['name'],
        'symbol': data['symbol']
    }
    currencies.append(currency)
    currency_id_counter += 1
    return jsonify(currency), 201

@app.route('/user/<int:user_id>/currency', methods=['POST'])
def set_default_currency(user_id):
    user = next((u for u in users if u['id'] == user_id), None)
    if user is None:
        abort(404, description="User not found")
    data = request.get_json()
    if 'currency_id' not in data:
        abort(400, description="Currency id is required")
    currency = next((c for c in currencies if c['id'] == data['currency_id']), None)
    if currency is None:
        abort(404, description="Currency not found")
    user['default_currency'] = currency
    return jsonify(user), 200

@app.route('/category', methods=['GET'])
def get_categories():
    return jsonify(categories)

@app.route('/category', methods=['POST'])
def create_category():
    global category_id_counter
    data = request.get_json()
    if 'name' not in data:
        abort(400, description="Name is required")
    category = {
        'id': category_id_counter,
        'name': data['name'],
        'user_id': data.get('user_id')  
    }
    categories.append(category)
    category_id_counter += 1
    return jsonify(category), 201


@app.route('/account', methods=['POST'])
def create_account():
    global account_id_counter
    data = request.get_json()
    if 'user_id' not in data or 'balance' not in data:
        abort(400, description="User id and balance are required")
    account = {
        'id': account_id_counter,
        'user_id': data['user_id'],
        'balance': Decimal(data['balance'])  
    }
    accounts.append(account)
    account_id_counter += 1
    return jsonify(account), 201

@app.route('/account/<int:user_id>', methods=['GET'])
def get_account(user_id):
    account = next((a for a in accounts if a['user_id'] == user_id), None)
    if account is None:
        abort(404, description="Account not found")
    return jsonify(account)

@app.route('/account/<int:user_id>/add', methods=['POST'])
def add_funds(user_id):
    account = next((a for a in accounts if a['user_id'] == user_id), None)
    if account is None:
        abort(404, description="Account not found")
    data = request.get_json()
    if 'amount' not in data:
        abort(400, description="Amount is required")
    account['balance'] += Decimal(data['amount'])
    return jsonify(account)

# Записи витрат
@app.route('/record', methods=['POST'])
def create_record():
    global record_id_counter
    data = request.get_json()
    if 'user_id' not in data or 'category_id' not in data or 'amount' not in data:
        abort(400, description="User id, category id, and amount are required")
    
    # Перевіряємо баланс
    account = next((a for a in accounts if a['user_id'] == data['user_id']), None)
    if account is None:
        abort(404, description="Account not found")
    
    # Отримуємо валюту для запису
    user = next((u for u in users if u['id'] == data['user_id']), None)
    
    if user and 'default_currency' in user:
        currency = user['default_currency']
    else:
        if len(currencies) > 0:
            currency = currencies[0]  # Якщо валюта не задана, використовуємо першу
        else:
            abort(404, description="No currencies available")  # Якщо немає валют, повертаємо помилку

    # Перевіряємо, чи достатньо грошей на рахунку
    if account['balance'] < Decimal(data['amount']):
        abort(400, description="Insufficient funds")

    # Створюємо запис
    record = {
        'id': record_id_counter,
        'user_id': data['user_id'],
        'category_id': data['category_id'],
        'amount': Decimal(data['amount']),
        'currency': currency['symbol'],
        'timestamp': data.get('timestamp', '2024-12-14T00:00:00')
    }

    # Оновлюємо баланс рахунку
    account['balance'] -= Decimal(data['amount'])

    records.append(record)
    record_id_counter += 1
    return jsonify(record), 201


# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
