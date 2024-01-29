#!/usr/bin/env python
# coding: utf-8

# In[1]:
import os
import csv
import subprocess
import re
import shutil
import random
import math
import sys
import datetime
from multiprocessing import Process, Manager

def search_changesets_issue_ids(source_dir, issue_id):
    proc = subprocess.Popen(['git', 'log', '--all', '--grep=%s' % issue_id, '--pretty=format:"commit1: %H%n title1: %s%n date1: %cD%n body1: %b"'], stdout=subprocess.PIPE, cwd=source_dir)
    output, errs = proc.communicate()
    #output = proc.stdout.read()
    output = output.decode('utf-8')
    output += 'commit1'
    
    result_changesets = re.findall('commit1: (.*)', output)
    result_dates = re.findall('date1: (.*)', output)
    result_titles = re.findall('title1: (.*)', output)
    result_bodys = re.findall('body1: (.*?)commit1', output, re.DOTALL)
    
    changesets_list = []
    for result_title, result_body, result_date, result_changeset in zip(result_titles, result_bodys, result_dates, result_changesets):
        if re.search('[^0-9]'+issue_id+'[^0-9]', result_body) or re.search('[^0-9]'+issue_id+'[^0-9]', result_title):
            changesets_list.append(result_changeset.strip()+'|'+result_date.strip())
    return changesets_list

def read_issue_ids(project):
    issue_ids = []
    proc = subprocess.Popen(['find', '.', '-regex', '.*[0-9]+\.txt'], stdout=subprocess.PIPE, cwd=os.path.join('issues', 'perf_bugs', project))

    output, errs = proc.communicate()
    output = output.decode('utf-8')
    for line in output.split('\n'):
        issue_id = line.split('/')[-1][:-4]
        if len(issue_id) > 3:
            issue_ids.append(issue_id)
    return issue_ids


def collect_changeset(issue, changesets_list, project, data_dir, source_dir):
    try:
        for item in changesets_list:
            changeset = item.split('|')[0]
            timestamp = item.split('|')[1]
            print(changeset)
            # make the dir of the commit
            if not os.path.exists(os.path.join(data_dir, project, 'commits', changeset)):
                os.mkdir(os.path.join(data_dir, project, 'commits', changeset))
            
            # record the timestamp of the commit
            f = open(os.path.join(data_dir, project, 'commits', changeset, "issue_id.txt"), "w")
            f.write(issue)
            f.close()

            f = open(os.path.join(data_dir, project, 'commits', changeset, "timestamp.txt"), "w")
            f.write(timestamp)
            f.close()

            # collect the modified files
            proc = subprocess.Popen(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', changeset], stdout=subprocess.PIPE, cwd=source_dir)
            output, errs = proc.communicate()
            output = output.decode('utf-8')
            modified_files = output.split('\n')[:-1]

            if len(modified_files) > 0:
                if not os.path.exists(os.path.join(data_dir, project, 'commits', changeset, 'diff')):
                    os.makedirs(os.path.join(data_dir, project, 'commits', changeset, 'diff'))
                if not os.path.exists(os.path.join(data_dir, project, 'commits', changeset, 'before')):
                    os.makedirs(os.path.join(data_dir, project, 'commits', changeset, 'before'))
                if not os.path.exists(os.path.join(data_dir, project, 'commits', changeset, 'after')):
                    os.makedirs(os.path.join(data_dir, project, 'commits', changeset, 'after'))
            for file_name in modified_files:
                if file_name.endswith('.java') or file_name.endswith('.groovy'):
                    # write the diff of the file
                    f = open(os.path.join(data_dir, project, 'commits', changeset, 'diff', file_name.replace('/', '_')), "w")
                    proc = subprocess.Popen(['git', 'diff', changeset + '^:' + file_name, changeset + ':' + file_name], stdout=f, cwd=source_dir)
                    output, errs = proc.communicate()
                    f.close()

                    # output the file after the commit 
                    f = open(os.path.join(data_dir, project, 'commits', changeset, 'after', file_name.replace('/', '_')), "w")
                    proc = subprocess.Popen(['git', 'show', changeset + ':' + file_name], stdout=f, cwd=source_dir)
                    output, errs = proc.communicate()
                    f.close()

                    # output the file before the commit 
                    f = open(os.path.join(data_dir, project, 'commits', changeset, 'before', file_name.replace('/', '_')), "w")
                    proc = subprocess.Popen(['git', 'show', changeset + '^:' + file_name], stdout=f, cwd=source_dir)
                    output, errs = proc.communicate()
                    f.close()
    except Exception as e:
        print('Exception', str(e))

def execute_thread(project, data_dir, source_dir, issue_ids):
    for issue in issue_ids:
        print(issue)
        changesets_list = search_changesets_issue_ids(source_dir, issue)
        if len(changesets_list) == 0:
            print('cannot find', issue)
        collect_changeset(issue, changesets_list, project, data_dir, source_dir)

if __name__=='__main__':

    data_dir = sys.argv[1]
    project= sys.argv[2]
    source_dir = os.path.join('/home/gzhao/performance_bug_prediction/github_data_collection/projects', project)
    issue_ids = read_issue_ids(project)
    print('number of issues ids: %d' % len(issue_ids))
    if not os.path.exists(os.path.join(data_dir, project, 'commits')):
        os.makedirs(os.path.join(data_dir, project, 'commits'))
    num_threads = 4
    chunk_size = math.ceil(len(issue_ids)/num_threads)
    process = []
    for i in range(0, len(issue_ids), chunk_size):
        p = Process(target=execute_thread, args=(project, data_dir, source_dir, issue_ids[i: i+chunk_size],))
        process.append(p)
        p.start()
    for p in process:
        p.join()
