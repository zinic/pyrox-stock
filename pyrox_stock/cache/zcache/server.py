import zmq
import msgpack
import weakref

from pyrox.log import get_logger
from pyrox_stock.cache import CacheProvider
from pyrox_stock.cache.zcache.config import load_zcache_config


_LOG = get_logger(__name__)


def create_server(conf_location=None):
    cfg = load_zcache_config(conf_location)
    return ZCacheServer(cfg)


def _strval(string):
    strval = 0
    for c in string:
        strval += ord(c)
    return _strval

class WeakRefCache(CacheProvider):

    def __init__(self):
        self._cache = dict()

    def get(self, key):
        item = self._cache.get(_strval(key))
        return item.value if item else None

    def put(self, key, value):
        self._cache[_strval(key)] = CacheItem(value)

    def delete(self, key):
        return self._cache.pop(_strval(key), None) != None


class CacheItem(object):

    def __init__(self, value):
        self.value = value


class ZCacheServer(object):

    def __init__(self, cfg):
        self._cfg = cfg

    def start(self):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._cache = WeakRefCache()

        #self._socket.bind('tcp://127.0.0.1:{}'.format(
        #    self._cfg.network.cache_port))

        self._socket.bind('ipc:///tmp/zcache.fifo')

        while True:
            try:
                bmsg = self._socket.recv()
                msg = msgpack.unpackb(bmsg)

                self._handle_msg(msg)
            except Exception as ex:
                _LOG.exception(ex)
                break

    def _handle_msg(self, msg):
        op = msg['operation']

        reply = dict()
        reply['status'] = 'error'

        if op == 'get':
            cached_obj = self._cache.get(msg['key'])
            _LOG.debug('Getting {}'.format(msg['key']))

            if cached_obj:
                reply['status'] = 'found'
                reply['value'] = cached_obj
            else:
                reply['value'] = None
        elif op == 'put':
            _LOG.debug('Putting {}:{}'.format(msg['key'], msg['value']))
            self._cache.put(msg['key'], msg['value'])
            reply['status'] = 'ok'
        elif op == 'del':
            _LOG.debug('Deleting {}'.format(msg['key']))
            if self._cache.delete(msg['key']):
                reply['status'] = 'deleted'
            else:
                reply['status'] = 'not_found'

        self._socket.send(msgpack.packb(reply))
