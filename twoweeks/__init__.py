__author__ = 'davidlarrimore'

import json
from datetime import datetime

from flask import Flask, render_template, request, jsonify, abort, g , flash, url_for, redirect, session, make_response
import twoweeks.config as config
from datetime import timedelta


######################
# BASE CONFIGURATION #
######################

app = Flask(__name__)

app.debug = config.DEBUG
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config['TRAP_BAD_REQUEST_ERRORS'] = config.TRAP_BAD_REQUEST_ERRORS


# API CONFIG
from flask_restful import Resource, Api
api = Api(app)




##########################
# DATABASE CONFIGURATION #
##########################
from twoweeks.database import init_db
from twoweeks.database import db_session
from twoweeks.models import User, Bill, Role, Payment_Plan, Payment_Plan_Item, Feedback
from sqlalchemy.sql import func

init_db()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()



#######################
# EMAIL CONFIGURATION #
#######################
from threading import Thread
from flask.ext.mail import Mail, Message
from .decorators import async

app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

mail = Mail(app)

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body=None, html_body=None):
    msg = Message(subject, recipients=recipients)
    if text_body is not None:
        msg.body = text_body
    if html_body is not None:
        msg.html = html_body

    if text_body is not None and html_body is not None:
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()



#TODO: LOGGING
#logging.basicConfig(filename='twoweeks.log',level=logging.DEBUG)



##################
# AUTHENTICATION #
##################
app.permanent_session_lifetime = timedelta(minutes=config.PERMANENT_SESSION_LIFETIME)
from werkzeug.security import generate_password_hash

from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user, login_required
import base64

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id = user_id).first()


@app.route('/login')
def login():
    return '''
        <form action="/login/check" method="post">
            <p>Username: <input name="username" type="text"></p>
            <p>Password: <input name="password" type="password"></p>
            <input type="submit">
        </form>
    '''


@app.route('/login/check', methods=['post'])
def login_check():
    app.logger.info('User:' + request.form['username'] + ' attempting to login')
    # validate username and password
    if (request.form['username'] is not None and request.form['password'] is not None):
        user = User.query.filter_by(username = request.form['username']).first()
        app.logger.info(user.id);
        if (user is not None and user.verify_password(request.form['password'])):
            app.logger.info('Login Successful')
            login_user(user)
        else:
            app.logger.info('Username or password incorrect')
    else:
        app.logger.info('Please provide a username and password')

    return redirect(url_for('home'))


#APILOGIN
class ApiLoginCheck(Resource):
    def get(self):
        user = None

        if 'username' in session and session['username'] is not '':
            user=User.query.filter_by(username=session['username']).first()
            if user:
                return {"meta":buildMeta(), "error": None, "data":[user.serialize]}
            else:
                return {"meta":buildMeta(), "error":"No Session Found for '"+session['username']+"'", "data":None}
        else:
            return {"meta":buildMeta(), "error":"No Session Found", "data":None}

api.add_resource(ApiLoginCheck, '/api/login_check', '/api/login_check/')








@app.route('/logout')
def logout():
    session['username']= ''
    logout_user()
    return redirect(url_for('/'))


@app.route('/adminLogout')
def adminLogout():
    session['username']= ''
    logout_user()
    return redirect(url_for('/admin/'))




#APILOGIN
class ApiLogin(Resource):
    def post(self):
        username = None
        password = None
        app.logger.info(request.accept_mimetypes)
        if request_is_json():
            app.logger.info('Attempting to login using JSON')
            data = request.get_json()
            app.logger.info(request.data)
            for key,value in data.iteritems():
                print key+'-'+value
                if key == 'username':
                    username = value
                if key == 'password':
                    password = value
        elif request_is_form_urlencode():
            app.logger.info('Attempting to login using x-www-form-urlencoded')
            requestData = json.loads(request.form['data'])
            username = requestData['email']
            password = requestData['password']
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}


        # validate username and password
        if (username is not None and password is not None):
            user = User.query.filter_by(username = username).first()
            if (user is not None and user.verify_password(password)):
                app.logger.info('Login Successful')
                login_user(user)
                session['username']=username
                return {"meta":buildMeta(), "data": None}
            elif (config.DEBUG == True and username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD):
                app.logger.info('Attempting to login as Root User')
                user = User.query.filter_by(username = username).first()
                if (user is None):
                    app.logger.info('No Admin User Found, Creating')
                    newUser = User(username=config.ADMIN_USERNAME, password=config.ADMIN_PASSWORD, email=config.ADMIN_EMAIL, first_name='Admin', last_name='Admin')
                    db_session.add(newUser)
                    db_session.commit()
                    login_user(newUser)
                    session['username']=username
                else:
                    login_user(user)
                    session['username']=username
            else:
                app.logger.info('Username or password incorrect')
                return {"meta":buildMeta(), "error":"Username or password incorrect", "data": None}
        else:
            app.logger.info('Please provide a username and password')
            return {"meta":buildMeta(), "error":"Please provide a username and password", "data": None}


        return {"meta":buildMeta()}

api.add_resource(ApiLogin, '/api/login')




#APILOGOUT
class ApiLogout(Resource):
    def get(self):
        logout_user()
        session['username']= ''
        return {"meta":buildMeta(), "error":None, "data": None}
api.add_resource(ApiLogout, '/api/logout/')



@login_manager.request_loader
def load_user_from_request(request):
    # first, try to login using the api_key url arg
    api_key = request.args.get('api_key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key)
        except TypeError:
            pass
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None




# Unauthorized_handler is the action that is performed if user is not authenticated
@login_manager.unauthorized_handler
def unauthorized_callback():
    app.logger.info(request)
    if '/api' in str(request):
        return {"meta":buildMeta(), "error":"User is not authenticated, please login"}, 401
    elif '/admin' in str(request):
        return redirect('/admin/')
    else:
        return redirect('/')




@app.route('/api/token')
@login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })






###############
# Base Routes #
###############

@app.route('/')
def index():
    #send_email('Test', ['david.larrimore@mixfin.com'], 'Test Flask Email', 'Test Flask Email')
    return render_template('index.html')

@app.route('/home/')
@login_required
def home():
    return render_template('home.html')

@app.route('/admin/')
def adminLogin():
    return render_template('adminLogin.html')


@app.route('/admin/home/')
@login_required
def adminHome():
    return render_template('admin.html')







############
# USER API #
############

#USERS
class ApiUser(Resource):
    @login_required
    def get(self, user_id=None):
        userID = None;

        if user_id is not None:
            userID = user_id
        elif request.args.get('user_id') is not None:
            userID = request.args.get('user_id')

        if userID is not None:
            app.logger.info("looking for user:" + userID)
            user = User.query.filter_by(id=userID).first()
            app.logger.info(user)

            if user is None:
                return {"meta":buildMeta(),"error": "No results returned for user id #"+ userID, "data": None}
            else:
                return jsonify(meta=buildMeta(), data=[user.serialize])
        else:
            users = [i.serialize for i in User.query.all()]
            #TODO: DO NOT RETURN PASSWORDS
            return {"meta":buildMeta(), "data":users}

    @login_required
    def put(self, user_id=None):
        app.logger.info('Accessing User.put')
        id = ''
        username = ''
        new_password = ''
        confirm_password = ''
        email = ''
        first_name = ''
        last_name = ''
        role_id = ''

        if user_id is not None:
            id = user_id
        elif request.args.get('user_id') is not None:
            id = request.args.get('user_id')


        user = User.query.filter_by(id=user_id).first()

        if user is not None:
            if request_is_json():
                app.logger.info('Updating user based upon JSON Request')
                print json.dumps(request.get_json())
                data = request.get_json()
                for key,value in data.iteritems():
                    print key+'-'+str(value)
                    if key == 'new_password':
                        new_password = value
                    if key == 'confirm_password':
                        confirm_password = value
                    elif key == 'email':
                        email = value
                        username = value
                        user.username = value
                        user.email = value
                    elif key == 'first_name':
                        first_name = value
                        user.first_name = value
                    elif key == 'last_name':
                        last_name = value
                        user.last_name = value
            elif request_is_form_urlencode():
                # TODO: Handle nulls
                app.logger.info('Updating user '+username)
                requestData = json.loads(request.form['data'])
                user.username = requestData['email']
                user.email = requestData['email']
                user.last_name = requestData['last_name']
                user.first_name = requestData['first_name']
                confirm_password = requestData['confirm_password']
                password = requestData['password']
            else:
                return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        else:
            return {"meta":buildMeta(), "error":"Could not find user id #"+id, "data": None}

        #TODO: PASSWORD and CONFIRM_PASSWORD comparison

        db_session.commit()
        return {"meta":buildMeta(), "data": "Updated Record with ID " + user_id, "data": None}


    @login_required
    def post(self, user_id=None):
        app.logger.info('Accessing User.post')

        username = ''
        password = ''
        confirm_password = ''
        email = ''
        first_name = ''
        last_name = ''
        role_id = ''

        if request_is_json():
            app.logger.info('Creating new user based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            for key,value in data.iteritems():
                print key+'-'+str(value)
                if key == 'password':
                    password = value
                if key == 'confirm_password':
                    confirm_password = value
                elif key == 'email':
                    username = value
                    email = value
                elif key == 'first_name':
                    first_name = value
                elif key == 'last_name':
                    last_name = value
        elif request_is_form_urlencode():
            app.logger.info('Creating new user based upon other Request')
            requestData = json.loads(request.form['data'])
            username = requestData['email']
            email = requestData['email']
            last_name = requestData['last_name']
            first_name = requestData['first_name']
            confirm_password = requestData['confirm_password']
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        #TODO: PASSWORD and CONFIRM_PASSWORD comparison
        if email is None or password is None:
            return {"meta":buildMeta(), "error":"Email and Password is required", "data": None}

        if User.query.filter_by(username = username).first() is not None:
            return {"meta":buildMeta(), "error":"Username already exists", "data": None}

        newUser = User(username=username, password=password, email=email, first_name=first_name, last_name=last_name)

        db_session.add(newUser)
        db_session.commit()

        return {"meta":buildMeta()}

    @login_required
    def delete(self, user_id):
        app.logger.info("Deleting User #: " + user_id)
        user = User.query.filter_by(id=user_id).first()
        db_session.delete(user)
        db_session.commit()

        return {"meta":buildMeta(), "data": None}

api.add_resource(ApiUser, '/api/user', '/api/user/', '/api/user/<string:user_id>', '/api/users/', '/api/users/<string:user_id>')


















##########
# ME API #
##########

# the ME API covers the logged in user.
class ApiMe(Resource):
    @login_required
    def get(self, user_id=None):

        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if user is None:
            return {"meta":buildMeta(),"error": "No results returned for user id #"+ userID, "data": None}
        else:
            return jsonify(meta=buildMeta(), data=[user.serialize])


    @login_required
    def put(self, user_id=None):
        app.logger.info('Accessing User.put')
        id = ''
        username = None
        new_password = None
        current_password = None
        new_password = None
        confirm_new_password = None
        email = None
        first_name = None
        last_name = None
        account_balance_amount = None

        average_paycheck_amount = None
        next_pay_date = None
        pay_recurrance_flag = None





        if user_id is not None:
            id = user_id
        elif request.args.get('user_id') is not None:
            id = request.args.get('user_id')

        user = User.query.filter_by(id=user_id).first()

        if user is not None:
            if request_is_json():
                app.logger.info('Updating user based upon JSON Request')
                print json.dumps(request.get_json())
                data = request.get_json()
                if data:
                    for key,value in data.iteritems():
                        #print key+'-'+str(value)
                        if key == 'new_password':
                            new_password = value
                        elif key == 'current_password':
                            current_password = value
                        elif key == 'confirm_new_password':
                            confirm_new_password = value
                        elif key == 'email':
                            email = value
                            username = value
                        elif key == 'first_name':
                            first_name = value
                        elif key == 'last_name':
                            last_name = value
                        elif key == 'next_pay_date':
                            next_pay_date = value
                        elif key == 'pay_recurrance_flag':
                            pay_recurrance_flag = value
                        elif key == 'average_paycheck_amount':
                            average_paycheck_amount = value
                        elif key == 'account_balance_amount':
                            account_balance_amount = value
                else:
                    return {"meta":buildMeta(), "error":"No Data Sent", "data": None}
            elif request_is_form_urlencode():
                # TODO: Handle nulls
                app.logger.info('Updating user '+username)
                requestData = json.loads(request.form['data'])
                username = requestData['email']
                email = requestData['email']
                last_name = requestData['last_name']
                first_name = requestData['first_name']
                confirm_new_password = requestData['confirm_new_password']
                new_password = requestData['new_password']
                current_password = requestData['current_password']
                password = requestData['password']
                next_pay_date = requestData['next_pay_date']
                pay_recurrance_flag = requestData['pay_recurrance_flag']
                average_paycheck_amount = requestData['average_paycheck_amount']
                account_balance_amount = requestData['account_balance_amount']
            else:
                return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        else:
            return {"meta":buildMeta(), "error":"Could not find user id #"+id, "data": None}

        #TODO: PASSWORD and CONFIRM_PASSWORD comparison
        #TODO: Prevent Username or Email Change without confirmation token!?!



        if first_name:
            user.first_name = first_name;
        if last_name:
            user.last_name = last_name;
        if pay_recurrance_flag:
            user.pay_recurrance_flag = pay_recurrance_flag;
        if next_pay_date:
            user.next_pay_date = next_pay_date;
        if average_paycheck_amount:
            user.average_paycheck_amount = average_paycheck_amount
        if account_balance_amount:
            user.account_balance_amount = account_balance_amount

        #Password Change Logic
        if current_password and new_password and confirm_new_password:
            app.logger.info('Current Password:'+user.password+', Proposed Password:'+generate_password_hash(new_password))
            if new_password == confirm_new_password and user.verify_password(current_password) and current_password != new_password:
                app.logger.info("Everything checks out, creating new password")
                user.password = generate_password_hash(new_password)
            elif current_password == new_password:
                app.logger.info("Your new password must be different than your own password")
                return {"meta":buildMeta(), "error":"Your new password must be different than your own password"}
            elif user.verify_password(current_password) == False:
                app.logger.info("Current password does not match our records. Please try again")
                return {"meta":buildMeta(), "error":"Current password does not match our records. Please try again"}
            elif new_password != confirm_new_password:
                return {"meta":buildMeta(), "error":"New passwords do not match"}
            else:
                return {"meta":buildMeta(), "error":"Failed to update Password"}
            #TODO: ADD LOGIC TO MEET PASSWORD COMPLEXITY REQUIREMENTS
        elif new_password and not confirm_new_password:
            return {"meta":buildMeta(), "error":"When changing passwords, both password and confirmation are required"}
        elif confirm_new_password and not new_password:
            return {"meta":buildMeta(), "error":"When changing passwords, both password and confirmation are required"}
        elif current_password and not confirm_new_password or new_password:
            return {"meta":buildMeta(), "error":"New Password not provided, ignoring"}
        elif current_password and not confirm_new_password or new_password:
            return {"meta":buildMeta(), "error":"All required information was not provided to change password"}

        db_session.commit()
        return {"meta":buildMeta(), "data": [user.serialize]}


    @login_required
    def post(self, user_id=None):
        app.logger.info('Accessing User.post')

        id = ''
        username = None
        new_password = None
        current_password = None
        new_password = None
        confirm_new_password = None
        email = None
        first_name = None
        last_name = None
        account_balance_amount = None

        average_paycheck_amount = None
        next_pay_date = None
        pay_recurrance_flag = None

        if request_is_json():
            app.logger.info('Updating user based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            if data:
                for key,value in data.iteritems():
                    #print key+'-'+str(value)
                    if key == 'new_password':
                        new_password = value
                    elif key == 'current_password':
                        current_password = value
                    elif key == 'confirm_new_password':
                        confirm_new_password = value
                    elif key == 'email':
                        email = value
                        username = value
                    elif key == 'first_name':
                        first_name = value
                    elif key == 'last_name':
                        last_name = value
                    elif key == 'next_pay_date':
                        next_pay_date = value
                    elif key == 'pay_recurrance_flag':
                        pay_recurrance_flag = value
                    elif key == 'average_paycheck_amount':
                        average_paycheck_amount = value
                    elif key == 'account_balance_amount':
                        account_balance_amount = value
            else:
                return {"meta":buildMeta(), "error":"No Data Sent", "data": None}
        elif request_is_form_urlencode():
            # TODO: Handle nulls
            app.logger.info('Updating user '+username)
            requestData = json.loads(request.form['data'])
            username = requestData['email']
            email = requestData['email']
            last_name = requestData['last_name']
            first_name = requestData['first_name']
            confirm_new_password = requestData['confirm_new_password']
            new_password = requestData['new_password']
            current_password = requestData['current_password']
            password = requestData['password']
            next_pay_date = requestData['next_pay_date']
            pay_recurrance_flag = requestData['pay_recurrance_flag']
            average_paycheck_amount = requestData['average_paycheck_amount']
            account_balance_amount = requestData['account_balance_amount']
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}



        #TODO: PASSWORD and CONFIRM_PASSWORD comparison
        if email is None or password is None:
            return {"meta":buildMeta(), "error":"Email and Password is required", "data": None}

        if User.query.filter_by(username = username).first() is not None:
            return {"meta":buildMeta(), "error":"Username already exists", "data": None}

        newUser = User(username=username, password=password, email=email, first_name=first_name, last_name=last_name, account_balance_amount=account_balance_amount)

        db_session.add(newUser)
        db_session.commit()

        return {"meta":buildMeta()}

    @login_required
    def delete(self, user_id):
        app.logger.info("Deleting User #: " + user_id)
        user = User.query.filter_by(id=user_id).first()
        db_session.delete(user)
        db_session.commit()

        return {"meta":buildMeta(), "data": None}

api.add_resource(ApiMe, '/api/me', '/api/me/', '/api/me/<string:user_id>', '/api/me/', '/api/me/<string:user_id>')














############
# BILL API #
############

class ApiBill(Resource):
    @login_required
    def get(self, bill_id=None):
        billId = None
        paid_flag = None
        funded_flag = None


        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}



        #TODO: BIND Bill with User ID based upon session
        if bill_id is not None:
            billId = bill_id
        elif request.args.get('bill_id') is not None:
            billId = request.args.get('bill_id')

        if request.args.get('paid_flag') is not None:
            if request.args.get('paid_flag').upper() == 'TRUE':
                app.logger.info('paid flag is TRUE')
                paid_flag = True
            elif request.args.get('paid_flag').upper() == 'FALSE':
                app.logger.info('paid flag is FALSE')
                paid_flag = False

        if request.args.get('funded_flag') is not None:
            if request.args.get('funded_flag').upper() == 'TRUE':
                app.logger.info('funded flag is TRUE')
                funded_flag = True
            elif request.args.get('funded_flag').upper() == 'FALSE':
                app.logger.info('funded flag is FALSE')
                funded_flag = False

        if billId is not None:
            app.logger.info("looking for bill:" + billId)
            bill = Bill.query.filter_by(id=billId, user_id=user.id, paid_flag=paid_flag).first()
            app.logger.info(bill)

            if bill is None:
                return {"meta":buildMeta(), 'data':[]}
            else:
                return jsonify(meta=buildMeta(), data=[bill.serialize])
        else:
            if paid_flag is not None and funded_flag is not None:
                bills = [i.serialize for i in Bill.query.filter_by(user_id=user.id, paid_flag=paid_flag, funded_flag=funded_flag)]
            elif paid_flag is not None:
                bills = [i.serialize for i in Bill.query.filter_by(user_id=user.id, paid_flag=paid_flag)]
            elif funded_flag is not None:
                bills = [i.serialize for i in Bill.query.filter_by(user_id=user.id, funded_flag=funded_flag)]
            else:
                bills = [i.serialize for i in Bill.query.filter_by(user_id=user.id)]
            return {"meta":buildMeta(), "data":bills}

    @login_required
    def put(self, bill_id=None):
        app.logger.info('Accessing Bill.put')

        #TODO: Handle update
        user_id = None
        payee_id = None
        name = None
        description = None
        due_date = None
        billing_period = None
        total_due = None
        paid_flag = None
        paid_date = None
        check_number = None
        payment_type = None
        payment_type_ind = None
        payment_processing_flag = None
        user = None

        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if bill_id is None:
            if request.args.get('bill_id') is not None:
                bill_id = request.args.get('bill_id')
            else:
                return {"meta":buildMeta(), "error":"No Bill ID Provided"}

        bill = Bill.query.filter_by(id=bill_id).first()
        bill.user_id = user.id

        if bill is not None:
            if request_is_json():
                app.logger.info('Updating bill based upon JSON Request')
                print json.dumps(request.get_json())
                data = request.get_json()
                if data:
                    for key,value in data.iteritems():
                        #print key+'-'+str(value)
                        if key == 'name':
                            name = value
                        if key == 'description':
                            description = value
                        elif key == 'due_date':
                            due_date = value
                        elif key == 'billing_period':
                            billing_period = value
                        elif key == 'total_due':
                            total_due = value
                        elif key == 'paid_flag':
                            paid_flag = value
                        elif key == 'paid_date':
                            paid_date = value
                        elif key == 'check_number':
                            check_number = value
                        elif key == 'payment_type':
                            payment_type = value
                        elif key == 'payment_type_ind':
                            payment_type_ind = value
                        elif key == 'payment_processing_flag':
                            payment_processing_flag = value
            elif request_is_form_urlencode():
                app.logger.info('Updating bill #'+bill_id)
                requestData = json.loads(request.form['data'])

                name = requestData['name']
                description = requestData['description']
                due_date = requestData['due_date']
                billing_period = requestData['billing_period']
                total_due = requestData['total_due']
                paid_flag = requestData['paid_flag']
                paid_date = requestData['paid_date']
                check_number = requestData['check_number']
                payment_type = requestData['payment_type']
                payment_type_ind = requestData['payment_type_ind']
                payment_processing_flag = requestData['payment_processing_flag']
            else:
                return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}
        else:
            return {"meta":buildMeta(), "error":"Could not find bill id #"+id}

        if name:
            bill.name = name
        if description:
            bill.description = description
        if due_date:
            bill.due_date = due_date
        if billing_period:
            bill.billing_period = billing_period
        if total_due:
            bill.total_due = total_due
        #TODO: Prevent amount changes if bill is funded or paid

        if paid_flag is not None:
            bill.paid_flag = paid_flag
            if paid_flag and paid_date is None:
                bill.paid_date = datetime.utcnow()

        if paid_date:
            bill.paid_date = paid_date
            bill.paid_flag = True


        if check_number:
            bill.check_number = check_number
        if payment_type:
            bill.payment_type = payment_type
        if payment_type_ind:
            bill.payment_type_ind = payment_type_ind
        if payment_processing_flag is not None:
            bill.payment_processing_flag = payment_processing_flag

        if bill.name is None or bill.name =='' or not bill.name:
            return {"meta":buildMeta(), "error":"Name is required", "data":None}
        else:
            db_session.commit()
            return {"meta":buildMeta(), "data": bill.serialize}, 201

    @login_required
    def post(self, bill_id=None):
        app.logger.info('Accessing Bill.post')

        user = None

        user_id = None
        payee_id = None
        name = None
        description = None
        due_date = None
        billing_period = None
        total_due = None
        paid_flag = None
        paid_date = None
        check_number = None
        payment_type = None
        payment_type_ind = None
        payment_processing_flag = None



        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()

        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if request_is_json():
            app.logger.info('Creating new user based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            for key,value in data.iteritems():
                print key+'-'+str(value)
                if key == 'name':
                    name = value
                if key == 'description':
                    description = value
                elif key == 'due_date':
                    due_date = value
                elif key == 'billing_period':
                    billing_period = value
                elif key == 'total_due':
                    total_due = value
                elif key == 'paid_flag':
                    paid_flag = value
                elif key == 'paid_date':
                    paid_date = value
                elif key == 'check_number':
                    check_number = value
                elif key == 'payment_type':
                    payment_type = value
                elif key == 'payment_type_ind':
                    payment_type = value
                elif key == 'payment_processing_flag':
                    payment_processing_flag = value
        elif request_is_form_urlencode():
            app.logger.info('Creating new user based upon other Request')
            requestData = json.loads(request.form['data'])
            name = requestData['name']
            description = requestData['description']
            due_date = requestData['due_date']
            billing_period = requestData['billing_period']
            total_due = requestData['total_due']
            paid_flag = requestData['paid_flag']
            paid_date = requestData['paid_date']
            check_number = requestData['check_number']
            payment_type = requestData['payment_type']
            payment_type_ind = requestData['payment_type_ind']
            payment_processing_flag = requestData['payment_processing_flag']
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        if Bill.query.filter_by(name = name, user_id = user_id).first() is not None:
            return {"meta":buildMeta(), "error":"Bill already exists"}

        newBill = Bill(user_id=user.id, name=name, description=description, due_date=due_date, billing_period=billing_period, total_due=total_due, paid_flag=paid_flag, paid_date=paid_date, payment_type_ind=payment_type_ind, check_number=check_number, payment_processing_flag=payment_processing_flag)

        db_session.add(newBill)
        db_session.commit()

        return {"meta":buildMeta(), 'data':newBill.serialize}, 201

    @login_required
    def delete(self, bill_id):

        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}


        app.logger.info("Deleting Bill #: " + bill_id)
        bill = Bill.query.filter_by(id=bill_id, user_id=user.id).first()
        if bill is not None:
            db_session.delete(bill)
            db_session.commit()
            return {"meta":buildMeta(), "data" : None}
        else:
            return {"meta":buildMeta(), "error":"Bill #"+bill_id+" Could not be found", "data" : None}

api.add_resource(ApiBill, '/api/bill', '/api/bill/', '/api/bill/<string:bill_id>')
















####################
# PAYMENT PLAN API #
####################

class ApiPaymentPlan(Resource):
    @login_required
    def get(self, payment_plan_id=None):
        paymentPlanId = None
        accepted_flag = None
        bill_id = None

        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        #TODO: BIND payment_plan with User ID based upon session
        if payment_plan_id is not None:
            paymentPlanId = payment_plan_id
        elif request.args.get('payment_plan_id') is not None:
            paymentPlanId = request.args.get('payment_plan_id')

        if request.args.get('accepted_flag') is not None:
            if request.args.get('accepted_flag').upper() == 'TRUE':
                app.logger.info('accepted_flag is true')
                accepted_flag = True
            elif request.args.get('accepted_flag').upper() == 'FALSE':
                app.logger.info('accepted_flag is false')
                accepted_flag = False

        if request.args.get('bill_id') is not None:
            bill_id = request.args.get('bill_id')

        #TODO: Add some logic for "Base_flag" filtering
        if paymentPlanId is not None:
            app.logger.info("looking for payment plan:" + paymentPlanId)
            payment_plan = Payment_Plan.query.filter_by(id=paymentPlanId, user_id=user.id).first()
            app.logger.info(payment_plan)

            if payment_plan is None:
                return {"meta":buildMeta(), 'data':[]}
            else:
                return jsonify(meta=buildMeta(), data=[payment_plan.serialize])
        else:
            if accepted_flag is not None:
                #There should only be 1 record with accepted_flag of false...if there are no records, create one
                if accepted_flag is False:
                    payment_plan = Payment_Plan.query.filter_by(user_id=user.id, accepted_flag=accepted_flag).first()
                    if payment_plan is None:
                        #User does not have a working payment plan...creating new one
                        app.logger.info('User does not have a working payment plan...creating new one')
                        newPaymentPlan = Payment_Plan(user_id=user.id, accepted_flag=False, base_flag=False, amount=0)
                        db_session.add(newPaymentPlan)
                        db_session.commit()
                        payment_plan = newPaymentPlan.serialize
                        return {"meta":buildMeta(), "data":payment_plan}
                    else:
                        return {"meta":buildMeta(), "data":payment_plan.serialize}
                #Get existing payment plans
                else:
                    if bill_id is not None:
                        items = Payment_Plan_Item.query.filter_by(bill_id=bill_id)
                        idList = list();
                        for item in items:
                            idList.append(item.payment_plan_id)

                        payment_plans = [i.serialize for i in Payment_Plan.query.filter(Payment_Plan.id.in_(idList)).all()]

                    else:
                        payment_plans = [i.serialize for i in Payment_Plan.query.filter_by(user_id=user.id, accepted_flag=accepted_flag)]
            else:
                payment_plans = [i.serialize for i in Payment_Plan.query.filter_by(user_id=user.id)]

            return {"meta":buildMeta(), "data":payment_plans}



    @login_required
    def put(self, payment_plan_id=None):
        app.logger.info('Accessing PaymentPlan.put')

        #TODO: Handle update
        user_id = None
        user = None
        amount = None
        base_flag = None
        transfer_date = None
        date_created = None
        last_updated = None
        accepted_flag = None
        payment_plan_items = None


        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if payment_plan_id is None:
            if request.args.get('payment_plan_id') is not None:
                payment_plan_id = request.args.get('payment_plan_id')
            else:
                return {"meta":buildMeta(), "error":"No Payment Plan ID Provided"}

        payment_plan = Payment_Plan.query.filter_by(id=payment_plan_id, user_id=user.id).first()
        app.logger.info(payment_plan)

        if payment_plan is None:
            return {"meta":buildMeta(), 'error':'Could not find Payment Plan', 'data':[]}


        if request_is_json():
            app.logger.info('Updating Payment Plan based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            if data is not None:
                for key,value in data.iteritems():
                    print key+'-'+str(value)
                    if key == 'transfer_date':
                        transfer_date = value
                    elif key == 'accepted_flag':
                        accepted_flag = value
                    elif key == 'payment_plan_items':
                        payment_plan_items = value
                    elif key == 'amount':
                        amount = value
            else:
                return {"meta":buildMeta(), "error":"No JSON Data Sent"}
        elif request_is_form_urlencode():
            app.logger.info('Updating Payment Plan based upon form Request')
            requestData = json.loads(request.form['data'])
            if requestData is not None:
                transfer_date = requestData['transfer_date']
                accepted_flag = requestData['accepted_flag']
                payment_plan_items = requestData['payment_plan_items']
                amount = requestData['amount']
            else:
                return {"meta":buildMeta(), "error":"No form Data Sent"}
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}


        if amount is not None:
            payment_plan.amount = amount

        if payment_plan_items is not None:
            #print "Payment_Plan_Items"
            #print payment_plan_items
            new_payment_plan_items = list()
            for payment_plan_item in payment_plan_items:
                new_payment_plan_items.append(Payment_Plan_Item(payment_plan_id=payment_plan_id, user_id=payment_plan_item['user_id'], bill_id=payment_plan_item['bill_id'], amount=payment_plan_item['amount']))

            Payment_Plan_Item.query.filter_by(payment_plan_id=payment_plan_id).delete()
            db_session.commit()

            payment_plan.payment_plan_items = new_payment_plan_items
            db_session.commit()



        if accepted_flag is not None:
            if str(accepted_flag).upper() == 'TRUE':
                accepted_flag = True
            elif str(accepted_flag).upper() == 'FALSE':
                accepted_flag = False


            if accepted_flag is True:
                payment_plan.accepted_flag = True
                #TODO: NEED TO CHECK TO SEE IF WE HAVE OVER PAID A BILL?

                #TODO: NEED TO UPDATE PAYMENT PLAN ITEMS ACCEPTED FLAG
                payment_plan_items = Payment_Plan_Item.query.filter_by(user_id=user.id, payment_plan_id=payment_plan_id)
                payment_plan_items_list = payment_plan_items.all()
                for payment_plan_item in payment_plan_items_list:
                    payment_plan_item.accepted_flag = True

                payment_plan.payment_plan_items = payment_plan_items_list
                db_session.commit()


                #CHECKING TO SEE IF BILL IS FULLY FUNDED
                #1. Loop through submitted payment plan items
                #2. Query each bill in the payment plan
                #3. sum all funded payment plan items for the bill
                #4. If the amounts match....set bill a "funded"
                for payment_plan_item in payment_plan.payment_plan_items:
                    paid_amount = 0
                    bill = Bill.query.filter_by(id = payment_plan_item.bill_id, user_id = user.id).first()
                    total_paid = db_session.query(func.sum(Payment_Plan_Item.amount).label('sum_amount')).filter(Payment_Plan_Item.bill_id == payment_plan_item.bill_id).filter(Payment_Plan_Item.accepted_flag == True).first()
                    if total_paid is not None:
                        if total_paid.sum_amount is not None:
                            paid_amount = float(total_paid.sum_amount)
                    app.logger.info("Bill Amount = $" + str(bill.total_due))
                    app.logger.info("total_paid = $" + str(round(paid_amount,2)))
                    if round(paid_amount,2) == float(bill.total_due):
                        app.logger.info("Bill '" +bill.name+ "' is fully paid!")
                        bill.funded_flag = True
                        db_session.commit()
                    else:
                        app.logger.info("Bill '" +bill.name+ "' is not fully paid")


            elif accepted_flag is False:
                payment_plan.accepted_flag = False

        payment_plan.last_updated = datetime.utcnow;
        app.logger.info('Saving Payment Plan')
        db_session.commit()
        return {"meta":buildMeta(), "data":payment_plan.serialize}

api.add_resource(ApiPaymentPlan, '/api/payment_plan', '/api/payment_plan/', '/api/payment_plan/<string:payment_plan_id>')
















#########################
# PAYMENT PLAN ITEM API #
#########################

class ApiPaymentPlanItem(Resource):
    @login_required
    def get(self, payment_plan_item_id=None):
        payment_plan_item_id = None
        payment_plan_id = None

        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if payment_plan_item_id is not None:
            paymentPlanId = payment_plan_item_id
        elif request.args.get('payment_plan_item_id') is not None:
            paymentPlanId = request.args.get('payment_plan_item_id')

        if request.args.get('payment_plan_id') is not None:
            payment_plan_id = request.args.get('payment_plan_id')

        if payment_plan_item_id is not None:
            app.logger.info("looking for Payment Plan Item:" + payment_plan_item_id)
            payment_plan_items = Payment_Plan_Item.query.filter_by(id=payment_plan_item_id, user_id=user.id).first()

            if payment_plan_items is None:
                return {"meta":buildMeta(), 'data':[]}
            else:
                return jsonify(meta=buildMeta(), data=[payment_plan_items.serialize])
        else:
            if payment_plan_id is not None:
                payment_plan_items = [i.serialize for i in Payment_Plan_Item.query.filter_by(user_id=user.id, payment_plan_id=payment_plan_id)]
            else:
                payment_plan_items = [i.serialize for i in Payment_Plan_Item.query.filter_by(user_id=user.id)]

            return {"meta":buildMeta(), "data":payment_plan_items}


    @login_required
    def put(self, payment_plan_item_id=None):
        app.logger.info('Accessing PaymentPlanItem.put')

        #TODO: Handle update
        user_id = None
        user = None
        amount = None

        if 'username' in session:
            user=User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}


        if payment_plan_item_id is None:
            if request.args.get('payment_plan_item_id') is not None:
                payment_plan_item_id = request.args.get('payment_plan_item_id')
            else:
                return {"meta":buildMeta(), "error":"No Payment Plan ID Provided"}

        payment_plan_item = Payment_Plan_Item.query.filter_by(id=payment_plan_item_id, user_id=user.id).first()
        app.logger.info(payment_plan_item)

        if payment_plan_item is None:
            return {"meta":buildMeta(), 'error':'Could not find Payment Plan Item', 'data':[]}




        if request_is_json():
            app.logger.info('Updating Payment Plan Item based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            if data is not None:
                for key,value in data.iteritems():
                    print key+'-'+str(value)
                    if key == 'amount':
                        amount = value
            else:
                return {"meta":buildMeta(), "error":"No JSON Data Sent"}
        elif request_is_form_urlencode():
            app.logger.info('Updating Payment Plan Item based upon form Request')
            requestData = json.loads(request.form['data'])
            if requestData is not None:
                amount = requestData['amount']
            else:
                return {"meta":buildMeta(), "error":"No form Data Sent"}
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        if amount is not None:
            payment_plan_item.amount = amount

        app.logger.info('Saving Payment Plan Item')
        db_session.commit()
        return {"meta":buildMeta(), "data":payment_plan_item.serialize}

    @login_required
    def delete(self, payment_plan_item_id=None):
        app.logger.info('Accessing PaymentPlanItem.delete')
        bill_id = request.args.get('bill_id')

        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}

        if payment_plan_item_id is None:
            if bill_id is not None:
                bill = Bill.query.filter_by(id=bill_id, user_id=user.id).first()
                if bill is not None:
                    app.logger.info("Deleting all Payment_plan_items from bill #" + str(bill_id))
                    bill.funded_flag = False;
                    bill.payment_processing_flag = False;
                    Payment_Plan_Item.query.filter_by(bill_id=bill_id).delete()
                    db_session.commit()
                    return {"meta":buildMeta(), "data" : None}
                else:
                    return {"meta":buildMeta(), "error":"Bill #" + str(bill_id) + " Could not be found", "data" : None}
        else:
            payment_plan_item = Payment_Plan_Item.query.filter_by(id=payment_plan_item_id, user_id=user.id).first()
            if payment_plan_item is not None:
                app.logger.info("Deleting Payment_plan_item #" + str(payment_plan_item_id))
                db_session.delete(payment_plan_item)
                db_session.commit()
                return {"meta":buildMeta(), "data" : None}
            else:
                return {"meta":buildMeta(), "error":"Payment Plan Item #" + str(payment_plan_item_id) + " Could not be found", "data" : None}


api.add_resource(ApiPaymentPlanItem, '/api/payment_plan_item', '/api/payment_plan_item/', '/api/payment_plan_item/<string:payment_plan_item_id>')

















################
# FEEDBACK API #
################

class ApiFeedback(Resource):
    @login_required
    def get(self, feedback_id=None):
        feedbackId = None;

        if feedback_id is not None:
            feedbackId = feedback_id
        elif request.args.get('feedback_id') is not None:
            feedbackId = request.args.get('feedback_id')

        if feedbackId is not None:
            app.logger.info("looking for feedback:" + feedbackId)
            feedback = Feedback.query.filter_by(id=feedbackId).first()
            app.logger.info(feedback)

            if feedback is None:
                return {"meta":buildMeta(), 'data':[]}
            else:
                return jsonify(meta=buildMeta(), data=[feedback.serialize])
        else:
            feedbacks = [i.serialize for i in Bill.query.all()]
            return {"meta":buildMeta(), "data":feedbacks}

    @login_required
    def post(self, feedback_id=None):
        app.logger.info('Accessing Feedback.post')

        user = None
        user_id = None
        rating = None
        feedback = None


        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()

        if user is None:
            return {"meta":buildMeta(), "error":"No Session Found"}
        else:
            user_id = user.id;

        if request_is_json():
            app.logger.info('Creating new feedback based upon JSON Request')
            print json.dumps(request.get_json())
            data = request.get_json()
            if data is not None:
                for key,value in data.iteritems():
                    print key+'-'+str(value)
                    if key == 'rating':
                        rating = value
                    if key == 'feedback':
                        feedback = value
        elif request_is_form_urlencode():
            app.logger.info('Creating new user based upon other Request')
            requestData = json.loads(request.form['data'])
            rating = requestData['rating']
            feedback = requestData['feedback']
        else:
            return {"meta":buildMeta(), "error":"Unable to process "+ request.accept_mimetypes}

        if rating is not None and feedback is not None:
            newFeedback = Feedback(user_id=user_id, rating=int(rating), feedback=feedback)

            db_session.add(newFeedback)
            db_session.commit()

            html_message = "<p>Rating: " + str(rating) + "</p><p>Feedback: "+ feedback + "</p>"
            text_message = "Rating: " + str(rating) + "\r\nFeedback: "+ feedback

            send_email('New Feedback', ['"Robert Donovan" <admin@mixfin.com>', '"David Larrimore" <david.larrimore@mixfin.com'], text_message, html_message)

            return {"meta":buildMeta(), 'data':newFeedback.serialize}, 201
        else:
            return {"meta":buildMeta(), 'error':'No feedback was provided'}, 201

api.add_resource(ApiFeedback, '/api/feedback', '/api/feedback/', '/api/feedback/<string:feedback_id>')























####################
# HELPER FUNCTIONS #
####################

def request_is_json():
    if 'application/json' in request.accept_mimetypes:
        return True;
    else:
        return False



def request_is_form_urlencode():
    if 'application/x-www-form-urlencoded' in request.accept_mimetypes:
        return True;
    else:
        return False


def buildMeta():
    return [{"authors":["David Larrimore", "Robert Donovan"], "copyright": "Copyright 2015 MixFin LLC.", "version": "0.1"}]






########
# main #
########
if __name__ == "__main__":
    app.run(host='0.0.0.0')
