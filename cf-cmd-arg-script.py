import boto.ec2
import sys
import time
import collections
import copy

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

    print ("\nstatus for each instance... \n")
    for otherIdx in instance_list:
        print("index: %s " % (otherIdx))
        print("name: %s deployment: %s " % (instance_list[otherIdx]['Name'], instance_list[otherIdx]['Deployment']))
        otherInst = getInstance(instance_list[otherIdx], conn, instances)
        if otherInst is not None:
            detailedStatus = conn.get_all_instance_status(instance_ids=otherInst.id)
            print("instance: %s state: %s " % (otherInst.id, otherInst.state))
            if detailedStatus:
                print("System Status Check: %s \nInstance Status Check: %s" % (detailedStatus[0].system_status.details['reachability'], detailedStatus[0].instance_status.details['reachability']))
            for t in otherInst.tags:
                print("name: %s value: %s " % (t, otherInst.tags[t]))
        print("")

    return None;

def serverIsUp(svr_inst):
    "Will check whether the current server in the list is running and checks that both system and instance status checks have passed"
    result = True

    if svr_inst is not None:
        sys_reachability = 'unknown'
        inst_reachability = 'unknown'

        svr_inst.update()

        svr_inst_status = conn.get_all_instance_status(instance_ids=svr_inst.id)
        if svr_inst_status:
            sys_reachability = svr_inst_status[0].system_status.details["reachability"]
            inst_reachability = svr_inst_status[0].instance_status.details["reachability"]
        else:
            result = False

        if (svr_inst.state != 'running') or (sys_reachability != 'passed') or (inst_reachability != 'passed'):
            result = False
    else:
        result = False

    return result

def serverIsDown(svr_inst):
    "Will check whether the current server in the list is in a shut down state"
    result = True

    if svr_inst is not None:
        svr_inst.update()
        if (svr_inst.state != 'stopped'):
            result = False
    else:
        result = False

    return result

def stopInstances(instance_list):
    "Stops all the instances in reverse order of the list provided."

    count = 0
    for i in reversed(instance_list):
        inst = getInstance(instance_list[i], conn, instances)

        if inst is not None:

            if(inst.state != 'stopped'):
                nm = instance_list[i]['Name']
                dep = instance_list[i]['Deployment']
                shouldPause = instance_list[i]['ShouldPause']
                print("\nstopping instance: %s in deployment: %s " % (nm, dep))
                inst.stop()
                count += 1

                if shouldPause and shouldPause == 'stop-pause' or shouldPause == 'both':
                    print("\nWill wait for instance(s) to stop!")
                    while not serverIsDown(inst):
                        time.sleep(2)
                        print('.',end="",flush=True)
            else:
                print("Instance: %s is in state [%s]...and will not be stopped. If this is an issue please see AWS Console" % (inst.id, inst.state))

        else:
            print("Instance: %s not found " % (instance_list[i]))

    print("\n[%d] servers stopped" % count)
    return None;

def startInstances(instance_list):
    "Starts all instances in order from the list provided and waits for the system and instance checks to complete."

    count = 0
    for i in instance_list:
        inst = getInstance(instance_list[i], conn, instances)

        if inst is not None:

            if(inst.state == 'stopped'):
                nm = instance_list[i]['Name']
                dep = instance_list[i]['Deployment']
                shouldPause = instance_list[i]['ShouldPause']
                print("\nstarting instance: %s in deployment: %s " % (nm, dep))
                inst.start()
                count += 1

                if shouldPause and shouldPause == 'start-pause' or shouldPause == 'both':
                    print("Will wait until the instance is running and both system and instance status checks have passed!")
                    while not serverIsUp(inst):
                        time.sleep(2)
                        print('.',end="",flush=True)

            else:
                print("Instance: %s is in state [%s]...and will not be started. If this is an issue please see AWS Console" % (inst.id, inst.state))
        else:
            print("Instance: %s not found " % instance_list[i])


    print("\n[%d] servers started" % count)
    return None;

otherInstances = dict()
with open('./otherInstances.txt', 'r') as file:
    for line in file:
        nd = line.split('|')
        otherInstances[nd[0]] = {'Name': nd[1], 'Deployment': nd[2], 'ShouldPause' : nd[3].replace('\n','')}

instance_list = collections.OrderedDict(sorted(otherInstances.items()))

# Create a connection to the service
conn = boto.ec2.connect_to_region("us-west-2")
instances = conn.get_only_instances()

USAGE = "Usage: %s (start|stop|status|region)" % sys.argv[0]
try:
    cmdarg = sys.argv[1]
    if cmdarg not in ['start','stop','status','region']:
        print("Unknown arg: %s" % cmdarg)
        print(USAGE)
        sys.exit(1)
except IndexError:
    print("Missing option(s)")
    print(USAGE)
    sys.exit(1)

if cmdarg == ('stop'):
    print("\nstopping instances ... \n")
    stopInstances(instance_list)
    print("\nAll instances have now been stopped. \nYour CF environment has been safely shutdown!")


if cmdarg == ('start'):
    print("\nstarting instances ... \n")
    startInstances(instance_list)
    print("\nYour CF environment is now up!")

if cmdarg == ('status'):
    getStatusForInstances()

if cmdarg == ('region'):
    print("not finished yet...")
