import os
from flask import jsonify

from flask import Flask, request, abort
from requests import codes
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound, ServiceUnavailable
import requests
from general import Log, get_env_var, is_docker, all_links, nice_json




# Use the name of the current directory as a service type
serviceType = os.path.basename(os.getcwd())
logger = Log(serviceType).logger

# Setup MiSSFire
try:
    PROT = 'http'
    if get_env_var('MTLS', False) or get_env_var('TOKEN', False):
        from MiSSFire import Requests
        requests = Requests()
        if get_env_var('MTLS', False):
            PROT = 'https'

        if get_env_var('TOKEN', False):
            from MiSSFire import jwt_conditional
        else:
            def jwt_conditional(reqs):
                def real_decorator(f):
                    return f
                return real_decorator
    else:
        from general import Requests
        requests = Requests()
        def jwt_conditional(reqs):
            def real_decorator(f):
                return f
            return real_decorator
except ImportError:
    logger.error("Module MiSSFire is required. Terminating.")
    exit()



# Setup Flask
# FLASK_DEBUG = getEnvVar('FLASK_DEBUG', False)
# FLASK_HOST = '0.0.0.0'

if is_docker():
    FLASK_PORT = 80
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, "users", 80)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, "accounts", 80)
    INVENTORY_SERVICE_URL = '%s://%s:%s/' % (PROT, "INVENTORY", 80)
else:

    FLASK_PORT = 9084
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, '127.0.0.1', 9081)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, '127.0.0.1', 9082)
    INVENTORY_SERVICE_URL = '%s://%s:%s/' % (PROT, '127.0.0.1', 9083)

app = Flask(__name__)

import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)








@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links(app)}, 200)

cart = {
    1: {1: {'name': 'Product A', 'price': 10.0, 'quantity': 2}},
    2: {2: {'name': 'Product B', 'price': 15.0, 'quantity': 1}},
}


@app.route("/cart", methods=['GET'])
def get_all_carts():
    try:
        return jsonify(cart), 200
    except Exception as e:
        return jsonify({'message': 'Error retrieving carts', 'error': str(e)}), 500




@app.route("/cart/<int:user_id>/<int:product_id>", methods=['POST'])
def add_to_cart(user_id, product_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)

        # Check if the user is authorized to perform this action (e.g., match user_id with JWT claims)
        print(user_id)
        logger.info(f"Unauthorized request by User ID: {user_id}")

        # Get product details from the /products/<int:product_id> endpoint
        product_details = get_product_details(product_id)

        if product_details is None:
            return jsonify({'message': 'Product not found'}), 404

        # Check if the requested quantity is available in the inventory
        if quantity > product_details['stock']:
            return jsonify({'message': 'Not enough stock available'}), 400

        # Initialize the user's cart if it doesn't exist
        if user_id not in cart:
            cart[user_id] = {}

        # Add the product to the user's cart
        if product_id in cart[user_id]:
            cart[user_id][product_id]['quantity'] += quantity
        else:
            cart[user_id][product_id] = {
                'name': product_details['name'],
                'price': product_details['price'],
                'quantity': quantity,
            }

        user_cart = cart.get(user_id, {})
        print("added in teh cart successfully")
        return user_cart
    except Exception as e:
        return jsonify({'message': 'Error adding item to cart', 'error': str(e)}), 500
# Function to retrieve product details from the /products/<int:product_id> endpoint
def get_product_details(product_id):
    try:
        # Make a GET request to the /products/<int:product_id> endpoint
        response = requests.get(f'{INVENTORY_SERVICE_URL}/products/{product_id}')
        print(response)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except ConnectionError as e:
        # Handle connection error here
        return None


@app.route("/cart/<int:user_id>/<int:product_id>", methods=['DELETE'])
@jwt_conditional(requests)
def remove_from_cart(user_id, product_id):
    try:
        print(f"Received user_id: {user_id}, product_id: {product_id}")
        if user_id in cart and product_id in cart[user_id]:
            del cart[user_id][product_id]
            print(cart)
            return jsonify({'message': 'Item removed from cart successfully'}), 200
        else:
            return jsonify({'message': 'Item not found in cart'}), 404
    except Exception as e:
        return jsonify({'message': 'Error removing item from cart', 'error': str(e)}), 500


@app.route("/cart/<int:user_id>", methods=['GET'])
@jwt_conditional(requests)
def get_cart(user_id):
    try:
        print(cart)
        if user_id in cart:
            user_cart = cart[user_id]
            return jsonify(user_cart), 200
        else:
            return jsonify({'message': 'Cart not found for this user'}), 404
    except Exception as e:
        return jsonify({'message': 'Error retrieving cart', 'error': str(e)}), 500

##start


import requests  # Import the requests module

# Define the INVENTORY_SERVICE_URL
INVENTORY_SERVICE_URL = 'http://127.0.0.1:9083'

@app.route("/cart/checkout/<int:user_id>", methods=['POST'])
@jwt_conditional(requests)
def checkout(user_id):
    try:
        # Calculate the total price of items in the cart
        #print("entering")
        total_price = 0.0
        #print(cart[user_id])
        for product_id, product_des in cart[user_id].items():

            print(product_id)
            quant = product_des['quantity']
            print(quant)
            # Make a request to the inventory service to fetch product details
            product_details_response = requests.get(f'{INVENTORY_SERVICE_URL}/products/{product_id}')
            print(f"Product ID: {product_id},  Quantity: {quant}")

            
            if product_details_response.status_code == 200:
                product_details = product_details_response.json()
                price = product_details.get('price', 0.0)  # Get the price from the product details
                
                # Calculate the subtotal for this product and add it to the total price
                print(price)
                subtotal = price * quant
                total_price += subtotal
                print(total_price)
                        
                        
                print(quant)
                
                print(total_price)
            else:
                return jsonify({'message': f'Failed to fetch product details for Product {product_id}'}), 500

        # Fetch the user's account balance
        # Replace with actual function to fetch user's account balance
        user_balance = fetch_account_balance(user_id)
        print("bal" , user_balance)

        # Check if the user has enough balance for the purchase
        if user_balance < total_price:
            return jsonify({'message': 'Insufficient balance for checkout'}), 400

        # Update the user's account balance
        # Replace with actual function to update user's account balance
        updated_balance = update_user_balance(user_id, user_balance - total_price)
        print(updated_balance)
        print(cart[user_id])

        # Update the stock in the inventory service
        for product_id, product_des in cart[user_id].items():
            print("entering this loop ")
            # Calculate the new stock value (current stock - quantity purchased)

            product_details_response = requests.get(f"http://localhost:9083/products/{product_id}")
            print(product_details_response)
            
            if product_details_response.status_code == 200:
                product_details = product_details_response.json()
                current_stock = product_details['stock']
                new_stock_value = current_stock - quant
                print(current_stock, new_stock_value)

                # Make a request to the inventory service to update stock
                url = f"http://localhost:9083/products/{product_id}/updatestock"
                payload = {'stock': new_stock_value}
                update_stock_response = requests.put(url, json=payload)
                
                if update_stock_response.status_code != 200:
                    return jsonify({'message': f'Failed to update stock for Product {product_id}'}), 500
            else:
                return jsonify({'message': f'Failed to fetch product details for Product {product_id}'}), 500
                # Clear the user's cart after a successful checkout
                # Implement the function clear_user_cart(user_id) to clear the cart
        clear_user_cart(user_id)
        return jsonify({'message': 'Checkout successful', 'new_balance': updated_balance}), 200
    except Exception as e:
       return jsonify({'message': 'Error during checkout', 'error': str(e)}), 500

# Function to fetch product details from the inventory service
def fetch_product_details(product_id):
    # Make a GET request to the inventory service to fetch product details
    response = requests.get(f'INVENTORY_SERVICE_URL/products/{product_id}')
    if response.status_code == 200:
        return response.json()
    else:
        return None
  # Replace with the actual URL of your account service



def fetch_account_balance(user_id):
    try:
        # Make a GET request to the /accounts/user/<user_id> endpoint
        url = f"http://localhost:9082/accounts/user/{user_id}"
        print(url)
        response = requests.get(url)
        print(response)

        if response.status_code == 200:
            account_data = response.json()
            account_data = response.json()
            print(account_data , flush=True)

            balance = account_data.get("balance", 0.0)
            return balance
        else:
            # Handle error cases, e.g., log the error or return an appropriate value
            return 0.0  # Return a default value for error cases
    except Exception as e:
        # Handle exceptions, e.g., log the error or return an appropriate value
        return 0.0



import requests



def update_user_balance(user_id, amount):
    try:
        # Define the URL with the provided user_id
        url = f'http://localhost:9082/accounts/user/{user_id}/update_balance'
        print(amount)

        # Create a dictionary containing the amount to update
        payload = {'amount': amount}

        # Send a POST request to update the balance
        response = requests.post(url, json=payload)

        # Check the response status code
        if response.status_code == 200:
            updated_balance = response.json().get('balance')
            return {'status_code': 200, 'message': f"Updated balance for user {user_id}: {updated_balance}"}
        else:
            error_message = response.json().get('msg', 'Failed to update balance.')
            return {'status_code': response.status_code, 'message': error_message}
    except Exception as e:
        # Handle exceptions here, e.g., log the error
        return {'status_code': 500, 'message': 'An error occurred while updating the balance.'}




def update_product_stock(product_id, stock):
    try:
        # Define the URL with the provided product_id
        url = f'http://localhost:9082/products/{product_id}/updatestock'

        # Create a dictionary containing the stock to update
        data = {'stock': stock}

        # Send a PUT request to update the product's stock
        response = requests.put(url, json=data)

        # Check the response status code
        if response.status_code == 200:
            updated_message = response.json().get('message')
            return {'status_code': 200, 'message': updated_message}
        else:
            error_message = response.json().get('message', 'Failed to update stock.')
            return {'status_code': response.status_code, 'message': error_message}
    except Exception as e:
        # Handle exceptions here, e.g., log the error
        return {'status_code': 500, 'message': 'An error occurred while updating the stock.'}


    
def clear_user_cart(user_id):
    if user_id in cart:
        cart.pop(user_id)


def main():
    """
    logger.info("%s service starting now: MTLS=%s, Token=%s" % (SERVICE_TYPE, MTLS, TOKEN))
    # Start Flask web server
    if MTLS and serviceCert:
        # SSL configuration for Flask. Order matters!
        cert = serviceCert.getServiceCertFileName()
        key = serviceCert.getServiceKeyFileName()
        if cert and key:
            app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, ssl_context=(cert, key))
        else:
            logger.error("Cannot serve API without SSL cert and key.")
            exit()
    else:
    
    """
    app.run(host= '0.0.0.0', port=9084, debug=True)



if __name__ == "__main__":
    main()
    


