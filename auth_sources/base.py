class AuthSource:
    def get_auth_info(self, item_id):
        raise NotImplementedError

    def unlock(self, password):
        pass

    def __enter__(self):
        return self

    def lock(self):
        pass

    def __exit__(self, *args, **kwargs):
        self.lock()

class AuthError(Exception):
    def __init__(self, message, info):
        self.message = message
        self.info = info
