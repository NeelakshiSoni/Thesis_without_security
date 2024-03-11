import requests 
def checkout(user_id, token, cart):
        try:
            # Define the URL for checkout
            checkout_url = f'http://localhost:9084/cart/checkout/{user_id}'

            # Create a payload with the user's cart
            payload = {'cart': cart}

            # Create headers with the authorization token
            headers = {
                'Content-Type': 'application/json'
                #'Authorization': f'Bearer {token}'
            }

            # Send a POST request to perform the checkout
            response = requests.post(checkout_url, json=payload, headers=headers)
            print(response)
            # Return the response status code
            return response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error during checkout: {e}")
            return 500  # Return 500 for internal server error
        
print(checkout(2 , "123" , {}))

