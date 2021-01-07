import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from flasgger import Swagger

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)
Swagger(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
This is Coffee Shop API GET method to fetch all drinks 
This is a public method and does not require any Authorization.
---
tags:
    - Coffee-Shop API
responses:
    Good Response:
    description: All Drinks with short description
    500:
    description: Something went wrong!
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    f_drinks = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': f_drinks
    }), 200

'''
This is Coffee Shop API GET method to fetch Drink Details
This method required Authentication and role based Authorization to be accessible.
---
tags:
    - Coffee-Shop API
responses:
    Good Response:
    description: All Drinks with long description
    500:
    description: Something went wrong!
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(payload):
    drinks = Drink.query.order_by(Drink.id).all()
    f_drinks = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': f_drinks
    }), 200

'''
This is Coffee Shop API POST method to create a new Drink
This method required Authentication and role based Authorization to be accessible.
---
tags:
    - Coffee-Shop API
parameters:
      - in: body
        title: title
        type: String
        required: true
        description: Title of the drink
      - in: body
        recipe: recipe
        type: String
        required: true
        description: List of recipes
responses:
    Good Response:
    description: Saves the drink and return the drink details
    500:
    description: Something went wrong!
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    new_title  = body.get('title')
    new_recipe = json.dumps(body.get('recipe'))
    
    try:
        drink = Drink(title=new_title, recipe=new_recipe)
        drink.insert()

    except BaseException:
        abort(400)

    return jsonify({'success': True, 'drinks': [drink.long()]})


'''
This is Coffee Shop API PATCH method to update an existing Drink
This method required Authentication and role based Authorization to be accessible.
---
tags:
    - Coffee-Shop API
parameters:
      - in: path
        id: id
        type: integer
        required: true
        description: ID of the drink
      - in: body
        title: title
        type: String
        required: true
        description: Title of the drink
      - in: body
        recipe: recipe
        type: String
        required: true
        description: List of recipes
responses:
    Good Response:
    description: Updates the drink and return the drink details
    500:
    description: Something went wrong!
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)

    new_title  = body.get('title', None)
    new_recipe = json.dumps(body.get('recipe', None))
    
    try:
        if new_title:
            drink.title = new_title
        if new_recipe:
            drink.recipe = new_recipe
        drink.update()

    except BaseException:
        abort(400)

    return jsonify({'success': True, 'drinks': [drink.long()]}), 200

'''
This is Coffee Shop API DELETE method to delete an existing Drink
This method required Authentication and role based Authorization to be accessible.
---
tags:
    - Coffee-Shop API
parameters:
      - in: path
        id: id
        type: integer
        required: true
        description: ID of the drink
responses:
    Good Response:
    description: Deletes the drink and return the id of the deleted drink
    404:
    description: If the drink to be deleted is not found
    500:
    description: Something went wrong!
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)

    try:
        drink.delete()

    except BaseException:
        abort(400)

    return jsonify({'success': True, 'delete': id}), 200


## Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unauthorized'
    }), 401


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'Internal Server Error'
    }), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request'
    }), 400


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'Method Not Allowed'
    }), 405