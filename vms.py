from __future__ import print_function
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
import sys
from pyVim.task import WaitForTask
from tools import tasks

def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        vimtype, True)
    for view in container.view:
        if view.name == name:
            obj = view
            break
    return obj
    
def changeNIC(si, vm, sbxid):
    content = si.content
    #retrieve the 2nd network adapter
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == 'Network adapter 2':
            virtual_nic_device = dev
            break
            
    #no good device found in the loop        
    if dev.deviceInfo.label!='Network adapter 2': 
        return 
    
    #prepare device spec for editing
    device_change = []
    nicspec = vim.vm.device.VirtualDeviceSpec()
    nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    nicspec.device = dev

    network = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], sbxid)
    dvs_port_connection = vim.dvs.PortConnection()
    dvs_port_connection.portgroupKey = network.key
    dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
    nicspec.device.backing = vim.vm.device.VirtualEthernetCard. DistributedVirtualPortBackingInfo()
    nicspec.device.backing.port = dvs_port_connection

    nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nicspec.device.connectable.startConnected = True
    nicspec.device.connectable.allowGuestControl = True
    device_change.append(nicspec)

    #apply changes
    config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
    task = vm.ReconfigVM_Task(config_spec)
    tasks.wait_for_tasks(si, [task])
        
    
def getVMs(si, sbxid):
    #fetch all vms
    content = si.content
    objView = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
    vmList = objView.view
    objView.Destroy()
    
    #fitler vms starting with sbxid
    VMs = []
    for vm in vmList:
        if vm.name.find(sbxid)>-1:
            VMs.append(vm)
    return VMs        

#filter vms by sbx# id

#change 2nd nic to xxx trunk group

def connectvCenter(host, user, password):
    context = ssl._create_unverified_context()
    si = SmartConnect(host=host, user=user, pwd=password, port=443, sslContext=context)
    return si

def powerOnAll(si, VMs):
    task = []
    for vm in VMs:
        #power on machine
        try:
            task = vm.PowerOnVM_Task()
            tasks.wait_for_tasks(si, [task])
        except Exception,e:
            pass

def ShutDownOnAll(VMs):
    def get_snapshots_by_name_recursively(snapshots, snapname):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snapname:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + get_snapshots_by_name_recursively(snapshot.childSnapshotList, snapname)
        return snap_obj

    for vm in VMs:
        try:  
            #shutdown the machine
            task = vm.ShutdownGuest()
            #revert to 'base' snapshot
            snap_obj = get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList, 'base')
            WaitForTask(snap_obj.RevertToSnapshot_Task())
        except Exception,e:
            print(e)
    
    
if __name__ == "__main__":
    action = sys.argv[1]
    sbxid = sys.argv[2]

    si = connectvCenter('10.10.20.21','admin','admin_password')    
    VMs = getVMs(si, sbxid)
    if action == 'poweron':
        powerOnAll(si, VMs)
    elif action == 'changenic':
        for vm in VMs:
            #2nd nnic label name
            changeNIC(si, vm, 'kube'+sbxid)
    elif action == 'poweroff':
        ShutDownOnAll(VMs)
