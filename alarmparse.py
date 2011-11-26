from dateutil import rrule
import collections
import datetime
import yaml

def parse_timedelta(obj):
    return datetime.timedelta(**obj).total_seconds()

Action = collections.namedtuple('Action', 'what when')

def rrule_const(s):
    return getattr(rrule, str(s).upper())

def parse_rrule(obj, base=None):
    ret = {} if base is None else base.copy()
    for k, v in obj.iteritems():
        # This is okay because we're restricted to a limited set of input
        # types. Shut up.
        if isinstance(v, basestring):
            v = rrule_const(v)
        elif isinstance(v, list):
            v = [rrule_const(x) if isinstance(x, basestring) else x for x in v]
        ret[k] = v
    return ret

class Alarm(object):
    def __init__(self, name, collection, obj):
        self.name = name
        self.superseders = []
        self.cancelers = []
        if 'supersedes' in obj:
            parent = collection[obj['supersedes']]
            parent.superseders.append(self)
        elif 'cancels' in obj:
            parent = collection[obj['cancels']]
            parent.cancelers.append(self)
        else:
            parent = None
        rrule_base = None if parent is None else parent.rrule_source
        self.rrule_source = parse_rrule(obj['rrule'], rrule_base)
        self.rrule_source.setdefault('dtstart', collection.dtstart)
        self.rrule = rrule.rrule(**self.rrule_source)
        self.action = obj.get('action')
        self.replacements = obj.get('replace')

    def is_canceled_on(self, dt):
        return any(c.matches(dt) for c in self.cancelers)

    def matches(self, dt):
        if self.is_canceled_on(dt):
            return False
        return dt in self.rrule

    def transform(self, action):
        if not self.matches(action.when):
            return action
        if self.replacements:
            action = action._replace(when=action.when.replace(**self.replacements))
        if self.action:
            action = action._replace(what=self.action)
        return action

    def __iter__(self):
        for dt in self.rrule:
            if self.is_canceled_on(dt):
                continue
            action = Action(what=self.action, when=dt)
            for s in self.superseders:
                action = s.transform(action)
            yield action

    def first_between(self, start, end):
        for action in self:
            if action.when > end:
                return None
            if action.when < start:
                continue
            return action

class AlarmCollection(object):
    def __init__(self, content, dtstart):
        self.alarm_source = content['alarms']
        self.enabled = set(content['enabled'])
        self.dtstart = dtstart
        self.alarms = {}
        for k in self.alarm_source:
            self[k]

    def __getitem__(self, alarm):
        ret = self.alarms.get(alarm)
        if ret is None:
            ret = self.alarms[alarm] = Alarm(
                alarm, self, self.alarm_source[alarm])
        return ret

def parse(path, dtstart=None):
    content = yaml.safe_load(path)
    return AlarmCollection(content, dtstart)
