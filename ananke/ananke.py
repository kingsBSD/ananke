
import sys

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPullConnection

from app import app
from ipgetter import get_ip
import settings
from socket_server import  NotificationServerFactory, NotificationProtocol
   
if __name__ == '__main__':

    ip = get_ip()

    if not ip:
        ip = '127.0.0.1'

    zf = ZmqFactory()
    endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")

    pull = ZmqPullConnection(zf, endpoint)

    log.startLogging(sys.stdout)

    ws_factory = NotificationServerFactory(pull,host=ip)
    ws_factory.protocol = NotificationProtocol

    reactor.listenTCP(settings.WEBSOCKET_PORT, ws_factory)
    reactor.listenTCP(settings.APP_PORT, Site(app.resource()))
    reactor.run()