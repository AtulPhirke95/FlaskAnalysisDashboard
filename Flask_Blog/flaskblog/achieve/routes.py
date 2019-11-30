from flask import Flask, render_template, url_for, flash, redirect
from flaskblog.forms import RegistrationForm, LoginForm,ForgotPasswordForm,UpadateAccountForm,AdminAccountForm,UpdateUserEmailFormByAdmin,UpdateUserPasswordFormByAdmin
from flaskblog import app, bcrypt
from flaskblog import mongo
from flask_login import login_user
from flaskblog import login_manager
from flask_login import UserMixin
from flask_login import current_user,logout_user,login_required
from flask import request
from flaskblog.models import User
from bson import ObjectId
import secrets
import os
import shutil
from datetime import datetime

import sys
cwd_path_to_backend_modules = os.getcwd()
pathToFolderContainingScripts = cwd_path_to_backend_modules + r"\Failure Analysis_MongoDB\modules\\"
sys.path.append(pathToFolderContainingScripts)

import json_data_prep as jd
import data_segregator as ds
import Failure
import data_updation as du

import flask_admin as admin

from wtforms import form, fields

from flask_admin.form import Select2Widget
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.model.fields import InlineFormField, InlineFieldList

#Home page
@app.route("/home")
@login_required
def home():
    posts = mongo.db.FailedData.find({"FailureCategory":None})
    flag_to_show_data_on_home_page = mongo.db.homepagedata.find_one({})
    return render_template('home.html', todos=posts,flag_to_show_data = flag_to_show_data_on_home_page["flag_to_show"])

#Home page: Showing selected records on the page
@app.route("/show",methods=['POST'])
@login_required
def show_results():
    if request.method == 'POST':
        entries = int(request.values.get('show-results'))
        if entries != 999:
            flash("We would reccommend you to select MAX for better filtering results",'danger')
        values = mongo.db.FailedData.find({"FailureCategory":None}).limit(entries)
        return render_template('home.html', todos=values)

#Routing to update page for updating category
@app.route("/update")
@login_required
def update ():
  id=request.values.get("_id")
  #task= mongo.db.FailedData.find_one({"_id":ObjectId(id)})
  return render_template('update.html',task=ObjectId(id),h="Updating entry",t="x")

#Dropdown for updating category
@app.route("/action3/<id>", methods=['POST'])
def action3 (id):
  #Updating a Task with various references
  now = datetime.now()
  x=current_user.username
  category=request.values.get("category")
  mongo.db.FailedData.update_one({"_id":ObjectId(id)},{"$set":{"FailureCategory":category}})
  if mongo.db[x].find({"_id":ObjectId(id)}).count() == 0:
      mongo.db[x].insert_one(mongo.db.FailedData.find_one({"_id":ObjectId(id)}))
      mongo.db[x].update_one({"_id":ObjectId(id)},{"$set":{"Date":now.strftime("%d/%m/%Y %H:%M:%S")}})
      return redirect(url_for("home"))
  else:
      mongo.db[x].update_one({"_id":ObjectId(id)},{"$set":{"FailureCategory":category,"Date":now.strftime("%d/%m/%Y %H:%M:%S")}})
      return redirect(url_for("completed"))


#Recentely updated page
@app.route("/completed")
@login_required
def completed():
    x=current_user.username
    completed_tasks = mongo.db[x].find()
    flag_to_show_data_on_home_page = mongo.db.homepagedata.find_one({})
    return render_template('completed.html', title='Completed Tasks',todos=completed_tasks,flag_to_show_data = flag_to_show_data_on_home_page["flag_to_show"])

#Analysis page for showing graphs
@app.route("/analysisview")
@login_required
def analysis_view():
    root_list = create_stackedBarChart()
    list_final_categories_with_count = create_pieChart()
    flag_to_show_data_on_home_page = mongo.db.homepagedata.find_one({})
    return render_template('analysisview.html', title='Analysis View',data_pie=list_final_categories_with_count,data_bar=root_list,flag_to_show_data = flag_to_show_data_on_home_page["flag_to_show"])

def create_stackedBarChart():
    barChartList=[]
    aggregation_string=[{"$group":{"_id":{"Team":"$Team","FailureCategory":"$FailureCategory"},"Total":{"$sum":1}}},{"$sort":{"_id":-1}}]
    barChartData = mongo.db.FailedData.aggregate(aggregation_string)
    for _ in barChartData:
        _["_id"]["Total"] = _["Total"]
        del _["Total"]
        barChartList.append(_['_id'])

    main_dict = dict()
    
    for data in barChartList:
        if data["Team"] in main_dict:
            # append the new number to the existing array at this slot
            main_dict[data["Team"]].append([data["FailureCategory"],data["Total"]])
        else:
            # create a new array in this slot
            main_dict[data["Team"]] = [[data["FailureCategory"],data["Total"]]]

    root_list=[]

    count_of_categories = mongo.db.FailedData.distinct("FailureCategory")

    for key, values in main_dict.items():
        child_list = []
        child_list.append(key)
        
        child_dict={}
        for _ in values:
            child_dict[_[0]] = _[1]

        for i in count_of_categories:
           child_list.append(child_dict.get(i,0))
        root_list.append(child_list)
        
    if count_of_categories.count(None) > 0:
        count_of_categories[count_of_categories.index(None)] = 'Not Analyzed'
        
    count_of_categories.insert(0,"Teams")
    
    root_list.insert(0,count_of_categories)
    
    return root_list


def create_pieChart():
    count_of_categories = mongo.db.FailedData.distinct("FailureCategory")
    list_categories = []
    list_final_categories_with_count = []
    list_final_categories_with_count.append(['Failure Category', 'Count'])
    #if len(count_of_categories) == 8:
    for _ in count_of_categories:
        if _ is not None:
            list_categories.append(_)
            list_categories.append(mongo.db.FailedData.find({"FailureCategory":_}).count())
            list_final_categories_with_count.append(list_categories)
        list_categories=[]    
    list_final_categories_with_count.append(["Not Analyzed",mongo.db.FailedData.find({"FailureCategory":None}).count()])    
    return list_final_categories_with_count

#For registering new user
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.regUser.insert_one({"email_id":form.email.data,"password":hashed_password,"profile_image_name":"default.jpg"})
        flash(f'Account created for {form.email.data}! You can now login to your account', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

#For login to the tool
@app.route("/")
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.regUser.find_one({"email_id": form.email.data})
        if user and User.check_password(user['password'], form.password.data):
            user_obj = User(username=user['email_id'])  #<flaskblog.models.User object at 0x000001FE386A81D0>
            #login_user(user_obj,remember=form.remember.data)
            login_user(user_obj)
            return redirect('home')
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Sign In', form=form)

#logout button in the tool 
@app.route('/logout')
def logout():
    x=current_user.username
    logout_user()
    #mongo.db[x].drop()
    return redirect(url_for('login'))

#Admin Routing: For login into admin page 
@app.route('/admin',methods=['GET','POST'])
def admin():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = AdminAccountForm()
    if form.validate_on_submit():
        if form.email.data == "admin" and form.password.data == "HelloAdmin":
            return redirect(url_for('dashboardview'))
        else:
            flash("Please enter valid credentials",'danger')
    return render_template("admin.html",form=form)

#Admin Routing: Dashboard view 
@app.route('/dashboardview')
def dashboardview():
    posts = mongo.db.regUser.find({})
    flag_to_show_data_on_home_page = mongo.db.homepagedata.find_one({})
    return render_template("dashboardview.html",title='Dashboard',todos=posts,flag_to_show_data = flag_to_show_data_on_home_page["flag_to_show"])
    
#Admin Routing: Edit button -> for updating email or password of the selected user
@app.route('/updateusercredentials/<id_>',methods=['GET','POST'])
def update_user_credentials_by_admin(id_):
  id=id_
  return render_template('update_user_info_by_admin.html',task=ObjectId(id),h="Updating entry",t="x")

##Admin Routing: routing to choose weather email is to be updated or password of the selected user?
@app.route("/update_admin_action1/<id>", methods=['POST'])
def update_admin_action1(id):
  #Updating a Task with various references
  credential=request.values.get("credential")
  if credential == "Email":
      return redirect(url_for('update_user_email_by_admin',id_=ObjectId(id)))
  elif credential == "Password":
      return redirect(url_for('update_user_password_by_admin',id_=ObjectId(id)))

#Admin Routing: Updating user email id
@app.route("/update_user_email_by_admin/<id_>",methods=['GET','POST'])
def update_user_email_by_admin(id_):
    form = UpdateUserEmailFormByAdmin()
    if form.validate_on_submit():
        collection_name = mongo.db.regUser.find_one({"_id":ObjectId(id_)},{"_id":0,"email_id":1})
        mongo.db.regUser.update_one({"_id":ObjectId(id_)},{"$set":{"email_id":form.email.data}})
        list_of_collections_in_db=[]
        list_of_collections_in_db = mongo.db.collection_names()
        if form.email.data in list_of_collections_in_db:
            mongo.db[collection_name["email_id"]].rename(form.email.data)
            flash("Your account has been updated","success")
        else:
            flash("Your account has been updated","success")
        return  redirect(url_for('dashboardview'))
    return render_template("updateaccountformbyadmin.html",form=form)

#Admin Routing: Updating user password
@app.route("/update_user_password_by_admin/<id_>",methods=['GET','POST'])
def update_user_password_by_admin(id_):
    form = UpdateUserPasswordFormByAdmin()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.regUser.update_one({"_id":ObjectId(id_)},{"$set":{"password":hashed_password}})
        flash("Your account has been updated","success")
        return  redirect(url_for('dashboardview'))
    return render_template("updatepasswordformbyadmin.html",form=form)

#Not implemented yet
@app.route("/reset_password",methods=['GET','POST'])
def reset_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        mongo.db.regUser.update_one({"email_id":email},{'$set':{"password":form.password.data}})
        flash('Your password is successfully rested! Please try to login with new password', 'success')
        return redirect(url_for('login'))
    return render_template('resetpassword.html', title='Reset_password', form=form)

#Admin Routing: Delete button -> deletes the user from record alog with his/her data
@app.route("/deleteusercredentials/<id_>",methods=['GET','POST'])
def deleteusercredentials (id_):
    id=id_
    user_name = mongo.db.regUser.find_one({"_id":ObjectId(id)})
    return render_template('alert_pop_up.html',task=ObjectId(id),user_name = user_name['email_id'], message = "Do you want to delete",h="Deleting user",t="x",url="deleteuserinfo")

#Admin Routing: Deeletion of the selected user based on the action taken(yes or no)
@app.route("/deleteuserinfo/<value>")
def deleteuserinfo(value):
    if value == None:
        return redirect((url_for('dashboardview', title='Dashboard')))
    elif value != None:
        mongo.db.regUser.delete_one({"email_id":value})
        if mongo.db[value].find().count() != 0:
            mongo.db[value].drop()
        return redirect((url_for('dashboardview', title='Dashboard')))
#Admin Routing: Clear button -> Clear the recently updated data of the selected user without removing the user 
@app.route("/clearuserdata/<id_>",methods=['GET','POST'])
def clearuserdata (id_):
    id=id_
    user_name = mongo.db.regUser.find_one({"_id":ObjectId(id)})
    return render_template('alert_pop_up.html',task=ObjectId(id),user_name = user_name['email_id'], message = "Do you want to clear the data of",h="Clear Data",t="x",url="cleardata")

#Admin Routing: Clearing data of the user without distroying it
@app.route("/cleardata/<value>")
def cleardata(value):
    if value == None:
        return redirect((url_for('dashboardview', title='Dashboard')))
    elif value != None:
        if mongo.db[value].find().count() != 0:
            mongo.db[value].drop()
            flash('User data is cleared', 'success')
        return redirect((url_for('dashboardview', title='Dashboard')))

#Common actions taken on admin page(Dashboard view)
#Admin Routing: Clear the data of ALL the user without distroying them
@app.route("/clearalluserdata",methods=['GET','POST'])
def clearalluserdata ():
    return render_template('alert_pop_up_for_clearing_all_data.html', message = "Do you want to clear all the user data",h="Clear All User Data",t="x",url="clearalldata")

#Admin Routing: Clear all user data button
@app.route("/clearalldata/<value>")
def clearalldata(value):
    if value == 'no':
        return redirect((url_for('dashboardview', title='Dashboard')))
    elif value == 'yes':
        c = 0
        list_of_user_collections=[]
        list_of_user_collections = mongo.db.collection_names()
        if "FailedData" in list_of_user_collections:
            list_of_user_collections.remove("FailedData")
        if "regUser" in list_of_user_collections:
            list_of_user_collections.remove("regUser")
        if "homepagedata" in list_of_user_collections:
            list_of_user_collections.remove("homepagedata")
        for user_collections in list_of_user_collections:
            mongo.db[user_collections].drop()
            c+=1        
        if c>0:
            flash('All user data is cleared', 'success')
        else:
            flash('Data is already cleared', 'success')
        return redirect((url_for('dashboardview', title='Dashboard')))

#Admin Routing: Deleting all data failed data along with recently upadated data and not the user
@app.route("/deletefaileddata",methods=['GET','POST'])
def deletefaileddata ():
    return render_template('alert_pop_up_for_clearing_all_data.html', message = "Do you want to delete failuredata",h="Delete Failure Data",t="x",url="deletefailuredata")

#Admin Routing: Delete Failure Data button
@app.route("/deletefailuredata/<value>")
def deletefailuredata(value):
    if value == 'no':
        return redirect((url_for('dashboardview', title='Dashboard')))
    elif value == 'yes':
        c = 0
        list_of_user_collections=[]
        list_of_user_collections = mongo.db.collection_names()
        if "regUser" in list_of_user_collections:
            list_of_user_collections.remove("regUser")
            
        if "homepagedata" in list_of_user_collections:
            list_of_user_collections.remove("homepagedata")
            
        for user_collections in list_of_user_collections:
            mongo.db[user_collections].drop()
            c+=1        
        if "FailedData" in list_of_user_collections:
            mongo.db.FailedData.drop()
            flash('All the data is deleted', 'success')
        else:
            flash('Can not delete the data at this moment. Please check weather the data is already deleted or not?', 'danger')
        return redirect((url_for('dashboardview', title='Dashboard')))

#Admin Routing: Deleting all the user. (Failure data will be there)
@app.route("/deleteallusers",methods=['GET','POST'])
def deleteallusers ():
    return render_template('alert_pop_up_for_clearing_all_data.html', message = "Do you want to delete all the users",h="Delete Failure Data",t="x",url="deleteallusersaccount")

#Admin Routing: Delete All Users button
@app.route("/deleteallusersaccount/<value>")
def deleteallusersaccount(value):
    if value == 'no':
        return redirect((url_for('dashboardview', title='Dashboard')))
    elif value == 'yes':
        c = 0
        list_of_user_collections=[]
        list_of_user_collections = mongo.db.collection_names()
        if "homepagedata" in list_of_user_collections:
            list_of_user_collections.remove("homepagedata")
        if "FailedData" in list_of_user_collections:
            list_of_user_collections.remove("FailedData")
        for user_collections in list_of_user_collections:
            mongo.db[user_collections].drop()
            c+=1        
        if "regUser" in list_of_user_collections:
            mongo.db.regUser.drop()
            flash('All the users are deleted', 'success')
        else:
            flash('Can not delete the users', 'danger')
        return redirect((url_for('dashboardview', title='Dashboard')))


#Admin Routing: If yes then show data on the home page, recently updated page and Analysis view else show nothing
@app.route("/showdataonhomepage",methods=['GET','POST'])
def showdataonhomepage():
    if request.method == 'POST':
        entries = request.values.get('show-results')
        show_data_on_home_page=[]
        show_data_on_home_page = mongo.db.collection_names()
        if "homepagedata" in show_data_on_home_page:
            mongo.db.homepagedata.update_one({},{"$set":{"flag_to_show":entries}})
        elif "homepagedata" not in show_data_on_home_page:
            mongo.db.homepagedata.insert_one({"flag_to_show":entries})
        return redirect((url_for('dashboardview', title='Dashboard')))




""" Account related information like profile pic and name
@app.route("/account",methods=['GET','POST'])
@login_required
def account():
    form = UpadateAccountForm()
    if form.validate_on_submit():
        tempusername=current_user.username
        current_user.username=form.email.data
        mongo.db.regUser.update_one({"email_id":tempusername},{'$set':{"email_id":current_user.username}})
        flash("Your account has been updated")
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.email.data=current_user.username
    user = mongo.db.regUser.find_one({'email_id':current_user.username})
    image_path = user['profile_image_name']
    path_ = os.path.join(app.root_path,'static\profile_pics',image_path)
    #print(path_)
    mongo.send_file(image_path)
    return render_template('account.html', title='Account',form=form,image_path=image_path)


    
@app.route("/update_decision")
@login_required
def update_decision():
    return render_template('profile_update_decision.html', title='Update profile pic?')

@app.route("/updateprofilepic/<value>")
@login_required
def updateprofilepic(value):
    if value == 'no':
        return redirect((url_for('account', title='Account')))
    elif value == 'yes':
        return '''
            <form method='post' action="/newprofilepic" enctype="multipart/form-data">
                <input type="file" name="profile_image">
                <input type ="submit">
            </form>
            <a href="/account">Go back to account?</a>
        '''

@app.route('/newprofilepic',methods=['POST'])
@login_required
def newprofileppic():
    if request.method == 'POST':
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            random_hex = secrets.token_hex(8)
            #x = random_hex + profile_image.filename
            path_ = os.path.join(app.root_path,'static/profile_pics/x/')
            #shutil.move(profile_image,path_+profile_image.filename)
            mongo.save_file(profile_image.filename, profile_image)
            #mongo.save_file(path_, profile_image)
            mongo.db.regUser.update_one({"email_id":current_user.username},{"$set":{"profile_image_name":profile_image.filename}})
            if os.path.exists(path_+ profile_image.filename):
                flash("Profile pic is updated successfully")
            else:
                flash("Profile pic is not updated")  
    return redirect((url_for('account', title='Account')))
"""


@app.route('/backendpredictions',methods=['GET','POST'])  
def backendpredictions():  
    return render_template('file_upload_form.html')  

@app.route('/uploadfiletoserver', methods = ['POST'])  
def uploadfiletoserver():  
    if request.method == 'POST':  
        f = request.files['file']  
        f.save(f.filename)
        cwd = os.getcwd()
        cwd_new_dest = cwd + r"\Failure Analysis_MongoDB\excel_data\\{}".format(f.filename)
        if os.path.exists(cwd_new_dest):
            os.remove(cwd_new_dest)
        shutil.move(cwd+"\\"+f.filename, cwd_new_dest)
        flash('File {} has been uploaded successfully'.format(f.filename), 'success')
        return redirect(url_for("backendpredictions"))


@app.route('/jsondatapreparation',methods=['GET','POST'])  
def jsondatapreparation():  
    return render_template('file_upload_form_to_get_data_from_db.html')

@app.route('/uploadfileforjsongeneration', methods = ['POST'])  
def uploadfileforjsongeneration():  
    if request.method == 'POST':  
        f = request.files['file']
        f.save(f.filename)
        cwd = os.getcwd()
        cwd_new_dest = cwd + r"\Failure Analysis_MongoDB\excel_data\\{}".format(f.filename)
        if os.path.exists(cwd_new_dest):
            os.remove(cwd_new_dest)
        shutil.move(cwd+"\\"+f.filename, cwd_new_dest)
        cwd = os.getcwd()
        if os.path.exists(cwd_new_dest):
            returned_flag = jd.json_generator(cwd + r"\Failure Analysis_MongoDB\excel_data\{}".format(f.filename))
            if returned_flag == True:
                flash('Db is updated successfully', 'success')
            else:
                flash('Db is not updated successfully', 'danger')
        return redirect(url_for("backendpredictions"))

@app.route('/datasegregator',methods=['GET','POST'])  
def datasegregator():
    returned_flag = ds.new_and_total_creator()
    if returned_flag == True:
        cwd = os.getcwd()
        cwd_new_failure = cwd + r"\Failure Analysis_MongoDB\{}".format("NewFailure.xlsx")
        cwd_total_failure = cwd + r"\Failure Analysis_MongoDB\{}".format("TotalFailure.xlsx")
        
        if os.path.exists(cwd_new_failure) and os.path.exists(cwd_total_failure):
            os.remove(cwd_new_failure)
            os.remove(cwd_total_failure)
        
        shutil.move(cwd+"\\NewFailure.xlsx", cwd_new_failure)
        shutil.move(cwd+"\\TotalFailure.xlsx", cwd_total_failure)
        
        flash('NewFailure and Totalfailure file has been created','success')
    else:
        flash('There is problem in creating new and total file', 'danger')
    return redirect(url_for("backendpredictions"))

@app.route('/predictionsgenerator',methods=['GET','POST'])  
def predictionsgenerator():
    cwd = os.getcwd()
    cwd_path = cwd + r"\Failure Analysis_MongoDB"
    Failure.failure_main(cwd_path)
    if os.path.exists(cwd_path+r"\Predictions.xlsx"):
        flash('Predictions are generated','success')
    return redirect(url_for("backendpredictions"))

@app.route('/predictionsupdationtodb',methods=['GET','POST'])  
def predictionsupdationtodb():
    cwd = os.getcwd()
    cwd_path = cwd + r"\Failure Analysis_MongoDB"
    return_flag = du.updating_predictions_to_db(cwd_path)
    if return_flag == True:
        flash('Predictions are updated to db','success')
    else:
        flash('Predictions are not updated','danger')
    return redirect(url_for("backendpredictions"))

