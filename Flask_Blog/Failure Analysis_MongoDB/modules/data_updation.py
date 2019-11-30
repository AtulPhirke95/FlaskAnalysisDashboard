import pymongo
import json
import pandas as pd
import os
import glob
import re

#cwd = os.getcwd()
#cwd=re.sub(r'\\modules',"",cwd)

def updating_predictions_to_db(abs_path):
    myclient = pymongo.MongoClient(os.environ['db_cred'])
    mydb = myclient["FailureDB"]
    mycol = mydb["FailedData"]

    availableData = mycol.find()
    if os.path.exists(abs_path+r"/Predictions.xlsx"):
        mainDF = pd.ExcelFile(abs_path+r"/Predictions.xlsx")

        df1 = mainDF.parse("Data")
        df1.rename(columns={'_id':'id','First Prediction':'FirstPrediction','Second Prediction':'SecondPrediction'}, inplace=True)

        for row in df1.itertuples(index=True,name='Pandas'):
            for obj in availableData:
                if str(obj['_id']) == str(getattr(row,"id")):
                    obj['First Prediction'] = str(getattr(row,"FirstPrediction"))
                    obj['Second Prediction'] = str(getattr(row,"SecondPrediction"))
                    #obj['Suggestions'] = str(getattr(row,"SubCategory"))
                    mycol.save(obj)
                    break

        myclient.close()
        return True
    else:
        return False
