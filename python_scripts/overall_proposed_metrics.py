import os
import sys
import time
import subprocess

if __name__=='__main__':
    # all projects in the data dir
    data_dir = 'data'
    
    while(1):
        projects = os.listdir(data_dir)
        
        # projects that have calculated the proposed anti-pattern metrics
        
        with open('finished_projects.txt') as reader:
            content = reader.read()
        finished_projects = content.split('\n')[:-1]
        
        # projects need to calculate the proposed anti-pattern metrics
        remain_projects = set(projects) - set(finished_projects)
        
        for project in remain_projects:
            print(project)
        
            # calculate proposed metrics for the project
            subprocess.run(["python3.5", "calculate_proposed_metrics.py", data_dir, project])
        
            # record the project as a finished project
            with open('finished_projects.txt', 'a') as writer:
                content = writer.write(project+'\n')
        time.sleep(60*5)
    

