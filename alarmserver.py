from twisted.web import static, resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.python import log
from twisted.internet import reactor, defer
from twisted.internet.utils import getProcessValue
from twisted.application import service

import datetime

class CalledProcessError(Exception):
    pass

@defer.inlineCallbacks
def check_call(args):
    v = yield getProcessValue(args[0], args[1:], env=None)
    if v:
        raise CalledProcessError(args, v)

class AlarmService(service.Service):
    def __init__(self, alarm, callable):
        self.alarm = alarm
        self.callable = callable
        self._alarmIterator = iter(self.alarm)
        self._task = None

    def _reschedule(self):
        now = datetime.datetime.now()
        for act in self._alarmIterator:
            if act.when > now:
                break
        else:
            log.msg('%r alarm has no future occurrences' % (self.alarm.name,))
            self._task = None
            return
        delta = act.when - now
        log.msg(
            'scheduling %r alarm for %s (%s)' % (
                self.alarm.name, act.when, delta))
        self._task = reactor.callLater(delta.total_seconds(), self._alarm, act)

    def _alarm(self, action):
        self.callable(self.alarm, action)
        self._reschedule()

    def startService(self):
        service.Service.startService(self)
        self._reschedule()

    def stopService(self):
        if self.running and self._task is not None:
            self._task.cancel()
            self._task = None
        service.Service.stopService(self)

    def replaceAlarm(self, alarm):
        self.alarm = alarm
        self._alarmIterator = iter(self.alarm)
        if self.running:
            self._task.cancel()
            self._reschedule()

class AlarmCollectionContainer(object):
    def __init__(self, collection, serviceParent):
        self.collection = collection
        self.serviceParent = serviceParent
        self.alarmServices = {}

    def attachAlarm(self, alarm, callable):
        service = self.alarmServices.get(alarm)
        if service is not None:
            raise ValueError('alarm %r already attached' % (alarm,))
        service = self.alarmServices[alarm] = (
            AlarmService(self.collection[alarm], callable))
        service.setServiceParent(self.serviceParent)

    def attachEnabled(self, callable):
        for alarm in self.collection.enabled:
            self.attachAlarm(alarm, callable)

    def detachAlarm(self, alarm):
        service = self.alarmServices.pop(alarm, None)
        if service is None:
            raise ValueError('alarm %r not attached' % (alarm,))
        service.disownServiceParent()

    def detachAll(self):
        for alarm in list(self.alarmServices):
            self.detachAlarm(alarm)

    def replaceCollection(self, collection):
        self.collection = collection
        for alarm, service in self.alarmServices.iteritems():
            service.replaceAlarm(self.collection[alarm])

def deferredPage(func):
    func = defer.inlineCallbacks(func)
    def wrap(self, request):
        (func(self, request)
            .addErrback(request.processingFailed)
            .addErrback(lambda f: None))
        return NOT_DONE_YET
    return wrap

class SnoozeActionResource(resource.Resource):
    @deferredPage
    def render_POST(self, request):
        yield check_call(['osascript', '-e', 'tell app "iTunes" to pause'])
        request.redirect('/snooze')
        request.finish()

def buildSite():
    root = resource.Resource()
    root.putChild('static', static.File('static'))
    snooze = static.File('static/snooze.html')
    root.putChild('snooze', snooze)
    snooze.putChild('do', SnoozeActionResource())
    return Site(root)
