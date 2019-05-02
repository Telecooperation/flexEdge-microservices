from utils.config import config

class ApiResponse:
    offset = ''
    msg = ''
    body = {}

    @staticmethod
    def get(base_code):
        response = {'header': {}}
        response['header']['code'] = ApiResponse.get_code(base_code)
        response['header']['message'] = ApiResponse.msg
        response['body'] = ApiResponse.body
        return response

    @staticmethod
    def get_code(base_code):
        if ApiResponse.is_passed():
            return ApiResponse.offset
        else:
            return ApiResponse.offset + base_code

    @staticmethod
    def set_body(offset , msg , body):
        ApiResponse.set_msg(offset, msg)
        ApiResponse.body = body

    @staticmethod
    def set_msg(offset , msg):
        ApiResponse.offset = offset
        ApiResponse.msg = msg
        # android application requires "body" to be object but openwhisk converts empty object to empty array and
        # android application is unable to parse the json
        ApiResponse.body = {
            "message": msg
        }

    @staticmethod
    def is_passed():
        return ApiResponse.offset == config["api"]["base_code_success"]