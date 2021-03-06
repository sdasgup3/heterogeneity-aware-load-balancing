#!/usr/bin/python
import os,time, sys
import subprocess
import commands
import re

##########################################
#Usage: python file.py cpu_power_max cpu_power_min  step_size num_pes

os.system("rm -rf outputlog")
os.system("rm -rf charm_output_log")

outputfile = open("./outputlog", "a+")
logfile = open("./charm_output_log","a+")


#if len(sys.argv)==3
cpu_power_max   = int(sys.argv[1])
cpu_power_min   = int(sys.argv[2])
step            = int(sys.argv[3])
num_pes         = sys.argv[4]


no_of_steps 	= (cpu_power_max - cpu_power_min)/step
memory_power  	= 80
user            = os.getlogin()
node_list 	= ["41","42","43","44", "45", "46","47","48","49", "50"]
#node_list 	= ["41","42","43","44", "45"]
#node_list 	= ["46","47","48","49", "50"]
power 		= cpu_power_max
Iteration       = "20"

cmd = "~/sp14-cs533_charm/charm/examples/charm++/jacobi2d-iter/charmrun"   + " \
+p" + num_pes + " ++nodelist"  + " ~/sp14-cs533_charm/Doc/nodes41-50" + " \
~/sp14-cs533_charm/charm/examples/charm++/jacobi2d-iter/jacobi2d"  + " 36000 \
36000 60 60 " + Iteration  + " +setcpuaffinity +pemap 0-5  +balancer"
# RefineLB" 
#+balancer GreedyLB"
#\
#+LBSyncResume" 


#for i in range(cpu_power_max, cpu_power_min):
for i in range(0, no_of_steps):

  set_power_limits = "~/sp14-cs533_charm/Scripts/setpowerlimits " + str(power) + " " +str(memory_power)
  # set the power cap for each node
  for id in node_list:      
    node_name = user+"@tarekc" + id + ".cs.illinois.edu"
    if(subprocess.call(["ssh" , node_name , set_power_limits])==0):
       print "power cap set to" + " " + str(power) + " " + "on" + " "+  user + " " + "tarekc"+ str(id)

  # run the script
  status, output = commands.getstatusoutput(cmd)
  print >> logfile,output
  for line in output.splitlines():
    if "Total Program Time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Total Iteration Time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Max pe Time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Max idle time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Average idle time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Percentage max idle time" in line:
      print >> outputfile,"%d: %s" % (power, line)
    if "Percentage average idle time" in line:
      print >> outputfile,"%d: %s" % (power, line)
  #print >> outputfile,"\n"
  
  print "preparing for next iteration"
  power = power - step

print "exiting"
