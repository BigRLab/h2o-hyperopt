# Example script for using the DLEOptimizer in h2ohyperopt

import h2o
import sys
sys.path.append('')
import h2ohyperopt

# Initializing H2O
h2o.init()


# Function for preprocessing the data
def data():
    """
    Function to process the example titanic dataset.
    Train-Valid-Test split is 60%, 20% and 20% respectively.
    Output
    ---------------------
    trainFr: Training H2OFrame.
    testFr: Test H2OFrame.
    validFr: Validation H2OFrame.
    predictors: List of predictor columns for the Training frame.
    response: String defining the response column for Training frame.
    """
    titanic_df = h2o.import_file(path="https://s3.amazonaws.com/h2o-public-test-data/smalldata/gbm_test/titanic.csv")

    # Basic preprocessing
    # columns_to_be_used - List of columns which are used in the training/test
    # data
    # columns_to_factorize - List of columns with categorical variables
    columns_to_be_used = ['pclass', 'age', 'sex', 'sibsp', 'parch', 'ticket',
                          'embarked', 'fare', 'survived']
    columns_to_factorize = ['pclass', 'sex', 'sibsp', 'embarked', 'survived']
    # Factorizing the columns in the columns_to_factorize list
    for col in columns_to_factorize:
        titanic_df[col] = titanic_df[col].asfactor()
    # Selecting only the columns we need
    titanic_frame = titanic_df[columns_to_be_used]
    trainFr, testFr, validFr = titanic_frame.split_frame([0.6, 0.2],
                                                         seed=1234)
    predictors = trainFr.names[:]
    # Removing the response column from the list of predictors
    predictors.remove('survived')
    response = 'survived'
    return trainFr, testFr, validFr, predictors, response

def model():
    # Specfiying a DLE model
    dleModel = h2ohyperopt.DLEOptimizer(metric='auc')
    # Selecting parameters to optimize on
    dleModel.select_optimization_parameters({'epsilon': 'Default',
                                             'adaptive_rate': True,
                                             'hidden': ('choice', [[10, 20], [30, 40]]),
                                             'nfolds': 7})

    # Specifying a GBM model
    gbmModel = h2ohyperopt.GBMOptimizer(metric='auc')
    # Selecting parameters to optimize on
    gbmModel.select_optimization_parameters({'col_sample_rate': 'Default',
                                             'ntrees': 200,
                                             'learn_rate': ('uniform',(0.05, 0.2)),
                                             'nfolds': 7})

    # Using the data() function to get required data
    trainFr, testFr, validFr, predictors, response = data()

    # Specifying a ModelDocker object
    docker = h2ohyperopt.ModelDocker([dleModel, gbmModel], 'auc')
    docker.start_optimization(num_evals=10, trainingFr=trainFr,
                              validationFr=validFr, response=response,
                              predictors=predictors)

    docker.best_in_class_ensembles(numModels=2)
    print "Best Model Scores"
    print docker.best_model_scores()
    print "Test frame score: ", docker.best_model_test_scores(testFr)
    print "Best Model Parameters"
    print "------------------------"
    print docker.best_model_parameters()
    ensemble_test_score = docker.score_ensemble(testFr)
    print "Docker Ensemble Test score :", ensemble_test_score


if __name__ == '__main__':

    model()
