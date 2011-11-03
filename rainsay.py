import subprocess
import itertools
import posixpath
import operator
import urlparse
import urllib
import json

API_KEY = "a99fb0ae417940db"
LOCATION = "98121"

def main(args):
    url = urlparse.urljoin(
        "http://api.wunderground.com/api/",
        posixpath.join(API_KEY, "hourly", "q", LOCATION + ".json"))
    j = json.load(urllib.urlopen(url))
    results = []
    for pop, forecasts in itertools.groupby(j['hourly_forecast'][:18], operator.itemgetter('pop')):
        forecasts = list(forecasts)
        first, last = forecasts[0]['FCTTIME'], forecasts[-1]['FCTTIME']
        results.append(
            "{0}% chance between {1[hour]} hundred and {2[hour]} hundred.".format(pop, first, last))

    result = " ".join(results)
    subprocess.check_call(['say', result])

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
