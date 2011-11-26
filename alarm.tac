# -*- python -*-

import alarmserver, alarmparse

from twisted.application import service, internet
from twisted.python import log
from twisted.internet import defer, reactor

import signal

actions = {}
def action(kind):
    def deco(f):
        actions[kind] = f
        return f
    return deco

@action("command")
def action_command(args):
    check_call(args).addErrback(log.err)

@action("iTunes")
def action_iTunes(**args):
    check_call([
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'iTunes-alarm.applescript'),
        str(args['min-volume']),
        str(args['max-volume']),
        str(alarmparse.parse_timedelta(args['volume-interval'])),
        str(alarmparse.parse_timedelta(args['snooze'])),
        str(args['snooze-restore-volume']),
        args['playlist']]
    ).addErrback(log.err)

CONFIG = 'alarm.yaml'

application = service.Application("alarmserver")
container = alarmserver.AlarmCollectionContainer(
    alarmparse.parse(open(CONFIG)), application)

def alarmDispatch(alarm, action):
    action = action.what.copy()
    action_type = action.pop('type')
    actions[action_type](**action)
container.attachEnabled(alarmDispatch)

def reloadAlarms(sig, frame):
    log.msg('SIGHUP; reloading config')
    def _actuallyReloadAlarms():
        container.detachAll()
        container.replaceCollection(alarmparse.parse(open(CONFIG)))
        container.attachEnabled(alarmDispatch)
    reactor.callLater(0, _actuallyReloadAlarms)
signal.signal(signal.SIGHUP, reloadAlarms)

site = alarmserver.buildSite()
internet.TCPServer(8089, site).setServiceParent(application)
