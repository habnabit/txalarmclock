import alarmparse

import subprocess
import datetime
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

@action("iTunes")
def action_iTunes(**args):
    subprocess.check_call([
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'iTunes-alarm.applescript'),
        str(args['min-volume']),
        str(args['max-volume']),
        str(alarmparse.parse_timedelta(args['volume-interval'])),
        str(alarmparse.parse_timedelta(args['snooze'])),
        str(args['snooze-restore-volume']),
        args['playlist']])

def main(alarms, timepiece, alarm):
    fromtimestamp = datetime.datetime.fromtimestamp
    dtstart = fromtimestamp(os.path.getmtime(timepiece))
    os.utime(timepiece, None)
    now = fromtimestamp(os.path.getmtime(timepiece))
    collection = alarmparse.parse(open(alarms), dtstart)

    next_action = collection[alarm].first_between(dtstart, now)
    if next_action is None or not dtstart < next_action.when <= now:
        return
    action_type = next_action.what.pop('type')
    actions[action_type](**next_action.what)

if __name__ == '__main__':
    import sys
    main(*sys.argv[1:])

