
import requests
def fetch_account_balance(user_id):
    try:
        # Make a GET request to the /accounts/user/<user_id> endpoint
        url = f"http://localhost:9082/accounts/user/{user_id}"
        print(url)
        response = requests.get(url)
        print(response)

        if response.status_code == 200:
            account_data = response.json()
            balance = account_data.get("balance", 0.0)
            return balance
        else:
            # Handle error cases, e.g., log the error or return an appropriate value
            return 0.0  # Return a default value for error cases
    except Exception as e:
        # Handle exceptions, e.g., log the error or return an appropriate value
        return 0.0
    

print(fetch_account_balance(1))