import os
##os.system('pip install cloudpickle==0.6.1')
##os.system('pip install matplotlib==2.1.0')
##os.system('pip install pandas==0.23.4')
##os.system('pip install numpy==1.16.3')
##os.system('pip install sklearn')
##os.system('pip install openpyxl==2.6.0')
##os.system('pip install xlsxwriter')
##os.system('pip install xlrd')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.multiclass import OneVsRestClassifier
import openpyxl
import re

#cwd = os.getcwd()
#cwd=re.sub(r'\\modules',"",cwd)


def writer_To_Excel(excelFile, sheetName, data, ind):
    writer = pd.ExcelWriter(excelFile, engine='xlsxwriter')
    data.to_excel(writer, sheet_name=sheetName, index=ind)
    writer.save()

def load_Train_Data(excelFile):
    totalFailure = pd.read_excel(excelFile)
    le = preprocessing.LabelEncoder()
    x_team_train = le.fit_transform(totalFailure['Team'].astype(str))
    x_step_train = le.fit_transform(totalFailure['FailedStep'].astype(str))
    x_log_train = le.fit_transform(totalFailure['FailedLog'].astype(str))
    x_train = np.array([x_team_train, x_step_train, x_log_train]).transpose()
    y_train = np.array(totalFailure['FailureCategory'])
    return x_train, y_train


def load_Test_Data(excelFile):
    testFailure = pd.read_excel(excelFile)
    le = preprocessing.LabelEncoder()
    x_team_test = le.fit_transform(testFailure['Team'].astype(str))
    x_step_test = le.fit_transform(testFailure['FailedStep'].astype(str))
    x_log_test = le.fit_transform(testFailure['FailedLog'].astype(str))

    x_test = np.array([x_team_test, x_step_test, x_log_test]).transpose()
    return x_test

def predict_Category_Probabilites(x_train, y_train, classifier,x_test):
    #--------------Create linear regression object----------------
    if classifier == "LogisticRegression":
        reg = LogisticRegression(multi_class = 'ovr')
    elif classifier == "LogisticRegression":
        reg = OneVsRestClassifier(SVC(kernel='rbf'))
    elif classifier == "KNeighborsCalssifier":
        reg = KNeighborsClassifier(n_neighbors=15)
    elif classifier == "DecisionTreeClassifier":
        reg = DecisionTreeClassifier()  #most accurate results
    elif classifier == "GaussianNB":
        reg = GaussianNB()

    #----------------------train the model using the training sets------------
    reg.fit(x_train, y_train)
    #------------prediction---------------------------------------
    y_predict_probs = reg.predict_proba(x_test)
    classes = list(reg.classes_)
    y_predict_probs = pd.DataFrame(y_predict_probs, columns=classes)
    return y_predict_probs

def get_Error_Count(ExcelFile,abs_path):
    failureSheet = pd.read_excel(abs_path + '/Predictions.xlsx')
    errorLog = failureSheet['FailedLog']
    teamNames = failureSheet['Team']

    teamDict = {}

    reg = re.compile('at.tosca.javaengine[a-zA-Z.]+')

    for i in range(0, len(errorLog)):
        team = teamNames[i]

        fullException = reg.search(str(errorLog[i]))

        if fullException != None:
            exceptionArray = fullException.group(0).split('.')
            exception = exceptionArray[len(exceptionArray) - 1]
            if team in teamDict.keys():
                if exception in teamDict[team].keys():
                    teamDict[team][exception] = teamDict[team][exception] + 1
                else:
                    teamDict[team][exception] = 1
            else:
                teamDict[team] = {exception : 1}

    for key in teamDict.keys():
        errorCounts = pd.Series(teamDict[key])
        sortedCounts = errorCounts.sort_values(ascending = False)
        teamDict[key] = sortedCounts.to_dict()

        print(key)
        print(sortedCounts)
    return teamDict

def predict_Two_Categories(predicted_probs,abs_path):
    probs = pd.read_excel(abs_path + r'/NewFailure.xlsx')
    headers = list(predicted_probs)
    probs = np.array(predicted_probs)

    predictionList = []

    for r in range(0, probs.shape[0]):
        sample = {}
        for c in range(0,len(headers)):
            sample[probs[r][c]] = headers[c]
        sortedKeys = sorted(sample.keys(), reverse=True)
        firstPrediction = sample.get(sortedKeys[0])
        secondPrediction = sample.get(sortedKeys[1])
        predictions = [firstPrediction, secondPrediction]
        predictionList.append(predictions)

    predictionValues = pd.DataFrame(predictionList, columns=['First Prediction', 'Second Prediction'])

    return predictionValues


def load_Data(excelFile):
    loadedData = pd.read_excel(excelFile)
    return loadedData

#------------------------Generate graphs--------------------

def plot_Graphs(teamDict):
    for key in teamDict.keys():
        x1 = teamDict[key].keys()
        y1 = teamDict[key].values()
        width = 1/1.5
        plt.figure(figsize=[15.0, 9.0])
        plt.bar(x1, y1, width)
        plt.title(key)
        plt.savefig(key+'')

def failure_main(abs_path):

    #load training data-------------------------
    x_train, y_train = load_Train_Data(abs_path + r'/TotalFailure.xlsx')

    #load test data-------------------------------
    x_test = load_Test_Data(abs_path + r'/NewFailure.xlsx')

    y_predicted_probs = predict_Category_Probabilites(x_train, y_train, 'DecisionTreeClassifier',x_test)

    #predict probability of each category------------
    predictedCategories = predict_Two_Categories(y_predicted_probs,abs_path)
    #print(predictedCategories)

    testData = load_Data(abs_path + r'/NewFailure.xlsx')
    new_data_df = pd.concat([testData, predictedCategories], axis=1)


    writer = pd.ExcelWriter(abs_path + '/Predictions.xlsx')
    new_data_df.to_excel(writer,sheet_name = "Data")
    writer.close()


    #plot_Graphs(get_Error_Count(abs_path + '\Predictions.xlsx',abs_path))


    #------move-files-----------------------

##    import shutil
##    dir_src = (abs_path + '\modules')
##    dir_dst = (abs_path + '\Prediction-Graphs')
##
##    arr = os.listdir(dir_src)
##
##    for filen in range(len(arr)):
##        if arr[filen].endswith('.png'):
##            ffname = os.path.join(dir_src, arr[filen])
##            shutil.move(ffname, dir_dst)
##
##    print('Done')





