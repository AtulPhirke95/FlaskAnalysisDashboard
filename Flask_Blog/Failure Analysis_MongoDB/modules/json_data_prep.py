import json
import pandas as pd
import updating_db as up_db
import os
import glob
import re
import datetime
import argparse


def json_generator(path_a):
    cwd = os.getcwd()
    cwd=re.sub(r'/modules',"",cwd)
    cwd = cwd + r'/Failure Analysis_MongoDB'

    #current date and time
    now = datetime.datetime.now()
    timestamp = datetime.datetime.timestamp(now)
    timestamp = str(timestamp).replace('.','_')
    print("timestamp = ", timestamp)

    #mainDF = pd.ExcelFile(cwd+r"\excel_data\mail_data_issue.xlsx")

    mainDF = pd.ExcelFile(path_a)
    df1 = mainDF.parse("TestCase")
    json_file = cwd+r"/temp_files/temp"+timestamp+'.json'
    
    df1 = df1.astype({"ExecutionDate": str})

    with open(json_file, 'w') as f:
        f.write(df1.to_json(orient='records', lines=True))

    returned_flag = up_db.update_db(cwd+r"/temp_files/"+"temp"+timestamp+'.json')

    if returned_flag == True:
        print("DB is initialized...")

    return returned_flag
