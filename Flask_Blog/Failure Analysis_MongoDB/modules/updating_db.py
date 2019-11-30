import pymongo
import json
import os

flag = True
def update_db(json_file_name):
	try:
        	myclient = pymongo.MongoClient(os.environ['db_cred'])
        	mydb = myclient["FailureDB"]
	        mycol = mydb["FailedData"]

        	testList=[]

        	with open(json_file_name) as f:
            		for line in f:
                		testList.append(json.loads(line))
        	mycol.insert_many(testList)
	except:
        	global flag
        	flag = False
	finally:
		myclient.close()
		return flag


