import os,sys,csv,commands,subprocess

#############################################################
#                USAGE                                      #       
#   py .py file_name x_position y_position split_character  #
#############################################################


def get_stats(power, file_name):

   pe_start_time = {}
   pe_end_time = {}
   pe_time_diff = {}
   pe_idle_time = {}
   
   for i in range (0,100):
          pe_start_time[i] = 100000
          pe_end_time[i] = 0
          pe_time_diff[i] = 0
   
   #input_file = os.path.join(path, file_name)
   csv_reader = csv.reader(file_name)
   
   with open(file_name) as csv_reader:
       for row in csv_reader:
           tokens = row.split(' ')
           pe = int(tokens[3])
           time = float(tokens[1])
           if "start" in row:
               pe_start_time[pe] = min(pe_start_time[pe], time)    
           elif "end" in row:
               pe_end_time[pe] = max(pe_end_time[pe], time)    
   
   # find the minimum start time and the end time across PEs to get the total execution time

   minimum_start_time = pe_start_time[0]
   for i in range (0,100):
         if(pe_start_time.get(i) == 100000):
               break
         else:
               if(pe_start_time[i] < minimum_start_time):
                      minimum_start_time = pe_start_time[i]

   maximum_end_time=0

   for i in range (0,100):
         if (pe_start_time.get(i) == 100000):
                  break
         else:
                  if(pe_end_time[i] > maximum_end_time):
                      maximum_end_time = pe_end_time[i]
   
   total_execution_time = maximum_end_time - minimum_start_time          
   
   for i in range (0,100):
     if(pe_start_time.get(i) == 100000):
           break
     else:
           pe_time_diff[i] = pe_end_time[i] - pe_start_time[i]
   
   
   
   for i in range (0,100):
         if (pe_start_time.get(i) == 100000):
                  break
         #else :          
                  #print "PE:%d time:%f" %(i,pe_time_diff[i])
   
   maximum = 0
   for i in range (0,100):
         if (pe_start_time.get(i) == 100000):
                  break
         else:
                  if(pe_time_diff[i] > maximum):
                           maximum = pe_time_diff[i]

   total_idle_time = 0   
   for i in range (0,100):
         if (pe_start_time.get(i) == 100000):
                  break
         else:
                  total_idle_time = total_idle_time + (maximum - pe_time_diff[i])
                  #print "PE: %d Idle_time: %f"%(i, maximum - pe_time_diff[i])
                  pe_idle_time[i] = maximum - pe_time_diff[i]
   
   
   max_idle_time = 0
   for i in range (0,100):
         if (pe_start_time.get(i) == 100000):
                  break
         else:
                  if(pe_idle_time[i] > max_idle_time):
                          max_idle_time = pe_idle_time[i]
   
   minimum = pe_time_diff[0]   
   for i in range (0,100):
         if(pe_start_time.get(i) == 100000):
               break
         else:
                  if(pe_time_diff[i]<minimum):
                          minimum = pe_time_diff[i]

   average_idle_time = total_idle_time/num_pes # 60 being total number of nodes
   percentage_average_idle_time  = (average_idle_time/total_execution_time)*100	
   percentage_max_idle_time  = (max_idle_time/total_execution_time)*100	

 #  print >> outputfile_leanmd, "Power %d"%power
  # print >> outputfile_leanmd, "Max Idle Time : %f"%(max_idle_time)
 #  print >> outputfile_leanmd, "Average Idle Time :%f"%(average_idle_time) #60 being the number of nodes
 #  print >> outputfile_leanmd, "Percentage max idle time (Max Idle time/total_execution_time)*100 : %f"%(percentage_max_idle_time)
 #  print >> outputfile_leanmd, "Percentage average idle time (Average Idle time/total_execution_time)*100: %f"%(percentage_average_idle_time)
 #  print >> outputfile_leanmd, "total execution time time is %f"%(total_execution_time)

   for i in range (0,100):
         if(pe_start_time.get(i) == 100000):
               break
         else:
               print >> perpe_leanmd, "PE:%d Exec.Time %f"%(i,pe_time_diff[i])

   print >> perpe_leanmd, "--------------------------------------\n"
   print >> outputfile_leanmd, "%d:%f:%f:%f\n"%(power,total_execution_time,percentage_max_idle_time,percentage_average_idle_time)

   return                

                         
os.system("rm -rf outputlog")
os.system("rm -rf charm_output_log")
os.system("rm -rf leanmd_outputlog")
os.system("rm -rf leanmd_charm_outputlog")
os.system("rm -rf output_file_leanmd")
#outputfile = open("./leanmd_outputlog", "a+")
logfile = open("./leanmd_charm_output_log","a+")
outputfile_leanmd = open("./output_file_leanmd","a+")
perpe_leanmd = open("./leanmdperpelog","a+")

cpu_power_max   = 60
cpu_power_min   = 20
step            = 1
num_pes         = 30
no_of_steps     = (cpu_power_max - cpu_power_min)/step
memory_power    = 80
user            = os.getlogin()
node_list       = ["41","42","43","44", "45"]# , "46","47","48","49", "50"]
power           = cpu_power_max

#cmd =   "~/sp14-cs533_charm/charm/examples/charm++/leanmd/charmrun +p30 ++nodelist ~/sp14-cs533_charm/Doc/nodes12 ~/sp14-cs533_charm/charm/examples/charm++/leanmd/leanmd 30 30 30 1 +setcpuaffinity +pemap 0-5 +balancer RefineLB"
cmd =   "~/sp14-cs533_charm/charm/examples/charm++/leanmd/charmrun +p30 ++nodelist ~/sp14-cs533_charm/Doc/nodes12 ~/sp14-cs533_charm/charm/examples/charm++/leanmd/leanmd 30 30 30 1 +setcpuaffinity +pemap 0-5"

for i in range(0, no_of_steps):
    set_power_limits = "~/sp14-cs533_charm/Scripts/setpowerlimits " + str(power) + " " +str(memory_power)
    # set the power cap for each node
    for id in node_list:
        node_name = user+"@tarekc" + id + ".cs.illinois.edu"
        if(subprocess.call(["ssh" , node_name , set_power_limits])==0):
               print "power cap set to" + " " + str(power) + " on "+  user + " " + "tarekc"+ str(id)
    # run the script
    status, output = commands.getstatusoutput(cmd)

    logfile_name = "output_log"+str(power)
    
    rm_command = "rm" + " " + logfile_name
    os.system(rm_command)        

    outputfile = open(logfile_name,"a+")
    print >> logfile,output
    for line in output.splitlines():
       if "starttime" in line:
           print >> outputfile,line #"%d %s" % (power, line)
       if "endtime" in line:
           print >> outputfile,line #"%d %s" % (power, line)
    outputfile.close()
    print "preparing for next iteration"
    get_stats(power, logfile_name)
    power = power - step



