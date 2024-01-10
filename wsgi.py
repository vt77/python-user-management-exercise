import os
import sys
import logging
import uuid
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    abort,
    make_response,
)

import settings

from db import ObjectManager, DatabaseManager
from model.user import User
from model.audit import Audit
from db.sqlite import SqLiteBackend
from service import request_context

logging.basicConfig(
    format="[API]%(asctime)-15s %(process)d %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)
logger = logging.getLogger()

app = Flask("users-backend")

def get_next_request_id():
    return uuid.uuid4().hex

backend = SqLiteBackend('users-audit.db')
DatabaseManager.register_backend(backend)

@app.route("/api")
def main():
    return "<h1>Users managment service</h1>"

@app.route("/api")
def api():
    return render_template("api.html", devices=[request.hostname])


@app.route("/api/v1/users/",methods=['GET'])
def api_users_get():
    # Get all users except deleted
    request_id = get_next_request_id()
    logger.debug("[%s]Get users list",request_id)
    with request_context(request_id) as conn:
        ret = ObjectManager.get_many(User,{'deleted':0})
        conn.create_response(ret)
    return jsonify(conn.response)

@app.route("/api/v1/users/",methods=['POST'])
def api_user_create():
    request_id = get_next_request_id()
    logger.debug("[%s]User create",request_id)
    with request_context(request_id) as conn:
        data = request.json
        if not data or not isinstance(data,dict):
            abort(400)
        user = User.create(**data)
        user.save()
        conn.create_response(user)
    return jsonify(conn.response)


@app.route("/api/v1/users/<username>",methods=['GET'])
def api_user_get(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User get : %s",request_id,username)
    with request_context(request_id) as conn:
        ret = ObjectManager.get_one(User,{'deleted':0,'username':username})
        conn.create_response(ret)
    return jsonify(conn.response)

@app.route("/api/v1/users/<username>",methods=['PUT'])
def api_users_update(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User update : %s",request_id,username)
    with request_context(request_id) as conn:
        user = ObjectManager.get_one(User,{'deleted':0,'username':username})
        data = request.json
        for k,v in data.items():
            user.update(k,v)
        user.save()
        conn.create_response(user)
    return jsonify(conn.response)

@app.route("/api/v1/users/<username>",methods=['DELETE'])
def api_users_delete(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User delete : %s",request_id,username)
    with request_context(request_id) as conn:
        user = ObjectManager.get_one(User,{'deleted':0,'username':username})
        user.delete()
        conn.create_response(user)
    return jsonify(conn.response)

@app.route("/api/v1/audits/",methods=['POST'])
def api_audit_create():
    request_id = get_next_request_id()
    logger.debug("[%s]Audit create",request_id)
    with request_context(request_id) as conn:
        data = request.json
        audit = Audit.create(**data)
        audit.save()
        conn.create_response(audit)
    return jsonify(conn.response)

@app.route("/api/v1/audits/",methods=['GET'])
def api_audit_get():
    request_id = get_next_request_id()
    logger.debug("[%s]Audit list",request_id)
    with request_context(request_id) as conn:
        ret = ObjectManager.get_many(Audit,order={'datetime'})
        conn.create_response(ret)
    return jsonify(conn.response)

@app.route("/api/v1/audits/rotate",methods=['GET'])
def api_audit_rotate():
    """ Special API endpoint to rotate audit records. Called from cronjob """
    if not hasattr(backend,'rotate'):
        return "Rotate not supported by backend"
    backend.rotate('audit',max_size=100)
    return "OK"


if __name__ == "__main__":
    app.run(debug=True)


