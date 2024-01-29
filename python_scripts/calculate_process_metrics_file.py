#!/usr/bin/env python
# coding: utf-8

# In[4]:


import pandas as pd
import os
import csv
import subprocess
import re
import shutil
import random
from multiprocessing import Process, Manager
import urllib
import datetime


# In[2]:


def collect_changedfiles(project_dir, project):
    num_files = 0
    subdir = 'diff'
    relative_path_l = []
      
    commits_dir = os.path.join(project_dir, 'commits_for_process_metrics')
    for commit in os.listdir(commits_dir):
        commit_dir = os.path.join(commits_dir, commit)
        for file in os.listdir(os.path.join(commit_dir, subdir)):
            if file.endswith('.java') or file.endswith('.groovy'):
                file_name = file.split('_')[-1]
                with open(os.path.join(commit_dir, subdir, file)) as reader:
                    content = reader.read()
                    for line in content.split('\n'):
                        if line.startswith('- '):
                            relative_path = os.path.join('commits_for_process_metrics', commit, subdir, file)
                            relative_path_l.append(relative_path)
                            num_files += 1
                            break
                        
    print('number of changed files included in the project: %d' % (num_files))
    with open(os.path.join(project_dir, 'changedfiles_process_metrics.txt'), 'w') as writer:
        for relative_path in relative_path_l:
            writer.write(relative_path)
            writer.write('\n')




def metrics(revisions, source_dir):
    num_perf_fixing_revisions = 0
    num_general_fixing_revisions = 0
    perf_bugs = set()
    general_bugs = set()
    lines_deleted = 0
    lines_added = 0
    for commit_file in revisions:
        bug_id = -1
        changeset = commit_file.split('/')[1]
        if changeset in changeset_bug:
            bug_id = changeset_bug[changeset][0]
            output = changeset_bug[changeset][1]
            #print('bug_id', bug_id)
        else:
            proc = subprocess.Popen(['git', 'log', changeset, '-1'], stdout=subprocess.PIPE, cwd=source_dir)
            output, errs = proc.communicate()
            output = output.decode('utf-8')
            result = re.search('#.*?([0-9]+)', output)
            if result is not None:
                bug_id = result.group(1)
                #print(bug_id)
                changeset_bug[changeset] = [bug_id, output]
            #print(bug_id)
        if changeset in perf_fixing_commits:
            num_perf_fixing_revisions += 1
            #print(perf_bugs)
            if bug_id != -1:
                perf_bugs.add(bug_id)
        else:
            if '#' in output:
                num_general_fixing_revisions += 1
                if bug_id != -1:
                    general_bugs.add(bug_id)
        
        with open(os.path.join(data_dir, project, commit_file)) as reader:
            content = reader.read()
        for line in content.split('\n'):
            if line.startswith('-'):
                lines_deleted += 1
            if line.startswith('+'):
                lines_added += 1
    return num_perf_fixing_revisions, num_general_fixing_revisions, perf_bugs, general_bugs, lines_deleted, lines_added



if __name__=='__main__':

    #data_dir = 'data'
    #project = 'elasticsearch'
    data_dir = sys.argv[1]
    project = sys.argv[2]
    source_dir = os.path.join('/home/gzhao/performance_bug_prediction/github_data_collection/projects', project)
    project_dir = os.path.join(data_dir, project)
    collect_changedfiles(project_dir, project)
    
    
    
    with open(os.path.join(data_dir, project, 'changedfiles_process_metrics.txt'), 'r') as reader:
        content = reader.read()
    
    changedfiles = content.split('\n')[:-1]
    
    dataset = pd.read_csv(os.path.join(data_dir, project, 'dataset_file_level.csv'))
    
    dataset['lines_deleted'] = -1
    dataset['lines_added'] = -1
    dataset['num_general_bugs'] = -1
    dataset['num_perf_bugs'] = -1
    dataset['num_revisions'] = -1
    dataset['num_general_fixing_revisions'] = -1
    dataset['num_perf_fixing_revisions'] = -1
    
    perf_fixing_commits = os.listdir(os.path.join('data', project, 'commits'))
    
    changeset_bug = {}

    
    # calculate num_revisions
    for row_index, row in dataset.iterrows():
        print(row_index)
        file_name = row.File
        file_name = file_name[file_name.index(project)+len(project)+1:].replace('/','_')
        revisions = [file for file in changedfiles if file.endswith(file_name)]
        num_perf_fixing_revisions, num_general_fixing_revisions, perf_bugs, general_bugs, lines_deleted, lines_added = metrics(revisions, source_dir)
        dataset.at[row_index, 'lines_deleted'] = lines_deleted
        dataset.at[row_index, 'lines_added'] = lines_added
        dataset.at[row_index, 'num_revisions'] = len(revisions)
        dataset.at[row_index, 'num_general_bugs'] = len(general_bugs)
        dataset.at[row_index, 'num_perf_bugs'] = len(perf_bugs)
        dataset.at[row_index, 'num_perf_fixing_revisions'] = num_perf_fixing_revisions
        dataset.at[row_index, 'num_general_fixing_revisions'] = num_general_fixing_revisions
    
    
    print('dataset.shape:', dataset.shape)
    print(dataset[dataset['num_revisions']>0].shape)    
    dataset.to_csv(os.path.join(data_dir, project, 'dataset_file_with_process.csv'), index=False)  
