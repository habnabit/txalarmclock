from dateutil import rrule
import collections
import subprocess
import datetime
import yaml
import os

actions = {}
def action(kind):
    def deco(f):
        actions[kind] = f
        return f
    return deco

@action("command")
def action_command(args):
    subprocess.check_call(args)

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
    def __init__(self, collection, obj):
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

class AlarmCollection(object):
    def __init__(self, alarms, dtstart):
        self.alarm_source = alarms
        self.dtstart = dtstart
        self.alarms = {}
        for k in alarms:
            self[k]

    def __getitem__(self, alarm):
        ret = self.alarms.get(alarm)
        if ret is None:
            ret = self.alarms[alarm] = Alarm(self, self.alarm_source[alarm])
        return ret

def parse(path, dtstart=None):
    parsed = yaml.safe_load(path)['alarms']
    return AlarmCollection(parsed, dtstart)

def main(alarms, timepiece, alarm):
    try:
        dtstart = os.path.getmtime(timepiece)
    except OSError:
        dtstart = None
    else:
        dtstart = datetime.datetime.fromtimestamp(dtstart)
    collection = parse(open(alarms), dtstart)
    os.utime(timepiece, None)
    next_action = next(iter(collection[alarm]))
    if next_action.when > datetime.datetime.now():
        return
    action_type = next_action.what.pop('type')
    actions[action_type](**next_action.what)

if __name__ == '__main__':
    import sys
    main(*sys.argv[1:])

