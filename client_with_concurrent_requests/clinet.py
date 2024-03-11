import json
import time
import datetime
from multiprocessing import Process, Queue
import threading
from threading import Barrier
import random
import requests
import urllib3
import psutil
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from general import Log, get_env_var, is_docker, all_links, nice_json

import os
from flask import jsonify

from flask import Flask, request, abort
from requests import codes
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound, ServiceUnavailable
import requests
from general import Log, get_env_var, is_docker, all_links, nice_json


import logging
# Set the default logger to DEBUG to see the Requests library logging info.
#logging.basicConfig(level=logging.DEBUG)
import concurrent.futures

import requests
serviceType = os.path.basename(os.getcwd())
logger = Log(serviceType).logger
app = Flask(__name__)

HOST = '0.0.0.0'
PROT = 80


IS_MISSFIRE = False
IS_MISSFIRE_TOKEN = False

"""

# Setup Flask
# FLASK_DEBUG = getEnvVar('FLASK_DEBUG', False)
# FLASK_HOST = '0.0.0.0'
if is_docker():
    FLASK_PORT = 80
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, "users", 80)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, "accounts", 80)
    INVENTORY_SERVICE_URL = '%s://%s:%s/' % (PROT, "INVENTORY", 80)
    CART_SERVICE_URL = '%s://%s:%s/' % (PROT, "INVENTORY", 80)
else:
    FLASK_PORT = 9085
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, '0.0.0.0', 9081)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, '0.0.0.0', 9082)
    INVENTORY_SERVICE_URL = '%s://%s:%s/' % (PROT, '0.0.0.0', 9083)
    CART_SERVICE_URL = '%s://%s:%s/' % (PROT, "INVENTORY", 9084)
"""

NUM_ORDER_PER_CLIENT = 1
host= '0.0.0.0', 
APIGATEWAY_PORT=9085

class Simulation():
    def __init__(self, procNum):
        self.client = EcommerceClient()
        self.customers = [{'username': str(procNum + 441), 'pwd': '1234'},
                          {'username': str(procNum + 451), 'pwd': '5678'}]
        if len(self.customers) == 0:
            print("No customers to add!")
            exit()

        print("Adding %s customers." % (len(self.customers)))

        # Initialize a multiprocessing manager for sharing data between processes
        manager = multiprocessing.Manager()
        self.shared_queue = manager.Queue()

        # Use a multiprocessing pool to parallelize customer creation
        with multiprocessing.Pool() as pool:
            pool.map(self.create_customer, self.customers)

        # Retrieve the performance data from the queue
        self.queue.put(self.shared_queue.get())

    def create_customer(self, customer):
        print("Creating userid for customer")
        userID = self.client.create_user(customer['username'], customer['pwd'])
        print("UserID", userID)

        if userID:
            customer['userID'] = userID
        else:
            exit()

        if IS_MISSFIRE_TOKEN:
            token = self.client.login(customer['username'], customer['pwd'])
            if token:
                customer['access_token'] = token
            else:
                exit()
        else:
            customer['access_token'] = "notoken"

        accNum = self.client.openAccount(customer['userID'], customer['access_token'])
        print(accNum)

        if accNum:
            customer['accNum'] = accNum
        else:
            exit()

        print("Adding account balance here")
        accBal = self.client.fetch_account_balance(customer["userID"], customer["access_token"])
        print("Account Balance", accBal)
        if accBal:
            customer['accBal'] = accBal
        else:
            exit()

        print("Adding items to customer cart")
        for i in range(1, NUM_ORDER_PER_CLIENT + 1):
            user_cart = self.client.add_to_cart(customer['userID'], customer['access_token'], i, 10)
            print(user_cart)

        if user_cart:
            customer['user_cart'] = user_cart
            print(customer['user_cart'])
        else:
            exit()

        print(customer["user_cart"])

    def print_performance(self):
        endTime = datetime.datetime.now()
        seconds_passed = float((endTime - self.startTime).total_seconds())
        return seconds_passed

    def run_test(self, queue):
        self.queue = queue
        print("Start checking_out_cart.")
        self.startTime = datetime.datetime.now()

        # Create a multiprocessing pool for parallelizing checkout threads
        with multiprocessing.Pool() as pool:
            pool.map(self.checkout_process, range(NUM_ORDER_PER_CLIENT * len(self.customers)))

        cpu_percent = psutil.cpu_percent(interval=1)  # Monitor for 1 second
        memory_info = psutil.virtual_memory()
        print(f"CPU Usage: {cpu_percent}%")
        print(f"Memory Usage: {memory_info.percent}%")

        # Wait for all processes to complete
        pool.close()
        pool.join()

        # Retrieve the performance data from the queue
        self.queue.put(self.print_performance())
        return

    def checkout_process(self, customer_index):
        cpu_percent_before = psutil.cpu_percent(interval=None)  # Monitor immediately
        print(f"CPU Usage before checkout: {cpu_percent_before}%")
        memory_info_before = psutil.virtual_memory()
        print(f"Memory Usage before checkout: {memory_info_before.percent}%")

        res = self.client.checkout(self.customers[customer_index]["userID"],
                                   self.customers[customer_index]["user_cart"])
        cpu_percent_after = psutil.cpu_percent(interval=None)  # Monitor immediately
        print(f"CPU Usage after checkout: {cpu_percent_after}%")
        memory_info_after = psutil.virtual_memory()
        print(f"Memory Usage after checkout: {memory_info_after.percent}%")

        if res:
            print("Checkout successful for user:", self.customers[customer_index]["username"])
        else:
            print("Checkout failed for user:", self.customers[customer_index]["username"])


class EcommerceClient:
    
    def __init__(self):
        self.BASE_URL = "%s://%s:%s" % (PROT, HOST, APIGATEWAY_PORT)
        self.s = requests.Session()
    

    def create_user(self, username, pwd):
        url = 'http://localhost:9081/users'  # Replace with your Flask app's URL
        data = {'username': username, 'pwd': pwd}
        headers = {'Content-Type': 'application/json'}  # Set the Content-Type header to 'application/json'

        try:
            # Serialize the data dictionary to JSON before sending it
            json_data = json.dumps(data)
            response = requests.post(url, data=json_data, headers=headers)
            response.raise_for_status()  # Raise an HTTPError for bad status codes (>= 400)

            if 'User already exists' in response.text:
                # Handle the case where the user already exists
                url += f'?username={username}'
                response = requests.get(url, verify=False, allow_redirects=False, stream=False)
                response.raise_for_status()  # Raise an HTTPError for bad status codes (>= 400)
            
            user_data = response.json()
            
            if 'id' in user_data:
                return user_data['id']
            else:
                print("'id' not found in response data: %s" % user_data)
                return None
        except requests.exceptions.ConnectionError as e:
            print("Connection error create user: %s" % e)
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
            print(f"Response text: {response.text}")
            return None
        
    def fetch_account_balance(self , userID , token ) : 
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

        
        

    def login(self, username, pwd):
        access_token = None
        try:
            url = 'http://localhost:9081/login'
            payload = {'username': username, 'pwd': pwd}
            resp = self.s.post(url, json=payload, verify=False, allow_redirects=False, stream=False)

            resp.raise_for_status()  # Raise an HTTPError for bad status codes (>= 400)

            if 'access_token' in resp.json():
                access_token = resp.json()['access_token']
            else:
                print("'access_token' not found in response data: %s" % resp.json())
        except requests.exceptions.ConnectionError as e:
            print("Connection error during login: %s" % e)
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error during login: {e}")
            print(f"Response text: {resp.text}")
        return access_token
    
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
    
    def openAccount(self, userID, token):
        accNum = None
        url = 'http://localhost:9082/accounts'  # Replace with your endpoint URL
        data = {'userID' : userID}
        headers = {'Content-Type': 'application/json'}  # Set the Content-Type header to 'application/json'

        try:
            # Serialize the data dictionary to JSON before sending it
            json_data = json.dumps(data)
            response = requests.post(url, data=json_data, headers=headers)
            response.raise_for_status()  # Raise an HTTPError for bad status codes (>= 400)

            if 'accNum' in response.json():
                accNum = response.json()['accNum']
            else:
                print("'accNum' not found in response data: %s" % response.json())
                return None
        except requests.exceptions.ConnectionError as e:
            print("Connection error during openAccount: %s" % e)
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
            print(f"Response text: {response.text}")
            return None
        return accNum
    
    def add_to_cart(self, userID, token, product_id, quantity):
        try:
            #print(userID , product_id ,  quantity )
            # Create a payload with user ID and product ID
            payload = {"quantity" : quantity}
            """
            headers = {
                'Content-Type': 'application/json',
                  # Add the Authorization header with the provided token
            }
            """

            # Make a POST request to the cart service to add the item to the cart
            cart_url = f'http://localhost:9084/cart/{userID}/{product_id}'  # Corrected URL formatting

            response = requests.post(cart_url, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad status codes (>= 400)

            if response.status_code == 200:
                updated_cart = response.json() 
                 # Assuming the cart service returns the updated cart in the response
                #print("updated in the cart")
                return updated_cart
            else:
                return {'message': 'Error adding item to cart'}, response.status_code
        except requests.exceptions.ConnectionError as e:
            print("Connection error during add_to_cart: %s" % e)
            return {'message': 'Error adding item to cart'}, 500
        except requests.exceptions.HTTPError as e:
            #print(f"HTTP error during add_to_cart: {e}")
            #print(f"Response text: {response.text}")
            return {'message': 'Error adding item to cart'}, response.status_code
    def checkout(user_id, token, cart):
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


        
                

    

    
        

    

    

    


def main():
    numProcesses = 1
    queueList = []
    processList = []
    for x in range(0,numProcesses):
        q = Queue()
        queueList.append(q)
        p = Process(target=Simulation(x*2).runTest, args=(q,))
        processList.append(p)

    startTime = datetime.datetime.now()
    for p in processList:
        p.start()

    totalTime = 0
    for q in queueList:
        timeElapsed = q.get()
        totalTime+=timeElapsed
        #print "Result", timeElapsed

    endTime = datetime.datetime.now()
    secondsPassed = float((endTime - startTime).total_seconds())
    
    # operationsPerSec = float(NUM_PAYMENTS_PER_CLIENT*numProcesses / totalTime)
    # print "Transactions per second (%d/%f): %f" \
    #      % (NUM_PAYMENTS_PER_CLIENT*numProcesses, totalTime, operationsPerSec)
    operationsPerSec = float(NUM_ORDER_PER_CLIENT*numProcesses / secondsPassed)
    print ("Transactions per second (%d/%f): %f" \
         % (NUM_ORDER_PER_CLIENT*numProcesses, secondsPassed, operationsPerSec))

    for p in processList:
        p.join()




if __name__ == '__main__':
    main()

