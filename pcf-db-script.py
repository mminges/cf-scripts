import boto.rds
import boto.ec2
import datetime
import time
import argparse
import collections
from datetime import date, timedelta
from boto.exception import BotoServerError

def getSnapshots():
    "Lists all snapshots that were created using this script"

    snapshotList = []
    for snapshot in dbSnapshots:
        if snapshot.id.startswith(dbSnapshotBase) and snapshot.status == 'available':
            snapshotList.append(snapshot.id)
    snapshotList.sort(reverse=True)

    return snapshotList

def printSnapshots():
    snapshots = getSnapshots()
    if snapshots is None:
        print("Couldn't find any snapshots for instance " + dbInstanceName + ", note name must start with " + dbSnapshotBase)
        return
    for name in snapshots:
        print(name)

    return snapshots

def getStatusOfDatabase():
    "Gets the status of the specified available database"

    if dbInstances is not None:
        print("[%s] has status of [%s] " % (dbInstances[0], dbInstances[0].status))
    else:
        print("There is currently no available RDS database running. Please check the AWS Console if this is a problem!")

    return None

def removeDatabase():
    snapshotName = dbSnapshotBase + '-' + today.strftime('%Y%m%d-%H%M')
    print("Backing database up to snapshot name: %s " % snapshotName)

    deletedInstance = dbInstances[0].stop(skip_final_snapshot=False, final_snapshot_id=snapshotName)

    iterationCount = 0
    iterationMax = 40
    timerBreak = 30

    print("Deleting database..." + dbInstanceName)
    while (iterationCount < iterationMax):
        time.sleep(timerBreak)
        iterationCount += 1
        try:
            deletedInstance.update(validate=True)
            deletedStatus = deletedInstance.status
            print("deleted db status: " + deletedStatus)
        except ValueError:
            print("Could no longer access database status, assuming it has been deleted")
            break
        except BotoServerError as e:
            if e.status == "404":
                print("Could no longer access database status, assuming it has been deleted")
            else:
                print('Unknown botoServerError, giving up')
                print('status=', e.status)
                print('reason=', e.reason)
                print('body=', e.body)
                print('request_id=', e.request_id)
                print('error_code=', e.error_code)
                print('error_message=', e.error_message)
            break

    return None

def restoreDatabase():

    snapshots = getSnapshots()
    if snapshots is None:
        print("There are no snapshots to restore from, note name must start with " + dbSnapshotBase)
        return

    dbSnapshotName = snapshots[0]
    print("Will restore database from the most recent available snapshot: [%s] " % dbSnapshotName)

    dbClassName = 'db.m3.large'
    secGroupId = 'sg-86020ce2'
    secGroupName = 'tc-mysql'
    restoredInstance = conn.restore_dbinstance_from_dbsnapshot(dbSnapshotName, dbInstanceName, dbClassName, multi_az=True, db_subnet_group_name='tc-pcf-rdsgroup')

    iterationCount = 0
    iterationMax = 60
    timerBreak = 30
    restoredStatus = 'restoring'

    while ((iterationCount < iterationMax) and (restoredStatus != 'available')):
       time.sleep(timerBreak)
       iterationCount += 1
       try:
          restoredInstance.update(validate=True)
          restoredStatus = restoredInstance.status
          print ("restored db status: " + restoredStatus)
       except ValueError:
          print("could no longer access database status, exiting")

    if(iterationCount < iterationMax):
        print("\nWaited %s seconds to remove old instance" % (iterationCount*timerBreak))
    else:
        print("\nTimed out waiting for old instance to be removed, something probably went wrong, waited for maximum of %s seconds" % (iterationMax*timerBreak))
        return

    conn.modify_dbinstance(dbInstanceName, vpc_security_groups=[secGroupId]);

    return None

# def overrideLatestSnapshot():
#     "Will implement an override to use a specific snapshot instead of the most recently available snapshot"
#
#     snapshots = getSnapshots()
#     if snapshots is None:
#         print("There are no snapshots to restore from, note name must start with " + dbSnapshotBase)
#         return


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--remove', action='store_true', help='takes a snapshot and removes the specified database instance')
group.add_argument('--restore', action='store_true', help='restore the database from the latest snaphot taken')
group.add_argument('--status', action='store_true', help='status for the specified database snapshot')
group.add_argument('--snapshots', action='store_true', help='lists all available snapshots for the specified database instance')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1', choices=['us-east-1','us-west-2'])
parser.add_argument('-o','--override', help='allows user to specify snapshot to use for a database restore')

args = parser.parse_args()

dbInstanceName = 'tc-pcf-bosh'
dbSnapshotBase = 'tc-pcf-bosh-snapshot'
today = datetime.datetime.now()

print("Connecting to AWS Region [%s] \n" % args.region)
# Create a connection to the service
conn = boto.rds.connect_to_region(args.region)
dbInstances = conn.get_all_dbinstances()
dbSnapshots = conn.get_all_dbsnapshots(instance_id=dbInstanceName)

if args.remove:
    print("\ncreating a final snapshot and removing specified database ... \n")
    removeDatabase()
    print("\nYour AWS RDS database has been successfully removed!")

elif args.restore:
    print("\nrestoring database ... \n")
    restoreDatabase()
    print("\nYour AWS RDS database is now restored!")

elif args.override:
    print("Below is the available list of snapshots to use for a database restore\n")

    if args.override not in printSnapshots():
        print("\nThe snapshot entered for the override is not an available option! Check the above list for available snapshots to use!")
    else:
        print("\nThe snapshot that will be used for the override: [%s] " % args.override)
    # overrideLatestSnapshot()

elif args.snapshots:
    printSnapshots()

else:
    getStatusOfDatabase()
