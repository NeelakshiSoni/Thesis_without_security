import os
from flask import Flask, request, abort
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound, ServiceUnavailable

from general import log, getEnvVar, isDocker, niceJson, allLinks

# Use the name of the current directory as a service type
serviceType = os.path.basename(os.getcwd())
logger = log(serviceType).logger

if getEnvVar('MTLS', False):
    PROT = 'https'
else:
    PROT = 'http'

# Setup Flask
# FLASK_DEBUG = getEnvVar('FLASK_DEBUG', False)
# FLASK_HOST = '0.0.0.0'
if isDocker():
    FLASK_PORT = 80
    USERS_SERVICE_URL = f'{PROT}://users:80/'
    ACCOUNTS_SERVICE_URL = f'{PROT}://accounts:80/'
    INVENTORY_SERVICE_URL = f'{PROT}://transactions:80/'
    CART_SERVICE_URL = f'{PROT}://payment:80/'
else:
    FLASK_PORT = 80
    USERS_SERVICE_URL = f'{PROT}://0.0.0.0:9081/'
    ACCOUNTS_SERVICE_URL = f'{PROT}://0.0.0.0:9082/'
    INVENTORY_SERVICE_URL = f'{PROT}://0.0.0.0:9083/'
    CART_SERVICE_URL = f'{PROT}://0.0.0.0:9084/'

# Setup MiSSFire
try:
    # PROT = 'http'
    if getEnvVar('MTLS', False) or getEnvVar('TOKEN', False):
        from MiSSFire import Requests
        requests = Requests()

        if getEnvVar('TOKEN', False):
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

app = Flask(__name__)

@app.route("/", methods=['GET'])
def hello():
    return niceJson({"subresource_uris": allLinks(app)}, 200)

@app.route("/users", methods=['GET'])
def userInfo():
    username = request.args.get('username')
    try:
        url = USERS_SERVICE_URL + 'users'
        if username:
            url += f'?username={username}'
        res = requests.get(url)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Users service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"Cannot get user information, status {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

# Continue updating the rest of the code following this pattern
@app.route("/users", methods=['POST'])
def userEnroll():
    if not request.json or not 'username' in request.json or not 'pwd' in request.json:
        abort(400)
    username = request.json['username']
    pwd = request.json['pwd']
    try:
        url = USERS_SERVICE_URL + 'users'
        payload = {'username': username, 'pwd': pwd}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Users service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"Cannot register user {username}, resp {res.text}, status code {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

@app.route("/users/<userID>/accounts", methods=['GET'])
@jwt_conditional(requests)
def accountsInfo(userID):
    try:
        url = ACCOUNTS_SERVICE_URL + f'accounts?userID={userID}'
        res = requests.get(url)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Accounts service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"No accounts found for userID {userID}, status {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

@app.route("/users/<userID>/accounts", methods=['POST'])
@jwt_conditional(requests)
def openAccount(userID):
    try:
        url = ACCOUNTS_SERVICE_URL + 'accounts'
        payload = {'userID': userID}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Accounts service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"Cannot open account for userID {userID}, status code {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

@app.route("/users/<userID>/accounts/<accNum>/transactions", methods=['GET'])
@jwt_conditional(requests)
def transactionsInfo(userID, accNum):
    try:
        url = TRANSACTIONS_SERVICE_URL + f'transactions?accNum={accNum}'
        res = requests.get(url)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Transactions service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"No transactions found for accNum {accNum}, status {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

@app.route("/accounts/<userID>", methods=['POST'])
@jwt_conditional(requests)
def fetch_account_balance(userID  ) : 
        try:
        # Make a GET request to the /accounts/user/<user_id> endpoint
            url = f"http://localhost:9082/accounts/user/{userID}"
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
        
@app.route("cart/checkout/{user_id}", methods=['POST'])
@jwt_conditional(requests)


def checkout(self , user_id, cart):
        try:
            # Define the URL for checkout
            checkout_url = f'http://localhost:9084/cart/checkout/{user_id}'

            # Create a payload with the user's cart
            payload = {'cart': cart}

            # Create headers with the authorization token
            """
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            """

            # Send a POST request to perform the checkout
            response = requests.post(checkout_url, json=payload)

            # Return the response status code
            return response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error during checkout: {e}")
            return 500  # Return 500 for internal server error

@app.route("/login", methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'pwd' in request.json:
        abort(400)
    username = request.json['username']
    pwd = request.json['pwd']
    try:
        url = USERS_SERVICE_URL + 'users/login'
        payload = {'username': username, 'pwd': pwd}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(f"Users service connection error: {e}")

    if int(res.status_code) >= 400:
        logger.warning(f"Cannot login user {username}, resp {res.text}, status code {res.status_code}")
        resp = res.text
    else:
        resp = res.json()
    return niceJson(resp, res.status_code)

@app.route("/logout", methods=['POST'])
@jwt_conditional(requests)
def logout():
    raise NotImplementedError()

# All APIs provided by this application, automatically generated
LOCAL_APIS = allLinks(app)
# All external APIs that this application relies on, manually created
KNOWN_REMOTE_APIS = [USERS_SERVICE_URL + "users",
                    ACCOUNTS_SERVICE_URL + "accounts",
                    Inventory_SERVICE_URL + "transactions",
                    Cart_SERVICE_URL + "cart",
                    USERS_SERVICE_URL + "users/login"]


if __name__ == "__main__":
    """
    logger.info(f"{serviceType} service starting now: MTLS={MTLS}, Token={TOKEN}")
    # Start Flask web server
    if MTLS and serviceCert:
        # SSL configuration for Flask. Order matters!
        cert = serviceCert.getServiceCertFileName()
        key = serviceCert.getServiceKeyFileName()
        if cert and key:
            app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
        else:
            logger.error("Cannot serve API without SSL cert and key.")
            exit()
    else:
    """
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)

        