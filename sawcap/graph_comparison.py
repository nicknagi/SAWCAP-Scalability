import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import argparse

def parse_stats_file(file, stat_names):
  workload_dictionary = {}
  current_workload_name = ""
  current_workload_data = {}
  for line in open(file):
    if "sawcap problems" in line:
      current_workload_data = {}
    split = line.split()
    if len(split)==1:
      if current_workload_data != {}:
        workload_dictionary[current_workload_name].append(current_workload_data)
        current_workload_data = {}
      current_workload_name = split[0]
      if current_workload_name not in workload_dictionary.keys():
        workload_dictionary[current_workload_name]=[]
    else:
      for stat_name in stat_names:
        if stat_name in line:
          current_workload_data[stat_name] = float(line.split(stat_name + " Prediction Accuracy: ")[1])
          break
  if current_workload_data != {}:
    workload_dictionary[current_workload_name].append(current_workload_data)
    current_workload_data = {}
  lengths = [len(workload) for workload in workload_dictionary.values()]
  number_of_workloads = lengths[0]
  assert(len(set(lengths)) == 1)
  return workload_dictionary, number_of_workloads

def find_averages_per_workload_type(workload_dictionary, num_workloads, stat_names):
  averages = {}
  for stat_name in stat_names:
    averages[stat_name] = {}
  for worload_name, worload_stats in workload_dictionary.items():
    for stat_name in stat_names:
      averages[stat_name][worload_name] = 0
    for stat_num, stat in enumerate(worload_stats):
      for stat_name in stat_names:
        averages[stat_name][worload_name] +=stat[stat_name]
        if stat_num == (num_workloads-1):
          averages[stat_name][worload_name] = averages[stat_name][worload_name]/num_workloads
  return averages

def plot_data(array_of_stats_for_algos, stat_names, algos, save_path):
  merged_stats = {}
  for stat_name in stat_names:
    merged_stats[stat_name] = {}
  for algo in array_of_stats_for_algos:
    for stat_name in stat_names:
      for worload_name, worload_stat in algo[stat_name].items():
        if worload_name not in merged_stats[stat_name]:
          merged_stats[stat_name][worload_name]=[]
        merged_stats[stat_name][worload_name].append(worload_stat)
  for stat_name in stat_names:
    stat_frame = pd.DataFrame(merged_stats[stat_name]).T
    stat_frame.columns = algos
    stat_frame.plot(kind="bar")
    # Add title and axis names
    plt.title(stat_name)
    plt.xlabel('Algoripthms')
    plt.ylabel('Percentage Accuracy')
    
    # Limits for the Y axis
    plt.ylim(0,100)

    if save_path != None:
      stat_frame.to_csv(save_path + stat_name + '_'.join(algos) + '.csv')
      temp_save_path = save_path + stat_name + '_'.join(algos) + '.png'
      plt.savefig(temp_save_path)
      plt.close()
    else:
      print(stat_frame)
      plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plot Stats. Usage example: python graph_comparison.py --dir_name ~/Desktop/capstone/sawcap --stats CPU,MEM --stat_files sawcap_stats.txt --algos lasso --save_path ~/Desktop/capstone/sawcap/my_unique_id_')
    parser.add_argument('--dir_name', required=True, help='Directory name with all files')
    parser.add_argument('--stats', required=True, help='List of stats to compare, separated by a comma without space')
    parser.add_argument('--stat_files', required=True, help='List of data files to compare, separated by a comma without space')
    parser.add_argument('--algos', required=True, help='Algo names associated with stat files, , separated by a comma without space')
    parser.add_argument('--save_path', help='Save path for graphs')
    args = parser.parse_args()
    
    os.chdir(args.dir_name)
    stat_names = args.stats.split(',')
    stat_files = args.stat_files.split(',')
    algos = args.algos.split(',')
    array_of_stats_for_algos = []
    for file in stat_files:
      workload_dictionary, num_workloads = parse_stats_file(file, stat_names)
      averages = find_averages_per_workload_type(workload_dictionary, num_workloads, stat_names)
      array_of_stats_for_algos .append(averages)
    plot_data(array_of_stats_for_algos, stat_names, algos, args.save_path)
