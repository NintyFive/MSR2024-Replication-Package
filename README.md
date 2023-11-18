# Enhancing Performance Bug Prediction Using Performance Code Metrics #

**Requirements**
* Python 3.5 or newer
* Library [pandas](https://pandas.pydata.org) library 0.23.1 or newer
* Library [sklearn](https://scikit-learn.org/stable) library 0.22.2 or newer
* Library [scipy](https://www.scipy.org) library 1.4.1 or newer
* Library [numpy](https://numpy.org) library 1.18.5 or newer
* Library [xgboost](https://xgboost.readthedocs.io/en/latest/get_started.html) library 1.1.1 or newer

**Files description**
*  **data** 
	*  **experiment_dataset** folder contains the labeled dataset of clean and buggy files that have performance bugs in the 80 studied GitHub projects. Each project has a separate folder.
	* **issue_reports** folder contains the sample data of the non-performance bug reports and performance bug reports.
*  **python_scripts** folder contains the scripts for evaluating the performance machine learning algorithms and calculating the effects of metrics. 
    * **algorithms_comparison.py** contains the script for training and evaluating the performance of machine learning algorithms for predicting performance bugs.
    * **metrics_effects** contains the script for calculating the effects of metrics on the performance bug prediction models.
*  **samples_of_prediction** folder contains the samples of predicted performance bug files by the trained Random Forest models.
    * **sample_of_predicted_files.csv** contains the unlabeled 340 samples selected from the 80 experiment projects.
    * **sample_of_predicted_files_labeled.xlsx** contains the manually labeled samples.
    * **samples** contains the performance bug fixing commit information for each predicted performance bug. The authors based on these information to manually label if a predicted performance bugs file is true positive or false positive.
