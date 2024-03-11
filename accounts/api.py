import os
import sys
from functools import wraps
from flask import Flask, request, abort
from general import Log, get_env_var, is_docker, all_links, nice_json
from db_create import isWritable, isDBfile, isDBVolume
import db_create



from flask_sqlalchemy import SQLAlchemy
from main import dbCtrl
from app import db, app 

# Use the name of the current directory as a service type
serviceType = os.path.basename(os.getcwd())
logger = Log(serviceType).logger

# Setup MiSSFire
if get_env_var('TOKEN', False):
    try:
        from MiSSFire import jwt_conditional, Requests
        requests = Requests()
    except ImportError:
        logger.error("Module MiSSFire is required. Terminating.")
        exit()
else:
    from general import Requests
    requests = Requests()

    def jwt_conditional(reqs):
        def real_decorator(f):
            return f
        return real_decorator

# Setup Flask
if is_docker():
    FLASK_PORT = 80
else:
    FLASK_PORT = 9082



DEFAULT_BALANCE = 100000000

# Load DB controller
db = dbCtrl(logger)

def prepareDB():
    """Ensure presence of the required DB files."""
    res = False
    if db_create.isDBVolume():
        if not db_create.isDBfile():
            db_create.main()
            
        res = True
    return res
    
if not prepareDB():
    logger.error("Missing volume. Terminating.")
    sys.exit(1)

@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links(app)}, 200)

@app.route("/accounts", methods=['GET'])
@jwt_conditional(requests)
def accountsGet():
    userID = request.args.get('userID')
    if userID:
        res = db.getAccountsByUserId(userID, json=True)
    else:
        res = db.getAllAccounts()    
    if res:
        res_code = 200
    else:
        res = {}
        res_code = 400
    return nice_json(res, res_code)

@app.route("/accounts", methods=['POST'])
@jwt_conditional(requests)
def accountsPost():
    if not request.json or not 'userID' in request.json:
        abort(400)
    res = {}
    res_code = 400
    try:
        userID = int(request.json['userID'])
        accNum = db.createAccountForUserId(userID, DEFAULT_BALANCE)
        if accNum != 1:
            res = {'accNum': accNum}
            res_code = 200
    except ValueError:
        msg = "UserID expected integer, received: %s" % request.json['userID']
        logger.warning(msg)
        res = {'msg': msg}
    logger.info("niceJson(res): %s, %s" % (nice_json(res, res_code), res))
    return nice_json(res, res_code)

@app.route("/accounts/<accNum>", methods=['GET'])
@jwt_conditional(requests)
def accountsAccNumGet(accNum):
    res = {}
    res_code = 400
    try:
        accNum = int(accNum)
        res = db.getAccountByNum(accNum, json=True)
        if res:
            res_code = 200
    except ValueError:
        msg = "accNum expected integer, received: %s" % request.json['accNum']
        logger.warning(msg)
        res = {'msg': msg}
    return nice_json(res, res_code)

@app.route("/accounts/<accNum>", methods=['DELETE'])
@jwt_conditional(requests)
def accountsAccNumDel(accNum):
    res = {}
    res_code = 400
    try:
        accNum = int(accNum)
        if db.closeAccount(accNum) == 0:
            res = request.json
            res_code = 200
    except ValueError:
        msg = "accNum expected integer, received: %s" % request.json['accNum']
        logger.warning(msg)
        res = {'msg': msg}
    return nice_json(res, res_code)

@app.route("/accounts/<accNum>", methods=['POST'])
@jwt_conditional(requests)
def accountsAccNumPost(accNum):
    if not request.json or not 'amount' in request.json:
        abort(400)
    res = {}
    res_code = 400
    try:
        accNum = int(accNum)
        amount = int(request.json['amount'])
        new_balance = db.updateAccount(accNum, amount)
        if new_balance:
            res = {'balance': new_balance}
            res_code = 200
    except ValueError:
        msg = "Expected integers: accNum=%s, amount=%s" % (request.json['accNum'], request.json['amount'])
        logger.warning(msg)
        res = {'msg': msg}
    return nice_json(res, res_code)

#update the balance by userID 
@app.route("/accounts/user/<int:user_id>/update_balance", methods=['POST'])
@jwt_conditional(requests)
def updateBalanceByUserId(user_id):
    if not request.json or not 'amount' in request.json:
        abort(400)
    res = {}
    res_code = 400
    try:
        user_id = int(user_id)
        amount = int(request.json['amount'])
        # Call a hypothetical function to update the balance for the user
        new_balance = db.updateUserBalance(user_id, amount)
        if new_balance is not None:
            res = {'balance': new_balance}
            res_code = 200
    except ValueError:
        msg = "Expected integers: user_id=%s, amount=%s" % (user_id, request.json['amount'])
        logger.warning(msg)
        res = {'msg': msg}
    return nice_json(res, res_code)




@app.route("/accounts/user/<int:user_id>", methods=['GET'])
@jwt_conditional(requests)
#by userid fetching balance of that account
def accountByUserIdGet(user_id):
    res = {}
    res_code = 400
    try:
        user_id = int(user_id)
        # Call the corrected getAccountBalanceByUserId function without the 'json' argument
        balance = db.getAccountBalanceByUserId(user_id)
        if balance is not None:
            res = {'balance': balance}
            res_code = 200
    except ValueError:
        msg = "user_id expected integer, received: %s" % user_id
        logger.warning(msg)
        res = {'msg': msg}
    return nice_json(res, res_code)



# All APIs provided by this application, automatically generated
LOCAL_APIS = all_links(app)
# All external APIs that this application relies on, manually created
KNOWN_REMOTE_APIS = []



def main():
    """
#     logger.info("%s service starting now: MTLS=%s, Token=%s" \
#                 % (SERVICE_TYPE, MTLS, TOKEN))
#     # Start Flask web server
#     if MTLS and serviceCert:
#         # SSL configuration for Flask. Order matters!
#         cert = serviceCert.getServiceCertFileName()
#         key = serviceCert.getServiceKeyFileName()
#         if cert and key:
            
#             app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, \
#                     ssl_context=(cert,key))
#         else:
#             logger.error("Cannot serve API without SSL cert and key.")
#             exit()
#     else:
      """
    app.run(host= '0.0.0.0', port=9082, debug=True)



if __name__ == "__main__":
    main() 
