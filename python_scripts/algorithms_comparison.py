#!/usr/bin/env python
# coding: utf-8

# In[2]:


from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn import metrics
from sklearn.utils import resample
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import ComplementNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from scipy import stats
import pandas as pd
import numpy as np
import os
import xgboost as xgb

def get_correlated_features(dataset):
    correlation_matrix = dataset.corr()
    correlated_features = set()
    for i in range(len(correlation_matrix.columns)):
        for j in range(i):
            if abs(correlation_matrix.iloc[i, j]) > 0.7:
                colname = correlation_matrix.columns[min(i,j)]
                #print('(', correlation_matrix.columns[min(i,j)], ',', correlation_matrix.columns[max(i,j)], ')')
                correlated_features.add(colname)
    return correlated_features

def train_test_model(train_x, train_y, test_x, test_y, algorithm, param_dist):
    sc = MinMaxScaler()
    train_x = sc.fit_transform(train_x)
    test_x = sc.transform(test_x)
    clf = algorithm(**param_dist)
    
    clf.fit(train_x, train_y)
    if hasattr(clf, "predict_proba"):
        probs = clf.predict_proba(test_x)
        prob_pos = probs[:,1]
    else:  # use decision function
        prob_pos = clf.decision_function(test_x)
        prob_pos =  (prob_pos - prob_pos.min()) / (prob_pos.max() - prob_pos.min())
    
    
    fpr, tpr, thresholds = metrics.roc_curve(test_y, prob_pos, pos_label=1)
    auc = metrics.auc(fpr, tpr)
    return auc

def out_of_sample_evaluation(dataset, N, algorithm, param_dist):
    # get rid of correlated features
    correlated_features = get_correlated_features(dataset)
    test_dataset = dataset.drop(labels=correlated_features, axis=1, inplace=False)
    
    X = test_dataset.drop(['File', 'label'], 1)
    y = test_dataset['label']
    
    scores = {}
    scores['test_roc_auc'] = []
    for i in range(N):
        sample_index = resample(dataset.index.values)
        
        train_x = X.loc[sample_index]
        train_y = y.loc[sample_index]
        
        test_index = np.array(list(set(dataset.index.values) - set(sample_index)))
        
        test_x = X.loc[test_index]
        test_y = y.loc[test_index]
        
        if all(test_y==0) or all(train_y==0):
            continue
            
        auc = train_test_model(train_x, train_y, test_x, test_y, algorithm, param_dist)   
        
        scores['test_roc_auc'].append(auc)
    return scores



proposed_features = ['num_if_inloop', 'num_loop_inif', 'num_nested_loop', 'num_nested_loop_incrit',
              'synchronization', 'thread', 'io_in_loop', 'database_in_loop', 'collection_in_loop',
              'io', 'database', 'collection', 'recursive']

algorithms = ['CNB', 'LR', 'DT', 'MLP', 'SVM', 'XGBoost', 'RF']

algo = {}
algo['CNB'] = ComplementNB
algo['LR'] = LogisticRegression
algo['DT'] = DecisionTreeClassifier
algo['MLP'] = MLPClassifier
algo['SVM'] = LinearSVC
algo['XGBoost'] = xgb.XGBClassifier
algo['RF'] = RandomForestClassifier


algo_param_dist = {}
algo_param_dist['CNB'] = {}
algo_param_dist['LR'] = {}
algo_param_dist['DT'] = {}
algo_param_dist['SVM'] = {}
algo_param_dist['MLP'] = {}
algo_param_dist['CNB'] = {'alpha':0.001}
algo_param_dist['LR'] = {'max_iter': 100, 'class_weight': 'balanced'}
algo_param_dist['DT'] = { 'criterion':'entropy','max_features':0.3, 'max_depth': 6,
                          'min_samples_leaf':1, 'min_samples_split':2,
                          'random_state':0, 'class_weight':'balanced'}
algo_param_dist['MLP'] = {'max_iter':200,
                          'hidden_layer_sizes':7,
                          'shuffle': False,
                          'learning_rate': 'adaptive'}
algo_param_dist['SVM'] = {'max_iter':1000, 'class_weight':'balanced'}
algo_param_dist['XGBoost'] =  {'objective':'binary:logistic', 'n_estimators':100, 'max_depth': 6, 'eta': 0.01, 
                               #'gamma':1, 
                               'min_child_weight':2,'max_delta_step':2,
                               'colsample_bytree':0.4, 'subsample':0.4,
                               'verbosity':1 }
algo_param_dist['RF'] = {'n_estimators':500, 'max_samples': 0.2, 'n_jobs': 2, 
              'criterion':'entropy','max_features':0.2,
              'min_samples_leaf':1, 'min_samples_split':2,
              'random_state':0, 'class_weight':'balanced_subsample',
              'verbose':0 }


results_df = pd.DataFrame(columns=['project', 'auc', 'algorithm_metric'])

data_dir = '../data/experiment_dataset'
projects = os.listdir(data_dir)
N = 100
for project in projects:
    print(project)
    if os.path.exists(os.path.join(data_dir, project, 'dataset.csv')):
        dataset = pd.read_csv(os.path.join(data_dir, project, 'dataset.csv'))
        for algorithm in algorithms:
            print(algorithm)
            all_metrics_scores = out_of_sample_evaluation(dataset, N, algo[algorithm], algo_param_dist[algorithm])
            row = {'project':project}
            row['auc'] = np.mean(all_metrics_scores['test_roc_auc'])
            row['algorithm_metric'] = algorithm + ' with_anti-pattern_metrics'
            results_df = results_df.append(row, ignore_index=True)
            
            remain_dataset = dataset.drop(labels=proposed_features, axis=1)
            defect_metrics_scores = out_of_sample_evaluation(remain_dataset, N, algo[algorithm], algo_param_dist[algorithm])
            row = {'project':project}
            row['auc'] = np.mean(defect_metrics_scores['test_roc_auc'])
            row['algorithm_metric'] = algorithm + ' without_anti-pattern_metrics'
            
            results_df = results_df.append(row, ignore_index=True)

results_df.to_csv('with_without_anti_pattern_metrics.csv', index=False)

