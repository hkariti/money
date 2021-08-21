import subprocess
import os
import json

from .base import AuthSource, AuthError

class BitWardenAuthSource(AuthSource):
    def __init__(self, path='/usr/local/bin:/usr/bin', cmd='bw'):
        self._cmd = cmd
        self.sessionkey = None
        self._environ_base = dict(PATH=path, HOME=os.environ['HOME'])

    def _run_bw(self, *args, environ={}):
        return subprocess.run((self._cmd,) + args, shell=False, stdin=subprocess.DEVNULL, capture_output=True, env={ **self._environ_base, **environ }, text=True)

    def get_auth_info(self, item_id):
        item = self.get_item(item_id)
        return dict(username=item['login']['username'], password=item['login']['password'])

    def unlock(self, password):
        if self.sessionkey is None:
            self.sessionkey = self.bw("unlock", "--passwordenv", "BW_PASS", "--raw", environ=dict(BW_PASS=password))
        return self
        
    def lock(self):
        self.bw("lock")
        self.sessionkey = None

    def bw(self, *args, session=None, environ={}):
        if session:
            args = args + ('--session', session)
        ret = self._run_bw(*args, environ=environ)
        if ret.returncode != 0:
            raise AuthError(f"bw exited with return code {ret.returncode}.\nStdout:\n{ret.stdout}\nStderr:\n{ret.stderr}", runinfo=ret)

        return ret.stdout

    def get_item(self, item_id):
        try:
            item = self.bw("get", "item", item_id, session=self.sessionkey)
            return json.loads(item)
        except AuthError as e:
            if e.runinfo.stderr == 'Not found.':
                return None 
            raise
