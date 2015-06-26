import boto.rds
import boto.rds2
import boto.ec2
import datetime
import time
import argparse
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

    return None

def deleteOldSnapshots():
    "Deletes snapshots from the end of the list of snapshots if greater than 10."
    allSnapshots = getSnapshots()
    if (len(allSnapshots) > 5):
        print("The last snapshot in the list is %s and will be deleted first." % (allSnapshots[-1]))
    else:
        print("False")

    print("not finished yet ...")


def getStatusOfDatabase():
    "Gets the status of the specified available database"

    if dbInstances is not None:
        db = dbInstances[0]
        print("\n%s database has status of [%s] " % (db.id, db.status))
        print("\nInstance Class: %s \nAvailability Zone: %s \nVPC Security Groups: %s \nCreation Time: %s " % (db.instance_class, db.availability_zone, db.vpc_security_groups, db.create_time))

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

    print("\nDatabase instances that are active are: %s " % (dbInstances))

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

    conn.modify_dbinstance(dbInstanceName, vpc_security_groups=[secGroupId]);

    return None

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--remove', action='store_true', help='takes a snapshot and removes the specified database instance')
group.add_argument('--restore', action='store_true', help='restore the database from the latest snaphot taken')
group.add_argument('--status', action='store_true', help='status for the specified database snapshot')
group.add_argument('--get_snap', action='store_true', help='lists all available snapshots for the specified database instance')
group.add_argument('--del_snap', action='store_true', help='deletes snapshots at end of list if list greater than 10')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1', choices=['us-east-1','us-west-2'])
parser.add_argument('-o','--override', help='Specify a snapshot to use for a database restore')

args = parser.parse_args()

dbInstanceName = 'tc-pcf-bosh'
dbSnapshotBase = 'tc-pcf-bosh-snapshot'
today = datetime.datetime.now()

print("Connecting to AWS Region [%s] " % args.region)
# Create a connection to the service
conn = boto.rds.connect_to_region(args.region)
conn2 = boto.rds2.connect_to_region(args.region)
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
    print("not finished yet ...")

elif args.get_snap:
    printSnapshots()

elif args.del_snap:
    deleteOldSnapshots()

else:
    getStatusOfDatabase()
