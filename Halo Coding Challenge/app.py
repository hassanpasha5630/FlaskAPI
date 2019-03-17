from flask import Flask, request, jsonify, render_template,redirect,url_for,abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import UserMixin , LoginManager, current_user,login_required,logout_user,login_user# keep track of the user logged in
from flask_table import Table, Col
import os

# Init app
app = Flask(__name__)
login = LoginManager(app) # Flask login so we can use it later in the app 

#base directory
basedir = os.path.abspath(os.path.dirname(__file__))


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite_key_value_pairs_Final')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "SECRET!"

# Using SQLALCHEMY
db = SQLAlchemy(app)
# using Marshmallow
ma = Marshmallow(app)

@login.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class Results(Table):
    id = Col('id', show=False)
    key = Col('key')
    value = Col('value')
    

#Now we want to create and keep track of the users 
class User(db.Model,UserMixin):
	id = db.Column(db.Integer,primary_key=True)
	UserName = db.Column(db.String(100),unique=True)
	password = db.Column(db.String(100))
	apiKeys = db.relationship('API_Members',backref="APIOwners")

	def __init__(self, UserName, password,):
		self.UserName = UserName
		self.password = password
		
 
class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'UserName', 'password')


API_UserSchema = UserSchema(strict=True) # for one 
APIs_UserSchema = UserSchema(many=True, strict=True)




#This is espically for users that have signed up 
class API_Members(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  key = db.Column(db.Integer, unique=True)
  value = db.Column(db.String(100))
  user_id = db.Column(db.Integer,db.ForeignKey('user.id')) 

  def __init__(self, key, value,user_id):
    self.key = key
    self.value = value
    self.user_id = user_id
    
class APIMemSchema(ma.Schema):
  class Meta:
    fields = ('id', 'key', 'value','user_id')


API_Mem_schema = APIMemSchema(strict=True) # for one 
APIs_Mem_schema = APIMemSchema(many=True, strict=True) # for many objects


# part one is using the api 
class API(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  key = db.Column(db.Integer, unique=True)
  value = db.Column(db.String(100))

  def __init__(self, key, value):
    self.key = key
    self.value = value
    
class APISchema(ma.Schema):
  class Meta:
    fields = ('id', 'key', 'value')


API_schema = APISchema(strict=True) # for one 
APIs_schema = APISchema(many=True, strict=True) # for many objects

# Createing API set Function given key & value
@app.route('/api/<key>/<value>', methods=['POST'])
def set(key,value):
  print("In set")
  new_object = API(key, value)

  db.session.add(new_object)
  db.session.commit()

  return API_schema.jsonify(new_object)

# getting the value of the desired key 
@app.route('/api/<key>', methods=['GET'])
def get(key):
  
  key_value = API.query.filter_by(key=key).first_or_404()
  return API_schema.jsonify(key_value)

# part 2 creating a user Dashbored for NON users 
#UserDashBoard
@app.route('/UserDashBoard')
def DashBoard():
	return render_template("Application.html")


#ajax for set a key and value 
# we could have called the API url as well by using url redirect & as (url,key=Key,value=Value)
# But for show casing other methods I changed it to this 
@app.route('/setform',methods=['POST'])
def set_ajax():
	Key = request.form['Key']
	Value = request.form['Value']
	print(Key+Value)
	
	new_object = API(Key, Value)
	db.session.add(new_object)
	db.session.commit()

	return API_schema.jsonify(new_object)

@app.route('/getform',methods=['POST'])
def get_ajax():
	print("Hee")
	Key = request.form['Key']
	key_value = API.query.filter_by(key=Key).first_or_404()
	return key_value.value
	
	

#now we will be working on the home page


#home url if user logged in we dont want them to go back mistake so if they do redirect them back
@app.route('/',methods=['GET','POST'])
def home():

	if not current_user.is_authenticated:
		return render_template("index.html")
	else :
		return redirect(url_for('App'))	


#Sign up url using ajax now before I was using a sepearate template, not the best user experience for that 
@app.route('/Signup' ,methods =['POST'] )
def signup():
	UserName = request.form['UserName']
	Password = request.form['Password']
	print(UserName,Password)

	#adding new user into the databse
	newUser = User(UserName,Password)
	print(newUser)
	db.session.add(newUser)
	db.session.commit()
	return ("Success")



#sign in url
@app.route('/login' ,methods = ['POST'])
def signin():
	print("Here")
	UserName = request.form['UserName_login']
	Password = request.form['Password_login']
	print(UserName,Password)

	username = User.query.filter_by(UserName=UserName).first_or_404()
	if username :
		if username.password == Password:
			login_user(username)
			return redirect(url_for('App'))
		else:
			return abort(404)
	
	return('signIn Page')

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('home'))	

@app.route('/App')
@login_required
def App():
	data = API_Members.query.filter_by(user_id=current_user.id)
	table = Results(data)
	table.border = True

	return render_template("Members.html",text=current_user.UserName,table=table)


@app.route('/Memsetform',methods=['POST'])
def set_Members():
	Key = request.form['Key']
	Value = request.form['Value']
	print(Key,Value,current_user.id)
	
	new_object = API_Members(Key, Value,current_user.id)
	db.session.add(new_object)
	db.session.commit()


	return API_schema.jsonify(new_object)


@app.route('/MemUpdateform',methods=['PUT'])
def update_Members():
	Key = request.form['Key']
	Value = request.form['Value']
	print("HHHH",Key,Value,current_user.id)

	data = API_Members.query.filter_by(user_id=current_user.id).filter_by(key=Key).first_or_404()
	data.value = Value

	db.session.commit()

		
	return 'Success'




@app.route('/MemDeleteform',methods=['DELETE'])
def Del_Members():
	Key = request.form['Key']
	print("HERE",Key)

	data2 = API_Members.query.filter_by(user_id=current_user.id).filter_by(key=Key).first_or_404()
	db.session.delete(data2)
	db.session.commit()

		
	return 'Success'


#Run Server
if __name__ == '__main__':
  app.run(debug=True)
