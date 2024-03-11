import os
import sys
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
TOKEN_REQUIRED = get_env_var('TOKEN', False)
try:
    if TOKEN_REQUIRED:
        from MiSSFire import jwt_conditional, Requests
        requests = Requests()
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
if is_docker():
    FLASK_PORT = 80
else:
    FLASK_PORT = 9081



# Assuming 'app' is your Flask app and 'db' is your SQLAlchemy database instance


# Load DB controller
db = dbCtrl(logger)

def prepareDB():
    """Ensure presence of the required DB files."""
    try:
        if isDBVolume():
            if not isDBfile():
                db_create.main()
            return True
        else:
            logger.error(f"Data volume directory {DATAVOL} does not exist or is not writable.")
            return False
    except Exception as e:
        logger.error(f"Error while preparing DB: {str(e)}")
        return False


if not prepareDB():
    logger.error("Missing volume. Terminating.")
    sys.exit(1)

@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links(app)}, 200)

@app.route("/users", methods=['GET'])
def usersIndex():
    res_code = 400
    username = request.args.get('username')
    if username:
        res = {'id': db.getByUsername(username, json=True)['id']}
    else:
        res = db.getAllUsers(json=True)
    if res:
        res_code = 200
    return nice_json(res, res_code)


import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='debug.log', filemode='w')

@app.route("/users", methods=['POST'])
def addUser():
    if not request.json or not 'username' in request.json or \
                           not 'pwd' in request.json:
        abort(400)
    username = request.json['username']
    res = ""
    res_code = 400
    logging.debug(f"Received POST request with username: {username}")
    if not db.isUserName(username):
        pwd = request.json['pwd']
        userJson = db.createUser(username, pwd)
        logging.debug(f"User creation response: {userJson}")
        if userJson != 1 and userJson != 2 and 'id' in userJson:
            res = {'id': userJson['id']}
            res_code = 200
    else:
        res = "User already exists"
    return nice_json(res, res_code)

@app.route("/users/userID/<int:userID>", methods=['DELETE'])
@jwt_conditional(requests)
def removeUser(userID):
    if db.isUserID(userID):
        db.removeUserID(userID)
        res = "User (userID=%s) removed" % userID
    else:
        res = "User (userID=%s) non-existent" % userID
    return nice_json({'Result': res}, 201)



@app.route("/users/login", methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or \
                           not 'pwd' in request.json:
        abort(400)
    res = {}
    res_code = 403

    username = request.json['username']
    pwd = request.json['pwd']

    isAllowedCode = db.isUserAllowed(username, pwd)
    print(isAllowedCode)
    if isAllowedCode == 0:
        if TOKEN_REQUIRED:
            accessToken = requests.create_access_token(username)
            if accessToken:
                res = {'access_token': accessToken}
                res_code = 201
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
    app.run(host= '0.0.0.0', port=9081, debug=True)



if __name__ == "__main__":
    main() 