from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# File to store customer names
CUSTOMER_FILE = 'customers.txt'

def read_customers():
    if not os.path.exists(CUSTOMER_FILE):
        return []
    with open(CUSTOMER_FILE, 'r') as file:
        customers = file.read().strip().split(',')
        return [customer.strip() for customer in customers if customer.strip()]

def write_customers(customers):
    with open(CUSTOMER_FILE, 'w') as file:
        file.write(','.join(customers))

@app.route('/list_disabled', methods=['GET'])
def list_disabled():
    customers = read_customers()
    response = {
        "count": len(customers),
        "results": customers
    }
    return jsonify(response)

@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    try:
        data = request.get_json()
        customer_id = data.get("customer-id")
        customers = read_customers()

        if customer_id in customers:
            customers.remove(customer_id)
            write_customers(customers)
            response = {"status": "success"}
        else:
            response = {"status": "nonexist"}
    except Exception as e:
        response = {"status": "failed"}

    return jsonify(response)

if __name__ == '__main__':
    # Ensure the file exists
    open(CUSTOMER_FILE, 'a').close()
    app.run(host="0.0.0.0",debug=True)