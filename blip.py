from urllib.request import urlopen
import json, datetime, argparse

#
# The basics of the JSON interface, wrapped for convenience
#

prefix = "https://power.labitat.dk/"

def getJson(suffix):
    req = urlopen(prefix+suffix)
    blob = req.read()
    return json.loads(blob.decode('utf-8'))

def getBlip():
    return getJson("blip")

def getLast():
    return getJson("last")

def getLastN(n):
    return getJson("last/" + str(int(n)))

def getSinceN(n):
    return getJson("since/" + str(int(n)))

def getHourlyBetween(fr, to):
    return getJson("hourly/" + str(int(fr)) + "/" + str(int(to)))


#
# The monstrous fetch-n-average.
#
# This dude keeps calling getSinceN until it has all the data you want,
# and averages as requested while processing it
#

# The comparators that return True every time it should stop gathering things
# for averaging
# If you add a comparator here, you can immediately use it with the "average"
# option
comparators = {
    'day': lambda x, y: y.day != x.day,
    'month': lambda x, y: y.month != x.month,
    'year': lambda x, y: y.year != x.year,
    'none': lambda x, y: True
}
def getBetween(first, last, avg_dur='none'):
    first, last = int(first), int(last)
    data, avg_data = [], []
    cur = first
    last_dt = None
    dt_timestamp = None

    comparator = comparators[avg_dur]
    while True:
        things = getHourlyBetween(cur, last)

        for thing in things:
            cur = thing[0]
            avg_data.append(thing[2])
            dt_timestamp = datetime.datetime.fromtimestamp(cur/1000)

            # Make a first timestamp if necessary
            if last_dt is None:
                last_dt = dt_timestamp

            # Check if the comparator thinks it's time to average
            if comparator(last_dt, dt_timestamp):
                last_dt = dt_timestamp
                stuff = sum(avg_data) / len(avg_data)
                data.append([dt_timestamp, stuff])
                avg_data = []

            # Did this set include all our things?
            if cur > last:
                break
 
        # ... Are we completely done?
        if cur > last:
            # If something is left to average
            if len(avg_data):
                stuff = sum(avg_data) / len(avg_data)
                data.append([dt_timestamp, stuff])
                avg_data = []
            break

        # Make sure that we don't get duplicate things back
        cur += 1


    return data

# This fella is used for converting the date string parameters
def mkdate(datestring):
    return datetime.datetime.strptime(datestring, '%Y-%m-%d')

parser = argparse.ArgumentParser(description='Fetch a dataset from blip')
parser.add_argument("start", type=mkdate)
parser.add_argument("end", type=mkdate)
parser.add_argument('-a', '--average', nargs='?', default='none')
args = parser.parse_args()

# We want these things in milli-seconds
start = args.start.timestamp()*1000
end = args.end.timestamp()*1000

# Get ALL the things!
allDemStuffs = getBetween(start, end, args.average)

# Format for gnuplot
for x in allDemStuffs:
    print(x[0].isoformat("_")+" "+str(x[1]))

