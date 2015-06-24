import boto.rds
import boto.ec2
import datetime
import time
import argparse
from datetime import date, timedelta

def getStatusOfDatabase():
    if dbInstances is not None:
        # dbInstances.update(validate=True)
        print("This database has status of %s " % (dbInstances.status))
    else:
        print("There is currently no available RDS database running. Please check the AWS Console if this is a problem!")

def removeDatabase():
    today = datetime.date.today()

    snapshotName = dbInstanceName + '-' + today.strftime('%Y%m%d')
    print("Before removing database, will create a snapshot under the followin name: \n%s " % snapshotName)

    prevSnapshotName = datetime.datetime.now() - datetime.timedelta(days=1)
    prevSnapshotName_str = prevSnapshotName.strftime('%Y%m%d')
    latestSnapshotName = dbInstanceName + '-' + prevSnapshotName_str
    print("\nThe latest snapshot taken is: \n%s " % latestSnapshotName)

    print("\nDatabase instances that are active are: %s " % (dbInstances))

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
    dbSnapshotName = dbInstanceName + '-' + '7640aaf11164460db8e643a5226e5770'
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
group.add_argument('--status', action='store_true', help='status for the specified database')
group.add_argument('--list_snap', action='store_true', help='lists all available snapshots for the specified database instance')

parser.add_argument('-r','--region', help='connect to the specified region', default='us-east-1')

args = parser.parse_args()

dbInstanceName = 'tc-pcf-bosh'

print("Connecting to AWS Region [%s] " % args.region)
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
        print("\n%s has status of [%s] " % (i, i.status))

else:
    getStatusOfDatabase()
