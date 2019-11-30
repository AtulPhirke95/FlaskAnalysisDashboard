import pymongo
import json
import pandas as pd
import os
import glob
import re

def write_to_excel(excelFileName, dataframeName):
    writer = pd.ExcelWriter(excelFileName)
    dataframeName.to_excel(writer,sheet_name = "Sheet1")
    writer.close()

def new_and_total_creator():
    cwd = os.getcwd()
    cwd=re.sub(r'/modules',"",cwd)
    print(cwd)
    myclient = pymongo.MongoClient(os.environ['db_cred'])
    mydb = myclient["FailureDB"]
    mycol = mydb["FailedData"]

    emptyData = pd.DataFrame(list(mycol.find({"FailureCategory":None})))
    emptyData = emptyData.drop(['First Prediction','Second Prediction'], axis=1)

    notEmptyData = pd.DataFrame(list(mycol.find({"FailureCategory":{"$ne":None}})))
    notEmptyData = notEmptyData.drop(['First Prediction','Second Prediction'], axis=1)

    write_to_excel(cwd +r"/NewFailure.xlsx", emptyData)

    write_to_excel(cwd + r"/TotalFailure.xlsx", notEmptyData)

    myclient.close()
    
    if os.path.exists(cwd +r"/NewFailure.xlsx") and os.path.exists(cwd +r"/TotalFailure.xlsx"):
        return True
    else:
        return False
