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
    "Prints the list provided from getSnapshots()"

    snapshots = getSnapshots()
    if snapshots is None:
        print("Couldn't find any snapshots for instance " + dbInstanceName + ", note name must start with " + dbSnapshotBase)
        return
    for name in snapshots:
        print(name)

    return snapshots

def getStatusOfDatabase():
    "Gets the status of the specified available database"

    if dbInstances == []:
        print("There is currently no available RDS database running. \nPlease check the AWS Console if this is a problem!")
        return

    for dbInst in dbInstances:
        print("[%s] has status of [%s] " % (dbInstances[dbInst], dbInstances[dbInst].status))

    return None

def removeDatabase():
    "Removes the AWS RDS database instance after first taking a snapshot"

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
    "Restores a database from the latest snapshot"

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

def overrideLatestSnapshot():
    "Will implement an override to use a specific snapshot instead of the most recently available snapshot"

    snapshots = getSnapshots()
    if snapshots is None:
        print("There are no snapshots to restore from, note name must start with " + dbSnapshotBase)
        return

    if args.override not in snapshots:
        print("The snapshot entered for the override is not an available snapshot! \nAvailable snapshots are: \n")
        for snap in snapshots:
            print(snap)
        return

    print("The snapshot specified to use for the override is: [%s] \nWill now restore database from this snapshot!" % args.override)
    dbClassName = 'db.m3.large'
    secGroupId = 'sg-86020ce2'
    secGroupName = 'tc-mysql'
    restoredInstance = conn.restore_dbinstance_from_dbsnapshot(args.override, dbInstanceName, dbClassName, multi_az=True, db_subnet_group_name='tc-pcf-rdsgroup')

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

def delSnapshots():
    "Deletes snapshots from snapshotList when list is greater than 10"

    snapshots = getSnapshots()

    # count = 0
    # maxLength = 10
    # if len(snapshots) < maxLength:
    #     print("Currently there are %s snapshots " % (len(snapshots)))
    #     print("Will quit as the snapshot list is not over 10 snapshots!")
    #
    # print("Will delete old snapshots until there are 10 snapshots in the list!")
    #
    # lastSnap = snapshots[-1]
    # print(lastSnap)
    print("The oldest snapshot in the list is %s\n " % (snapshots[-1]))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--remove', action='store_true', help='takes a snapshot and removes the specified database instance')
group.add_argument('--restore', action='store_true', help='restore the database from the latest snapshot taken')
group.add_argument('--status', action='store_true', help='status for the specified database snapshot')
group.add_argument('--snapshots', action='store_true', help='lists all available snapshots for the specified database instance')

group.add_argument('--del_snapshots', action='store_true', help='delete snapshots from end of list if list greater than 10')
group.add_argument('-o','--override', help='allows user to specify snapshot to use for a database restore')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1', choices=['us-east-1','us-west-2'])

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
    overrideLatestSnapshot()

elif args.snapshots:
    printSnapshots()

elif args.del_snapshots:
    delSnapshots()

else:
    getStatusOfDatabase()
