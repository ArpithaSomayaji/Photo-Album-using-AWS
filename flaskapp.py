import boto3
from flask import Flask, request, render_template, session, redirect, url_for, make_response
import os
import MySQLdb, hashlib, os
from werkzeug.utils import secure_filename
from datetime import datetime
from pymemcache.client.base import Client
import base64

Uploadpath = "/home/ubuntu/Upload"
Downloadpath = "/home/ubuntu/Download"

# Port Details
port = int(os.getenv('PORT', 8000))

app = Flask(__name__)
app.secret_key = "RANDOM"



#Home Page
@app.route('/')
def HomePage():
    return render_template("login.html")

#Login Page
@app.route('/login',methods=['POST','GET'])
def UserLogin():
    if 'username' in session:
        return render_template('index.html', username = session['username'])
    if request.method == 'POST':
        db = MySQLdb.connect("sql-db-instance","Username","password","Db-Name")
        cursor = db.cursor()
        username = request.form['username']
        password = request.form['password']
        if(username == '' or password == ''):
            return render_template('login.html',resultText="Invalid UserName or Password")
        sql = "select Username from Users where Username = '"+username+"' and Password = '"+hashlib.md5(password).hexdigest()+"'"
        cursor.execute(sql)
        if cursor.rowcount == 1:
            results = cursor.fetchall()
            for row in results:
                session['username'] = username
                return render_template('index.html', username = session['username'])
        else:
            return render_template('login.html',resultText="Invalid Password")
    else:
        return render_template('register.html' , resultText ="User Not Present . Please Register")


#Register New USer Page
@app.route('/register',methods=['POST','GET'])
def NavigateToRegister():
    return  render_template('register.html')
#Register New User
@app.route('/registerUser',methods=['POST','GET'])
def RegisterUser():
    if 'username' in session:
        return render_template('index.html', username = session['username'])

    if request.method == 'POST':
        db = MySQLdb.connect("sql-db-instance","Username","password","Db-Name")
        cursor = db.cursor()
        username = request.form['username']
        password = request.form['password']
        if(username == '' or password == ''):
            return render_template('register.html',resultText="UserName or Password empty")
        sql = "select Username from Users where Username='"+username+"'"
        cursor.execute(sql)
        if cursor.rowcount == 1:
            return render_template('register.html', resultText="Username Already Present. Please try a different Name ")

        sql = "insert into Users (Username, Password) values ('"+username+"','"+hashlib.md5(password).hexdigest()+"')"
        cursor.execute(sql)
        db.commit()
        cursor.close()
        return render_template('login.html', resultText="User Regustered Successfully . please Login")
    else:
        return render_template('register.html',resultText="Something went Wrong! Please try again")

#Upload File
@app.route('/upload',methods=['POST','GET'])
def uploadFile():
    if request.method == 'POST':
        print("Test")
        db = MySQLdb.connect("sql-db-instance","Username","password","Db-Name")
        print(db)
        cursor = db.cursor()
        file = request.files['file']
        print(file.filename)
        filename = secure_filename(file.filename)
        file.save(os.path.join(Uploadpath, filename))
        filelastmodified=os.stat(Uploadpath +'/'+filename).st_mtime
        filelastmodified=str(datetime.fromtimestamp(filelastmodified))
        print(filelastmodified)
        title=request.form['title']
        print(title)
        likes=request.form['likes']
        print(likes)
        with open(Uploadpath+'/'+filename, 'rb') as example_file:
            file_contents = base64.standard_b64encode(example_file.read())
        sql = "select Username from Photos where Username = '"+session['username']+"' and Photo = '"+file_contents+"'"
        cursor.execute(sql)
        if cursor.rowcount > 0:
            return render_template('index.html', username = session['username'], resultText="File Already Present.. Rename the file and try!")
        sql = "insert into Photos (Username,Title,Timedate,Likes,Photo,Filename) values ('"+session['username']+"','"+title+"','"+filelastmodified+"','"+likes+"','"+file_contents+"','"+filename+"')"
        cursor.execute(sql)
        db.commit()
        cursor.close()
        return render_template('index.html', username = session['username'], resultText="File uploaded successfully")
    else:
        return render_template('index.html', username = session['username'], resultText="Something Went Wrong !!! TRy again")


#List Images
@app.route('/list_all', methods=['POST','GET'])
def ListAllImages():
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'GET':
        db = MySQLdb.connect("sql-db-instance","Username","password","Db-Name")
        cursor = db.cursor()
        sql = "select * from Photos where Username = '"+session['username']+"'"
        cursor.execute(sql)
        results = cursor.fetchall()
        allImageDetails=[]
        for row in results:
            data={}
            data['PhotoID']=row[0]
            data['Username']=row[1]
            data['Title']=row[2]
            data['Timedate']=row[3]
            data['Likes']=row[4]
            print("contents :" + row[5])
            data['Filename']=row[6]
            data['Fileext']=row[6].rsplit('.',1)[1].lower()
            if(data['Fileext']=='jpg'):
                data['Photo']=row[5]
            else:
                data['Photo']=base64.standard_b64decode(row[5])
            print(data['Fileext'])
            allImageDetails.append(data)
            cursor.close()
        return render_template('mygallery.html',username = session['username'],resultObject=allImageDetails )
    else:
        return render_template('mygallery.html',username = session['username'])

#Download Image
@app.route('/downloadImage', methods=['POST','GET'])
def ImageDownload():
    if request.method == 'POST':
        photoID=request.form['PhotoID']
        db = MySQLdb.connect("sql-db-instance","Username","password","Db-Name")
        cursor = db.cursor()
        sql = "select * from Photos where Username = '"+session['username']+"' and idPhotos = '"+photoID+"' "
        cursor.execute(sql)
        results = cursor.fetchall()
        for row in results:
            file_contents=row[5]
            file_name=row[6]
        print ("name  "+ file_name)
        print("file contents "+ file_contents)
        base64_decode = base64.standard_b64decode(file_contents)
        response = make_response(base64_decode)
        response.headers["Content-Disposition"] = "attachment; filename="+file_name
        cursor.close()
        return response
    else:
        return render_template('mygallery.html', username = session['username'])


#Logout User
@app.route('/logout', methods=['POST','GET'])
def logout():
    if 'username' in session:
        session.pop('username', None)
    return render_template('login.html')


#Main Function
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
