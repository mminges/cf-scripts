import boto.ec2
import sys
import time

def getInstance(info, conn, instances):
    "Retrieves the ECS Instance matching this info!"

    for i in instances:
        if 'deployment' in i.tags and 'Name' in i.tags:
            dep = i.tags['deployment']
            name = i.tags['Name']
        if name == info['Name'] and dep == info['Deployment']:
            return i;

    return None;

def stopBastion():
    "Stops the bastion instance so the others can be stopped after."

    bastion = getInstance(bastion_list[0], conn, instances)

    if bastion is not None:
        print("stopping bastion server...")
        bastion.stop()

        while bastion.state != 'stopped':
            time.sleep(2)
            bastion.update()
            print ("Bastion state: %s" % (bastion.state))
    else:
        print("bastion not found")

    return None;

def stopOtherInstances():
    "Stops the remaining instances after having stoppped the bastion instance."

    for i in instance_list:
        inst = getInstance(instance_list[i], conn, instances)
        if inst is not None:
            print("stopping instance: %s in deployment: %s " % (instance_list[i]['Name'], instance_list[i]['Deployment']))
            inst.stop()

            while inst.state != 'stopped':
                time.sleep(3)
                inst.update()
                print ("Instance: %s State: %s " % (instance_list[i]["Name"], inst.state))
        else:
            print ("Instance: %s not found" % (instance_list[i]))

    return None;

def startOtherInstances():
    "Starts all instances except for the bastion instance and waits until all checks have passed."

    for r in reversed(list(instance_list)):
        rev_inst = getInstance(instance_list[r], conn, instances)
        rev_inst_status = conn.get_all_instance_status()

        if rev_inst is not None:
            print ("starting instance: %s in deployment: %s " % (instance_list[r]['Name'], instance_list[r]['Deployment']))
            rev_inst.start()

            while (rev_inst.state != 'running') or (rev_inst_status[r].system_status.details["reachability"] != 'passed') or (rev_inst_status[r].instance_status.details["reachability"] != 'passed'):
                time.sleep(10)
                rev_inst.update()
                print ("Instance: %s State: %s " % (instance_list[r]["Name"], rev_inst.state))
                print ("System Status Check: %s Instance Status Check: %s " % (rev_inst_status[r].system_status.details["reachability"], rev_inst_status[r].instance_status.details["reachability"]))
        else:
            print ("Instance: %s not found" % (instance_list[r]))

    return None;

instance_list = {
0 : {'Name':'test-2', 'Deployment':'fungus-test-1'},
1 : {'Name':'test-2', 'Deployment':'fungus-test-2'}
}

bastion_list = {
0 : {'Name':'test', 'Deployment':'fungus-test-1'}
}

# Create a connection to the service
conn = boto.ec2.connect_to_region("us-west-2")
instances = conn.get_only_instances()

USAGE = "Usage: %s (start|stop|status)" % sys.argv[0]
try:
    cmdarg = sys.argv[1]
    if cmdarg not in ['start','stop','status']:
        print ("Unknown arg: %s" % cmdarg)
        print (USAGE)
        sys.exit(1)
except IndexError:
    print ("Missing option(s)")
    print (USAGE)
    sys.exit(1)

if cmdarg == ('stop'):
    first = stopBastion()
    second = stopOtherInstances()

if cmdarg == ('start'):
    print ("starting CF instances ...")
    first = startOtherInstances()
    print ("starting bastion")
#    second = startBastion()

if cmdarg == ('status'):
    for idx in instance_list:
        print ("index: %s " % (idx))
        print ("name: %s deployment: %s " % (instance_list[idx]['Name'], instance_list[idx]['Deployment']) )
        inst = getInstance(instance_list[idx], conn, instances)
        if inst is not None:
                print ("instance: %s state: %s " % (inst.id, inst.state))
                for t in inst.tags:
                    print ("name: %s value: %s " % (t, inst.tags[t]))
