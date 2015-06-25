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

    print("\nListing all snapshots associated with [%s] ... " % (dbInstanceName))
    snapshotList = []
    for snapshot in dbSnapshots:
        if snapshot.id.startswith('tc-pcf-bosh-snapshot') and snapshot.status == 'available':
            snapshotList.append(snapshot.id)
    snapshotList.sort(reverse=True)
    for name in snapshotList:
        print("%s " % (name))

    return snapshotList;

def getStatusOfDatabase():
    if dbInstances is not None:
        print("This database has status of %s " % (dbInstances.status))

    else:
        print("There is currently no available RDS database running. Please check the AWS Console if this is a problem!")
    return None;


def removeDatabase():
    snapshotName = dbSnapshotBase + '-' + today.strftime('%Y%m%d-%H%M')
    print("Backing database up to snapshot name: \n%s " % snapshotName)

    deletedInstance = dbInstances[0].stop(skip_final_snapshot=False, final_snapshot_id=snapshotName)

    iterationCount = 0
    timerBreak = 30

    print("Snapshot created...\nDeleting database..." + dbInstanceName)
    while (iterationCount < 40):
        time.sleep(timerBreak)
        print('.', end="", flush=True)
        try:
            deletedInstance.update(validate=True)
        except ValueError:
            print("could no longer access database status, assuming it has been deleted")
        except BotoServerError as e:
            print('botoServerError')
            print('status=', e.status)
            print('reason=', e.reason)
            print('body=', e.body)
            print('request_id=', e.request_id)
            print('error_code=', e.error_code)
            print('error_message=', e.error_message)

    return None

def restoreDatabase():

    snapshotList = []
    for snapshot in dbSnapshots:
        if snapshot.id.startswith('tc-pcf-bosh-snapshot') and snapshot.status == 'available':
            snapshotList.append(snapshot.id)
    snapshotList.sort(reverse=True)

    if snapshotList is not None:
        print("The most recent available snapshot is %s " % snapshotList[0])
    else:
        print("There are no snapshots to restore from")

    dbSnapshotName = dbSnapshotBase + '-' + '7640aaf11164460db8e643a5226e5770'
    dbClassName = 'db.m3.large'
    secGroupId = 'sg-86020ce2'
    secGroupName = 'tc-mysql'
    # restoredInstance = conn.restore_dbinstance_from_dbsnapshot(dbSnapshotName, dbInstanceName, dbClassName, multi_az=True, db_subnet_group_name='tc-pcf-rdsgroup')
    #
    # iterationCount = 0
    # timerBreak = 30
    # restoredStatus = 'restoring'
    #
    # while ((iterationCount < 60) and (restoredStatus != 'available')):
    #    time.sleep(timerBreak)
    #    try:
    #       restoredInstance.update(validate=True)
    #       restoredStatus = restoredInstance.status
    #       print ("restored db status:  " + restoredStatus)
    #    except ValueError:
    #       print("could no longer access database status, exiting")


    # conn.modify_dbinstance(dbInstanceName, vpc_security_groups=[secGroupId]);
    return None

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--remove', action='store_true', help='takes a snapshot and removes the specified database instance')
group.add_argument('--restore', action='store_true', help='restore the database from the latest snaphot taken')
group.add_argument('--status', action='store_true', help='status for the specified database snapshot')
group.add_argument('--get_snap', action='store_true', help='lists all available snapshots for the specified database instance')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1')
parser.add_argument('-o','--override', help='allows user to specify snapshot to use for a database restore')

args = parser.parse_args()

dbInstanceName = 'tc-pcf-bosh'
dbSnapshotBase = 'tc-pcf-bosh-snapshot'
today = datetime.datetime.now()

print("Connecting to AWS Region [%s] " % args.region)
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

elif args.get_snap:
    getSnapshots()

else:
    getStatusOfDatabase()
