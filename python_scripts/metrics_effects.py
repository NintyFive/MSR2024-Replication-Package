#!/usr/bin/env python
# coding: utf-8

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn import metrics
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
import os

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

def metric_importance_score(project, features, dataset, N, algorithm, param_dist, results_df):
    correlated_features = get_correlated_features(dataset)
    test_dataset = dataset.drop(labels=correlated_features, axis=1, inplace=False)
    
    X = test_dataset.drop(['File', 'label'], 1)
    y = test_dataset['label']
    
    for i in range(N):
        print(i)
        scores = {}
        scores['project_iteration'] = project + '_' + str(i)
        sample_index = resample(dataset.index.values)
        
        train_x = X.loc[sample_index]
        train_y = y.loc[sample_index]
        
        test_index = np.array(list(set(dataset.index.values) - set(sample_index)))
        
        test_x = X.loc[test_index]
        test_y = y.loc[test_index]
        
        if all(test_y==0) or all(train_y==0):
            continue
        clean_auc = train_test_model(train_x, train_y, test_x, test_y, algorithm, param_dist)   
        #print(clean_auc)
        scores['clean_auc'] = clean_auc
        for feature in features:
            if feature in train_x.columns:
                permuted_train_x = train_x.copy()
                permuted_test_x = test_x.copy()
                permuted_train_x[feature] = np.random.permutation(permuted_train_x[feature])
                permuted_test_x[feature] = np.random.permutation(permuted_test_x[feature])
                permuted_auc = train_test_model(permuted_train_x, train_y, permuted_test_x, test_y, algorithm, param_dist)
                #print(permuted_auc)
                scores[feature] = permuted_auc
            else:
                permuted_auc = 0
                scores[feature] = permuted_auc
        results_df = results_df.append(scores, ignore_index=True)
    return results_df




algo = {}
algo['RF'] = RandomForestClassifier
algo_param_dist = {}
algo_param_dist['RF'] = {'n_estimators':500, 'max_samples': 0.2, 'n_jobs': 2, 
              'criterion':'entropy','max_features':0.2,
              'min_samples_leaf':1, 'min_samples_split':2,
              'random_state':0, 'class_weight':'balanced_subsample',
              'verbose':0 }

data_dir = '../data/experiment_dataset'
dataset = pd.read_csv(os.path.join(data_dir, 'elasticsearch', 'dataset.csv'))

features = dataset.columns
features = features.drop(['File', 'label'], 1)
columns = features.insert(0, 'clean_auc')
columns = columns.insert(0, 'project_iteration')


results_df = pd.DataFrame(columns=columns)

projects = os.listdir(data_dir)

N = 100
for project in projects:
    if os.path.exists(os.path.join(data_dir, project, 'dataset.csv')):
        dataset = pd.read_csv(os.path.join(data_dir, project, 'dataset.csv'))
        if dataset[dataset['label']==1].shape[0] >= 10:
            print(project)
            results_df = metric_importance_score(project, features, dataset, N, algo['RF'], algo_param_dist['RF'], results_df)


importances_df = pd.DataFrame(columns=['metric', 'loss_of_auc'])
for index, row in results_df.iterrows():
    auc = row['clean_auc']
    for feature in features:
        if row[feature] == 0:
            loss_of_auc = 0
        else:
            loss_of_auc =  auc - row[feature]
        if loss_of_auc >=0 or feature == 'CountInput':
            importances_df = importances_df.append({'metric':feature, 'loss_of_auc':loss_of_auc}, ignore_index=True)


importances_df.to_csv('importances_of_metrics_new.csv', index=False)
