import boto.ec2
import sys
import time
import collections

def getInstance(info, conn, instances):
    "Retrieves the ECS Instance matching this info!"

    for i in instances:
        if 'deployment' in i.tags and 'Name' in i.tags:
            dep = i.tags['deployment']
            name = i.tags['Name']
        if name == info['Name'] and dep == info['Deployment']:
            return i;

    return None;

def getStatusForInstances():
    "Retrieves the current state for each instance and its deployment. If the instance is running, it will also return the system and instance status checks for each instance."

    print ("\n status for all instances except for bosh based instances... \n")
    for otherIdx in instance_list:
        print ("index: %s " % (otherIdx))
        print ("name: %s deployment: %s " % (instance_list[otherIdx]['Name'], instance_list[otherIdx]['Deployment']))
        otherInst = getInstance(instance_list[otherIdx], conn, instances)
        if otherInst is not None:
            # detailedStatus = boto.ec2.instancestatus.InstanceStatus(id=otherInst.id)
            detailedStatus = conn.get_all_instance_status(instance_ids=otherInst.id)
            print ("instance: %s state: %s " % (otherInst.id, otherInst.state))
            if detailedStatus:
                print ("detailed status: %s | %s" % (detailedStatus[0].system_status.details['reachability'], detailedStatus[0].instance_status.details['reachability']))
            for t in otherInst.tags:
                print ("name: %s value: %s " % (t, otherInst.tags[t]))

    print ("\n status for bosh instances... \n")
    for boshIdx in bosh_list:
        print ("index: %s " % (boshIdx))
        print ("name: %s deployment: %s " % (bosh_list[boshIdx]['Name'], bosh_list[boshIdx]['Deployment']))
        boshInst = getInstance(bosh_list[boshIdx], conn, instances)
        if boshInst is not None:
            print ("instance: %s state: %s " % (boshInst.id, boshInst.state))
            for tgs in boshInst.tags:
                print ("name: %s value: %s " % (tgs, boshInst.tags[tgs]))

    return None;

def stopBoshInstances():
    "Stops the bosh based instances so the others can be stopped after."

    for b in bosh_list:
        boshInst = getInstance(bosh_list[b], conn, instances)

        if boshInst is not None:
            print("\n stopping instance: %s in deployment: %s " % (bosh_list[b]['Name'], bosh_list[b]['Deployment']))
            boshInst.stop()

            while boshInst.state != 'stopped':
                time.sleep(3)
                boshInst.update()
                print ("Instance: %s State: %s" % (bosh_list[b]['Name'], boshInst.state))
        else:
            print("Instance: %s not found " % (bosh_list[b]))

    return None;

def stopOtherInstances():
    "Stops the remaining instances after having stoppped the bastion instance."

    for i in instance_list:
        inst = getInstance(instance_list[i], conn, instances)

        if inst is not None:
            print("\n stopping instance: %s in deployment: %s " % (instance_list[i]['Name'], instance_list[i]['Deployment']))
            inst.stop()

            while inst.state != 'stopped':
                time.sleep(3)
                inst.update()
                print ("Instance: %s State: %s " % (instance_list[i]["Name"], inst.state))
        else:
            print ("Instance: %s not found " % (instance_list[i]))

    return None;

def startOtherInstances():
    "Starts all instances except for bosh based instances and waits until all checks have passed."

    for i in reversed(instance_list):
        rev_inst = getInstance(instance_list[i], conn, instances)

        if rev_inst is not None:

            if(rev_inst.state == 'stopped'):
                print ("starting instance: %s in deployment: %s " % (instance_list[i]['Name'], instance_list[i]['Deployment']))

                sys_reachability = 'unknown'
                inst_reachability = 'unknown'

                rev_inst.start()

                while (rev_inst.state != 'running') or (sys_reachability != 'passed') or (inst_reachability != 'passed'):
                    time.sleep(10)
                    rev_inst.update()
                    rev_inst_status = conn.get_all_instance_status(instance_ids=rev_inst.id)
                    print ("Instance: %s State: %s " % (instance_list[i]['Name'], rev_inst.state))
                    if rev_inst_status:
                        sys_reachability = rev_inst_status[0].system_status.details["reachability"]
                        inst_reachability = rev_inst_status[0].instance_status.details["reachability"]
                        print ("System Status Check: %s Instance Status Check: %s " % (sys_reachability, inst_reachability))
            else:
                print ("Instance: %s is in state [%s]...and will not be started. If this is an issue please see AWS Console" % (rev_inst.id, rev_inst.state))
        else:
            print ("Instance: %s not found " % instance_list[i])

    return None;

def startBoshInstances():
    "Starts bosh based instances and waits until all checks have passed."

    for b in reversed(list(bosh_list)):
        rev_bosh_inst = getInstance(bosh_list[b], conn, instances)

        if rev_bosh_inst is not None:

            if (rev_bosh_inst.state == 'stopped'):
                print("starting instance: %s in deployment: %s " % (bosh_list[b]['Name'], bosh_list[b]['Deployment']))

                bosh_sys_reachability = 'unknown'
                bosh_inst_reachability = 'unknown'

                rev_bosh_inst.start()

                while (rev_bosh_inst.state != 'running') or (bosh_sys_reachability != 'passed') or (bosh_inst_reachability != 'passed'):
                    time.sleep(10)
                    rev_bosh_inst.update()
                    rev_bosh_inst_status = conn.get_all_instance_status(instance_ids=rev_bosh_inst.id)
                    print ("Instance: %s State: %s " % (bosh_list[b]['Name'], rev_bosh_inst.state))
                    if rev_bosh_inst_status:
                        bosh_sys_reachability = rev_bosh_inst_status[0].system_status.details["reachability"]
                        bosh_inst_reachability = rev_bosh_inst_status[0].instance_status.details["reachability"]
                        print ("System Status Check: %s Instance Status Check: %s " % (bosh_sys_reachability, bosh_inst_reachability))
            else:
                print ("Instance: %s is in state [%s]...and will not be started. If this is an issue please see AWS Console" % (rev_bosh_inst.id, rev_bosh_inst.state))
        else:
            print ("Instance: %s not found " % (bosh_list[b]))

    return None;

otherInstances = dict()
with open('./otherInstances.txt', 'r') as file:
    for line in file:
        nd = line.split('|')
        otherInstances[nd[0]] = {'Name': nd[1], 'Deployment': nd[2].replace('\n','')}

instance_list = collections.OrderedDict(sorted(otherInstances.items()))

boshInstances = dict()
with open('./boshInstances.txt', 'r') as file:
    for line in file:
        nd = line.split('|')
        boshInstances[nd[0]] = {'Name': nd[1], 'Deployment': nd[2].replace('\n','')}

bosh_list = collections.OrderedDict(sorted(boshInstances.items()))

# Create a connection to the service
conn = boto.ec2.connect_to_region("us-west-2")
instances = conn.get_only_instances()

USAGE = "Usage: %s (start|stop|status|region)" % sys.argv[0]
try:
    cmdarg = sys.argv[1]
    if cmdarg not in ['start','stop','status','region']:
        print ("Unknown arg: %s" % cmdarg)
        print (USAGE)
        sys.exit(1)
except IndexError:
    print ("Missing option(s)")
    print (USAGE)
    sys.exit(1)

if cmdarg == ('stop'):
    stopBoshInstances()
    print ("\n bosh instances are now stopped!")
    stopOtherInstances()
    print ("\n All instances have now been stopped. \n Your CF environment has been safely shutdown!")


if cmdarg == ('start'):
    print ("\n starting CF instances ... \n")
    startOtherInstances()
    print ("\n starting bosh instances ... \n")
    startBoshInstances()
    print ("\n Your CF environment is now up!")

if cmdarg == ('status'):
    getStatusForInstances()

if cmdarg == ('region'):
    print ("not finished yet...")
