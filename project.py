from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from flask import session as login_session
import random
import string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    return output


# JSON APIs to view Restaurant Information
@app.route('/catalog.json')
def catalogJSON():
    items = session.query(Item).all()
    return jsonify(items=[r.serialize for r in items])


# Show catalog
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(asc(Item.name))
    if 'username' in login_session: 
        return render_template('catalog.html', categories=categories, items=items, STATE=state, loggedin="true")
    else:
        return render_template('catalog.html', categories=categories, items=items, STATE=state, loggedin="false")
    

# Create a new item
@app.route('/catalog/newitem', methods=['GET', 'POST'])    
def newItem():
    if 'username' not in login_session: 
        return redirect('/')
    
    allcategories = session.query(Category).order_by(asc(Category.name))
    
    if request.method == 'POST':
        category = session.query(Category).filter_by(name=request.form['category']).one()
        newItem = Item(name=request.form['name'], description=request.form[
                           'description'], category_id = category.id)
        session.add(newItem)
        session.commit()

        return redirect(url_for('showCatalog'))
    else:
        return render_template('newitem.html', allcategories=allcategories)
                        
                        
# Show items for a category
@app.route('/catalog/<string:category_escaped>/items/', methods=['GET', 'POST'])
def showCategory(category_escaped):
    allcategories = session.query(Category).order_by(asc(Category.name))
    category_name = category_escaped.replace("%20", " ")
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    
    return render_template('showCategory.html', categories=allcategories, category=category, items=items)

    
#Show item
@app.route('/catalog/<string:category_name>/<string:item_escaped>/', methods=['GET', 'POST'])
def showItem(category_name, item_escaped):
    item_name = item_escaped.replace("%20", " ")
    item = session.query(Item).filter_by(name=item_name).one()
    
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form['name'])
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        if 'username' in login_session: 
            
            return render_template('showItem.html', item=item, editFeatures="true")
        else:
            return render_template('showItem.html', item=item, editFeatures="false")

# Edit item
@app.route('/catalog/<string:item_escaped>/edit/', methods=['GET', 'POST'])
def editItem(item_escaped):
    if 'username' not in login_session: 
        return redirect('/')
    
    item_name = item_escaped.replace("%20", " ")
    editedItem = session.query(Item).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(id=editedItem.category_id).one()
    allcategories = session.query(Category).order_by(asc(Category.name))
    
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            category = session.query(Category).filter_by(name=request.form['category']).one()
            editedItem.category_id = category.id

        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        if 'username' in login_session: 
            return render_template('edititem.html', item=editedItem, category=category, allcategories=allcategories, editFeatures="true")
    
        else:
            return render_template('edititem.html', item=editedItem, category=category, allcategories=allcategories, editFeatures="false")


# Delete item
@app.route('/catalog/<string:item_escaped>/delete/', methods=['GET', 'POST'])
def deleteItem(item_escaped):
    if 'username' not in login_session: 
        return redirect('/')

    item_name = item_escaped.replace("%20", " ")
    item = session.query(Item).filter_by(name=item_name).one()

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('/catalog'))
    else:
        return render_template('deleteitem.html', item=item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)