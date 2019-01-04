#'S5300SI-V200R005SPH016.pat' Example Patch

import getpass
import re
import subprocess
# import ping
# import socket

from netmiko import ConnectHandler
import ftplib
import time


def inputCreds():
    
    while True:
        print(30 * "-", "Hyperoptic", 30 * "-")
        print(30 * "-", "AutoPatch", 30 * "-", "\n")
        Option = input("Options: \n1. Patch \n2. Software Upgrade \n Enter [1/2]: " ) or '2'
        if (Option == '1'):
            patchName = input("Enter the Patch Version: " ) 
            Option = 1
            break
        elif (Option == '2'):
            patchName = input("Enter the Software Version: " )
            Option = 2
            break
        else:
            pass

    DeviceIP = input("Enter switch IP: ")
    username = input("Enter username: ")
    password = getpass.getpass()
    return patchName, DeviceIP, username, password, Option


def connection(DeviceIP, username, password):
   
    platform = 'huawei'
    device = ConnectHandler(device_type=platform, ip=DeviceIP, username=username, password=password, session_timeout=60)
    
    print(chr(27) + "[2J")
    print(30 * "-", "Hyperoptic", 30 * "-")
    print(30 * "-", "AutoPatch", 30 * "-", "\n")

    print("Connection Established \n")
    print(device)
    
    return device


def getVersion(device):

    output = device.send_command('display version')
    outputList = output.split()

    indexPatch = outputList.index("Copyright")
    indexPatch = int(indexPatch) - 1
    currentPatchNumber = outputList[indexPatch]
    currentPatchNumber = currentPatchNumber.replace(")", "")
    indexSwitch = outputList.index("uptime")
    indexSwitch = int(indexSwitch) - 3
    currentSwitchType = outputList[indexSwitch]

    print("\nSwitch Info: \n")

    print("     Current Version and Patch: ")
    print("     " + currentPatchNumber)

    print("\n     Switch Type: ")
    print("     " + currentSwitchType)


def getFlashSpace(device):
    
    output = device.send_command('dir flash:')
    # device.disconnect()
    outputList = output.split()

    indexFreeSpace = outputList.index("free)")
    indexFreeSpace = int(indexFreeSpace) - 2
    currentFreeSpace = outputList[indexFreeSpace]
    currentFreeSpace = currentFreeSpace.replace("(", "")
    
    indexFreeSpaceUnit = outputList.index("free)")
    indexFreeSpaceUnit = int(indexFreeSpaceUnit) - 1
    currentFreeSpaceUnit = outputList[indexFreeSpaceUnit]
    
    currentFreeSpaceComp = currentFreeSpace.replace(",", "")
    currentFreeSpaceComp = re.sub('[^A-Za-z0-9]+', '', currentFreeSpaceComp)


    if int(currentFreeSpaceComp) > 500:
        print("\n     Free Space:")
        print("     " + currentFreeSpace, currentFreeSpaceUnit)
        return True
    else:
        print("\n     Need More Space")
        return False


def configureFTP(device):
    
    device.send_command("system-view",  expect_string="\[[^\]]*\]")
    device.send_command("ftp server enable")
    device.send_command("aaa", expect_string="aaa?")
    device.send_command("local-user ftpu password cipher hyper0ptic privilege level 15", expect_string="aaa?")
    device.send_command("local-user ftpu service-type ftp", expect_string="aaa?")
    device.send_command("local-user ftpu ftp-directory flash:/", expect_string="aaa?")
    device.send_command("authentication-scheme hol-auth", expect_string="aaa-authen-hol-auth?")
    device.send_command("authentication-mode local radius", expect_string="aaa-authen-hol-auth?")
    device.send_command("return",  expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
    

    output = device.send_command("display ftp-server")
    print("\nFTP Configuration: \n")
    print(  output)

    output = device.send_command("display local-user")
    print("\nLocal Accounts: \n")
    print(  output)


def copyFile(DeviceIP, patchName):
    session = ftplib.FTP('{}'.format(DeviceIP),'ftpu','hyper0ptic')
    file = open('{}'.format(patchName),'rb')                  # file to send
    session.storbinary('STOR '+'{}'.format(patchName), file)     # send the file
    file.close()                                    # close file and FTP
    session.quit()
        

def deconfigureFTP(device):
    
    device.send_command("system-view",  expect_string="\[[^\]]*\]")
    device.send_command("undo ftp server")
    device.send_command("aaa", expect_string="aaa?")
    device.send_command("undo local-user ftpu", expect_string="aaa?")
    device.send_command("authentication-scheme hol-auth", expect_string="aaa-authen-hol-auth?")
    device.send_command("authentication-mode radius local", expect_string="aaa-authen-hol-auth?")
    device.send_command("return",  expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
    
    output = device.send_command("  ")
    print("\nFTP Configuration: \n")
    print(  output)

    output = device.send_command("display local-user")
    print("\nLocal Accounts: \n")
    print(  output)


def applyPatch(device, patchName):
    
    device.send_command("\n",  expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
    device.send_command("patch load {} all run".format(patchName))
    device.send_command("save", expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")

def verifyPatch(device, patchName):

    output = device.send_command("display patch-information")
    print("\nPatch Information: \n")
    print(  output)

# l   Patch Package Name: name of the patch file.
# l   Patch Package Version: patch version.
# l   State: patch status.
# a.         Running: The patch is running.
# b.         Deactive: The patch is in inactive state.
# c.         Active: The patch is in active state.
# After the patch is installed, check the following items:
# l   Check the Patch Package Name and Patch Package Version fields to determine whether the loaded patch is correct. If not, load and install the correct patch.
# l   Check the patch status (State).
# a.         If the patch is in Running state, the patch is working properly.
# b.         If the patch is in Deactive state, run the patch active all command in the user view to activate the patch, and run the patch run all command to run the patch. If the patch is still not in Running state, contact Huawei technical support personnel.
# c.         If the patch is in Active state, run the patch run all command in the user view to run the patch. If the patch is still not in Running state, contact Huawei technical support personnel.
    

# def patchRoleBack(device):

#     device.send_command("\n",  expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
#     device.send_command("patch delete all")
#     device.send_command("reboot", expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")




# def applySoftware(device, patchName):
    
#     device.send_command("\n",  expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
#     device.send_command("startup system-software {}".format(patchName), expect_string="((?:<.*>)|(?<=>)(?:\<.*\n?.*\>))")
#     device.send_command("reboot", expect_string="\[Y\/N\]")
#     device.send_command("Y")
#     # device.send_command("save")


# def pingDevice(DeviceIP):
    
#     while True:
#         pingP = subprocess.call(['ping', '-c', '5', '-W', '3', DeviceIP], stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
#         if pingP == 0:
#             print('Up')
            
#             break
#         else:
#             print('Down')
    # try:
    #     output = ping.verbose_ping(DeviceIP, count=3)
    #     # delay = ping.Ping('www.wikipedia.org', timeout=2000).do()
    # except socket.error:
    #     print ("Ping Error:")

    # print(output)


# def readCSV():
    
#     csvList = []
#     with open('/mnt/c/Users/adam.jarvis/output.csv', mode='r') as infile:
#     # with open('/home/adam.jarvis/Switches_Detailed.csv', mode='r') as infile:
#         reader = csv.reader(infile)
        
#         for line_list in reader:
            
#             if str(line_list[0]) == 'IP' or str(line_list[0]) == '':
#                 pass
#             elif str(line_list[1]) == 'Failed':
#                 csvList.append(line_list)
#                 # print(line_list[0], '-', line_list[5],'-', line_list[6],'-', line_list[7],'-', line_list[8])

#     return csvList


if __name__ == '__main__':
    
    patchName, DeviceIP, username, password, Option = inputCreds()
    device = connection(DeviceIP, username, password)
    getVersion(device)
    getFlashSpace(device)
    configureFTP(device)
    copyFile(DeviceIP, patchName)
    # if (Option == 1):
    #     pass
    applyPatch(device, patchName)
    verifyPatch(device, patchName)
    # elif (Option ==2):
    #     applySoftware(device, patchName)
    deconfigureFTP(device)
    # pingDevice(DeviceIP)


# from ftplib import FTP_TLS
# ftp=FTP_TLS()
# ftp.set_debuglevel(2)
# ftp.connect('172.16.21.177', 22)
# ftp.sendcmd('USER ftpu')
# ftp.sendcmd('PASS hyper0ptic')
# print(ftp.dir())
# ftp.close()

# ftp = FTP(host="172.16.21.177", user="ftpu", passwd="hyper0ptic")

#  ftp = ftplib.FTP()
#  host = "172.16.21.197"
#  port = 21
#  ftp.connect(host, port)
#  print (ftp.getwelcome())
#  try:
#       print ("Logging in...")
#       ftp.login("ftpu", "hyper0ptic")
#  except:
#      "failed to login"


# import ftplib
# session = ftplib.FTP('172.16.21.197','username','password')
# file = open('cup.mp4','rb')                  # file to send
# session.storbinary('STOR '+'cup.mp4', file)     # send the file
# file.close()                                    # close file and FTP
# session.quit()
