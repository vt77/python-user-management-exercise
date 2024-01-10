import os
import sys
import logging
import uuid

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

from db import ObjectManager, DatabaseManager, BackendError
from model.user import User
from model.audit import Audit
from model import ValidateException, ModelException
from db.sqlite import SqLiteBackend

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


class ApiResponse:
    """Convert general responce to API  format serilizable json
    """
    def __init__(self,request_id, object_list):
        self.request_id = request_id
        self.object_list = object_list

    def __iter__(self):
        yield "request_id", self.request_id
        yield "status", "ok"
        yield "payload", self.payload

    @property
    def payload(self):
        if isinstance(self.object_list,list):
            return {'items':[dict(e) for e in self.object_list]}
        return {'item':dict(self.object_list)}

class ApiError:
    """ General error format """
    def __init__(self,request_id, error_message, error_type='general'):
        self.request_id = request_id
        self.error_message = error_message
        self.error_type = error_type
        logger.error("[%s][%s]%s",self.request_id,self.error_type,self.error_message)

    def __iter__(self):
        yield "request_id", self.request_id
        yield "status", "error"
        yield "error_type", self.error_type
        yield "message", self.error_message

class ApiValidationError(ApiError):
    def __init__(self,request_id, error_message):
        super(ApiValidationError, self).__init__(request_id, error_message,'validation')

class ApiModelError(ApiError):
    def __init__(self,request_id, error_message):
        super(ApiModelError, self).__init__(request_id, error_message,'model')

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
    try:
        ret = ObjectManager.get_many(User,{'deleted':0})
        response = ApiResponse(request_id,ret)
    except Exception as ex:
        logger.exception(str(ex))
        response = ApiError(request_id,str(ex))
    return jsonify(dict(response))

@app.route("/api/v1/users/",methods=['POST'])
def api_user_create():
    request_id = get_next_request_id()
    logger.debug("[%s]User create",request_id)
    try:
        data = request.json
        user = User.create(**data)
        user.save()
        response = ApiResponse(request_id,[user])
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    except ValidateException as ex:
        response = ApiError(request_id,str(ex),'validation')
    except ModelException as ex:
        response = ApiError(request_id,str(ex),'model')
    return jsonify(dict(response))

@app.route("/api/v1/users/<username>",methods=['GET'])
def api_user_get(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User get : %s",request_id,username)
    try:
        ret = ObjectManager.get_one(User,{'deleted':0,'username':username})
        response = ApiResponse(request_id,ret)
    except BackendError as ex:
        response = ApiError(request_id,str(ex),'backend')
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    return jsonify(dict(response))


@app.route("/api/v1/users/<username>",methods=['PUT'])
def api_users_update(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User update : %s",request_id,username)
    try:
        user = ObjectManager.get_one(User,{'deleted':0,'username':username})
        data = request.json
        for k,v in data.items():
            user.update(k,v)
        user.save()
        response = ApiResponse(request_id, user)
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    except ValidateException as ex:
        response = ApiValidationError(request_id,str(ex))
    except ModelException as ex:
        response = ApiModelError(request_id,str(ex))
    return jsonify(dict(response))

@app.route("/api/v1/users/<username>",methods=['DELETE'])
def api_users_delete(username):
    request_id = get_next_request_id()
    logger.debug("[%s]User delete : %s",request_id,username)
    try:
        user = ObjectManager.get_one(User,{'deleted':0,'username':username})
        user.delete()
        response = ApiResponse(request_id,user)
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    except ValidateException as ex:
        response = ApiValidationError(request_id,str(ex))
    except ModelException as ex:
        response = ApiModelError(request_id,str(ex))
    return jsonify(dict(response))

@app.route("/api/v1/audit/<username>",methods=['PUT'])
def api_audit_user_create(username):
    request_id = get_next_request_id()
    logger.debug("[%s]Audit create : %s",request_id,username)
    try:
        data = request.json
        audit = Audit.create(**data)
        audit.save()
        response = ApiResponse(request_id,[audit])
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    except ValidateException as ex:
        response = ApiValidationError(request_id,str(ex))
    except ModelException as ex:
        response = ApiModelError(request_id,str(ex))
    return jsonify(dict(response))

@app.route("/api/v1/audit/<username>",methods=['GET'])
def api_audit_user_get(username):
    request_id = get_next_request_id()
    logger.debug("[%s]Audit list : %s",request_id,username)
    try:
        ret = ObjectManager.get_many(User,{'username':username},order={'created'})
        response = ApiResponse(request_id,ret)
    except Exception as ex:
        response = ApiError(request_id,str(ex))
    except ValidateException as ex:
        response = ApiValidationError(request_id,str(ex))
    except ModelException as ex:
        response = ApiModelError(request_id,str(ex))
    return jsonify(dict(response))



@app.route("/api/v1/audit/rotate",methods=['GET'])
def api_audit_rotate():
    """ Special API endpoint to rotate audit records. Called from cronjob """
    if not hasattr(backend,'rotate'):
        return "Rotate not supported by backend"
    backend.rotate(audit,max_size=100)
    return "OK"
