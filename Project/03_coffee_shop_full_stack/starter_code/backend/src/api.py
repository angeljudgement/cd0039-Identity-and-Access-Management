import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
    )
    return response

'''
@TODO_DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO_DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def retrieve_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()   
    except Exception:
        abort(500)

    if drinks is None:
        return jsonify(
        {
            "success": True,
            "drinks": [],
        }
    )
    else:
        return jsonify(
            {
                "success": True,
                "drinks": [drink.short() for drink in drinks],
            }
        )


'''
@TODO_DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def retrieve_detail_drinks(payload):
    try:
        drinks = Drink.query.order_by(Drink.id).all()   
    except Exception:
        abort(500)

    if drinks is None:
        return jsonify(
        {
            "success": True,
            "drinks": [],
        }
    )
    else:
        return jsonify(
            {
                "success": True,
                "drinks": [drink.long() for drink in drinks],
            }
        )


'''
@TODO_DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    body = request.get_json()
    # [
    #             {
    #                 "color": "blue",
    #                 "name": "water",
    #                 "parts": 1
    #             }
    #         ]
    if (body == None
        or 'title' not in body or body['title'] == ''
        or 'recipe' not in body or len(body['recipe']) < 1
        ):
        abort(400)
    try:
        drink = Drink(title=body['title'],
                        recipe=json.dumps(body['recipe']),
                        )
        db.session.add(drink)
        db.session.commit()
        return jsonify(
            {
                "success": True,
                "message": "recipe added.",
                "drink_id": drink.id,
            }
        )
    except Exception as e:
        db.session.rollback()
        abort(500)
'''
@TODO_DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(payload, id):
    body = request.get_json()
    # [
    #             {
    #                 "color": "blue",
    #                 "name": "water",
    #                 "parts": 1
    #             }
    #         ]
    if id is None:
        abort(404)

    if (body == None
        or 'title' not in body or body['title'] == ''
        or 'recipe' not in body or len(body['recipe']) < 1
        ):
        abort(400)
    try:
        drink = Drink.query.get(id)
        if drink is None:
            abort(404)

        drink.title = body['title']
        drink.recipe = json.dumps(body['recipe'])

        db.session.commit()
        return jsonify(
            {
                "success": True,
                "message": "recipe updated",
                "drinks": [drink.long()]
            }
        )
    except Exception as e:
        db.session.rollback()
        # abort(500)
        return e

'''
@TODO_DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        drinkToDelete = Drink.query.get(id)
    except Exception as e:
        return 'Error at retrieve question to delete: '+e, 500
    if drinkToDelete is not None:
        db.session.delete(drinkToDelete)
        db.session.commit()
        return jsonify({
            'success': True,
            'drink_id': id
        })
    else:
        db.session.rollback()
        abort(404)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO_DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )
'''
@TODO_DONE implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(403)
def forbidden(error):
    return (
        jsonify({"success": False, "error": 403, "message": "Forbidden"}),
        403,
    )

@app.errorhandler(401)
def unauthorized(error):
    return (
        jsonify({"success": False, "error": 401, "message": "Unauthorized"}),
        401,
    )

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(500)
def internal_server(error):
    return (
        jsonify({"success": False, "error": 500, "message": "internal server"}),
        500,
    )

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400, "message": "bad request"}), 400