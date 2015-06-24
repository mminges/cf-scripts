import boto.rds
import datetime
import time
import argparse
from datetime import date, timedelta

def getStatusOfDatabase():
    return None

def removeDatabase():
    today = datetime.date.today()

    snapshotName = dbInstanceName + '-' + today.strftime('%Y%m%d')
    print("Before removing database, will create a snapshot under the followin name: \n%s " % snapshotName)

    prevSnapshotName = datetime.datetime.now() - datetime.timedelta(days=1)
    prevSnapshotName_str = prevSnapshotName.strftime('%Y%m%d')
    latestSnapshotName = dbInstanceName + '-' + prevSnapshotName_str
    print("\nThe latest snapshot taken is: \n%s " % latestSnapshotName)

    # print("Database instances that are active are: %s " % (dbInstances))

    # deletedInstance = dbInstances[0].stop(skip_final_snapshot = False, final_snapshot_id = snapshotName)
    #
    # iterationCount = 0
    # timerBreak = 30
    #
    # while (iterationCount < 40):
    #    time.sleep(timerBreak)
    #    print('.',end="",flush=True)
    #    try:
    #       deletedInstance.update(validate=True)
    #       print ("deletion status:  " + deletedInstance.status)
    #    except ValueError:
    #       print("could no longer access database status, assuming it has been deleted")

    return None

def restoreDatabase():
    return None

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--remove', action='store_true', help='takes a snapshot and removes the specified database instance')
group.add_argument('--restore', action='store_true', help='restore the database from the latest snaphot taken')
group.add_argument('--status', action='store_true', help='status for the specified database')
group.add_argument('--list_snap', action='store_true', help='lists all available snapshots for the specified database instance')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1')

args = parser.parse_args()

dbInstanceName = 'tc-pcf-bosh'

print("Connecting to AWS Region [%s]" % args.region)
# Create a connection to the service
conn = boto.rds.connect_to_region(args.region)
dbInstances = conn.get_all_dbinstances(dbInstanceName)
dbSnapshots = conn.get_all_dbsnapshots(instance_id=dbInstanceName)

if args.remove:
    print("\ncreating a final snapshot and removing specified database ... \n")
    removeDatabase()
    print("\nYour AWS RDS database has been successfully removed!")

elif args.restore:
    print("\nrestoring database ... \n")
    restoreDatabase()
    print("\nYour AWS RDS database is now restored!")

elif args.list_snap:
    print("\nListing all snapshots associated with [%s] ... " % (dbInstanceName))
    for i in dbSnapshots:
        print("\n%s " % (i))

else:
    getStatusOfDatabase()
