#!/usr/bin/env python3

import os
from app import db
from models import User
from db_config import SQLALCHEMY_DATABASE_URI, DATAVOL
def isDBVolume():
	res = os.path.exists(DATAVOL)
	# print "Volume %s exists: %s" % (DATAVOL, res)
	if res:
		res = isWritable(DATAVOL)
		# print "Volume %s is writable: %s" % (DATAVOL, res)
	return res

def isWritable(directory):
    try:
        filepath = os.path.join(directory, "test.txt")
        with open(filepath, "w") as f:
            f.write("Hello, World!")

        os.remove(filepath)
        return True
    except Exception as e:
        print("{}".format(e))
        return False

def isDBfile():
    return os.path.exists(SQLALCHEMY_DATABASE_URI)



from app import app, db
from models import User

def main():
    with app.app_context():
        if not isDBfile():
            if isWritable(DATAVOL):
                db.create_all()
            else:
                print(f"Data volume directory {DATAVOL} does not exist or is not writable.")


if __name__ == '__main__':
    main()
