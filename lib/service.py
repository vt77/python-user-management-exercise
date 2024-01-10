import logging
from contextlib import contextmanager
from db import BackendError
from model import ValidateException, ModelException

logger = logging.getLogger()

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


class RequestContext():
    def __init__(self,request_id):
        self._response = None
        self._request_id = request_id

    def create_response(self,resp):
        self._response = ApiResponse(self._request_id,resp)

    def error(self,msg,err_type:str='general'):
        self._response = ApiError(self._request_id,msg,err_type)

    @property
    def response(self):
        return dict(self._response)

@contextmanager
def request_context(request_id):
    _request_context = RequestContext(request_id)
    try:
        yield _request_context
    except ValidateException as ex:
        _request_context.error(str(ex),'validation')
    except ModelException as ex:
        _request_context.error(str(ex),'model')
    except Exception as ex:
        logger.exception(str(ex))
        _request_context.error(str(ex))