import random
from venv import logger
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy import event
from models import Account
from app import db, app 
import logging
from general import Log, get_env_var, is_docker, all_links, nice_json

# SQLAlchemy allows for the PRAGMA statement to be emitted automatically
# for new connections through the usage of events.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    cursor.close()


import models
from models import Account

ACCOUNT_NUM_LENGTH = 10

class dbCtrl():
    """Wrapper over the accounts database."""
    def __init__(self, logger):
        self.logger = logger
        self.to_json = lambda account: {
            "user_id": account.user_id,
            "accNum": account.number,
            "balance": account.balance
        }

    def getAccountsByUserId(self, user_id, json=False):
        try:
            # A non-existing user_id gives None
            accounts = Account.query.filter_by(user_id=user_id)
            self.logger.debug('Accounts for user_id (%s) are retrieved' % user_id)
            if json:
                return [self.to_json(account) for account in accounts]
            else:
                return accounts
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    # Function to get account balance by user ID
    def getAccountBalanceByUserId(self, user_id):
        try:
            # Assuming you have a relationship between User and Account models
            # and the Account model has a 'balance' attribute
            account = Account.query.filter_by(user_id=user_id).first()
            print(account)
            if account:
                print(account)
                return account.balance
            
        except Exception as error:
            # Handle any exceptions or errors here
            print(error)  # You can log the error or handle it as needed
        return None  # Return None if user or account not found
    
   
    # by userid , update the amount 
    def updateUserBalance(self, user_id, amount):
        try:
            # Retrieve the account by user ID
            account = Account.query.filter_by(user_id=user_id).first()
            if account:
                # Update the account's balance
                account.balance = amount
                db.session.commit()
                return account.balance
        except Exception as error:
            db.session.rollback()
            #logger.error(error)
        return None  # Return None in case of errors or if the account is not found

    def getAccountByNum(self, accNum, json=False):
        try:
            # A non-existing accNum gives None
            a = Account.query.filter_by(number=accNum).first()
            self.logger.debug('Account with number (%s) is retrieved' % accNum)
            if json:
                return self.to_json(a)
            else:
                return a
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def createAccountForUserId(self, user_id, initial_balance):
        res = 1
        try:
            a = Account(user_id=user_id, balance=initial_balance)
            db.session.add(a)
            db.session.commit()
            res = a.number
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)
        return res

    def updateAccount(self, accNum, amount):
        res = None
        a = self.getAccountByNum(accNum)
        if a:
            try:
                a.balance -= amount
                # db.session.add(a) # Uncomment this line if needed
                db.session.commit()
                res = a.balance
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        return res

    def closeAccount(self, accNum):
        res = 1
        a = self.getAccountByNum(accNum)
        if a:
            try:
                db.session.delete(a)
                db.session.commit()
                res = 0
                self.logger.debug('Account with number (%s) is removed' % accNum)
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        return res

    def getAllAccounts(self):
        try:
            accounts = Account.query.all()
            self.logger.debug('All accounts are retrieved')
            return [self.to_json(account) for account in accounts]
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)


