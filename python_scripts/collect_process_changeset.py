#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import os
import csv
import subprocess
import re
from multiprocessing import Process
from reset_source_files import obtain_time_last_commit
import datetime
import math


def collect_changeset(changesets_list, project, data_dir, source_dir, file_name):
    for item in changesets_list:
        try:
            changeset = item.split('|')[0]
            timestamp = item.split('|')[1]
            # make the dir of the commit
            
            if not os.path.exists(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'diff')):
                os.makedirs(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'diff'))
            if not os.path.exists(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'before')):
                os.makedirs(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'before'))
            if not os.path.exists(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'after')):
                os.makedirs(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'after'))
            
            # record the timestamp of the commit
            f = open(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, "timestamp.txt"), "w")
            f.write(timestamp)
            f.close()
    
            # write the diff of the file
            f = open(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'diff', file_name.replace('/', '_')), "w")
            proc = subprocess.Popen(['git', 'diff', changeset + '^:' + file_name, changeset + ':' + file_name], stdout=f, cwd=source_dir)
            output, errs = proc.communicate()
            f.close()

            # output the file after the commit 
            f = open(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'after', file_name.replace('/', '_')), "w")
            proc = subprocess.Popen(['git', 'show', changeset + ':' + file_name], stdout=f, cwd=source_dir)
            output, errs = proc.communicate()
            f.close()

            # output the file before the commit 
            f = open(os.path.join(data_dir, project, 'commits_for_process_metrics', changeset, 'before', file_name.replace('/', '_')), "w")
            proc = subprocess.Popen(['git', 'show', changeset + '^:' + file_name], stdout=f, cwd=source_dir)
            output, errs = proc.communicate()
            f.close()

        except Exception as e:
            print('Exception:', str(e))





def search_changesets(file_name, source_dir, start_time, split_time):
    proc = subprocess.Popen(['git', 'log', '--pretty=format:"commit1: %H%n date1: %cD%n"', file_name], stdout=subprocess.PIPE, cwd=source_dir)
    output, errs = proc.communicate()
    output = output.decode('utf-8')
    
    result_changesets = re.findall('commit1: (.*)', output)
    result_dates = re.findall('date1: (.*)', output)
    
    changesets_list = [] 
    for result_date, result_changeset in zip(result_dates, result_changesets):
        date_time_obj = datetime.datetime.strptime(result_date.strip()[:-6], '%a, %d %b %Y %H:%M:%S')
        #print(date_time_obj)
        if start_time<date_time_obj and split_time>date_time_obj:
            changesets_list.append(result_changeset.strip()+'|'+result_date.strip())
    return changesets_list
    



def execute_thread(project, data_dir, source_dir, files, start_time, split_time):
    for file_name in files:
        file_name = file_name[file_name.find(project)+len(project)+1:]
        print(file_name)
        changesets = search_changesets(file_name, source_dir, start_time, split_time)
        if len(changesets) > 0:
            print(changesets)
        collect_changeset(changesets, project, data_dir, source_dir, file_name)


if __name__=='__main__':
    source_dir = os.path.join('/home/gzhao/performance_bug_prediction/github_data_collection/projects', project)
    data_dir = sys.argv[1]
    project = sys.argv[2]

    last_commit_time, _ = obtain_time_last_commit(source_dir)
    split_time = last_commit_time - datetime.timedelta(days=180)
    print('split_time', split_time)
    start_time = split_time - datetime.timedelta(days=180)
    print('start_time', start_time)
    
    
    methods = pd.read_csv(os.path.join(data_dir, project, 'methods.csv'))

    files = methods['File'].unique()
    num_threads = 6
    chunk_size = math.ceil(len(files)/num_threads)
    process = []
    for i in range(0, len(files), chunk_size):
        p = Process(target=execute_thread, args=(project, data_dir, source_dir, files[i: i+chunk_size], start_time, split_time,))
        process.append(p)
        p.start()
    for p in process:
        p.join()

