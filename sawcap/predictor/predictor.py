from sklearn import linear_model
import numpy as np
from config import BATCH_SIZE, NUM_RESOURCES

class Predictor:

    def __init__(self, database, algo):
        self.database = database
        self.algo = algo

    def get_prediction(self, cur_phase):
        # if no phase available
        if cur_phase == "":
            return [0] * NUM_RESOURCES
        
        # load prev1, prev2 and curr from database
        self._get_triplet_values()

        # if phase does not exist yet, return prev1
        if not self.database.check_phase_exists(cur_phase):
            return self.prev1_resource

        # if no model has been built yet, just use naive prediction
        if len(self.database.get_models_from_phase(cur_phase)) == 0:
            return self.prev1_resource
        else:
            return self._prediction_helper(cur_phase)
    
    def update_ml_model(self, phase_string):
        # do not build model for an idle phase (no trace string) or if phase doesn't exist
        if phase_string == "" or not self.database.check_phase_exists(phase_string):
            return
        
        if len(self.database.get_data_from_phase(phase_string)) == BATCH_SIZE:
            # load prev1, prev2 and curr from database
            self._get_triplet_values()

            self._update_helper(phase_string)

            # reset the profiling data for current phase
            self.database.flush_data_from_phase(phase_string)

    def _get_triplet_values(self):
        self.prev2_resource = self.database.get_prev2_resource()
        self.prev1_resource = self.database.get_prev1_resource()
        self.curr_resource = self.database.get_curr_resource()

    def _predict_naive(self, cur_phase):
        return self.prev1_resource

    def _predict_individual_lasso(self, model, X):
        return model.predict(X)

    def _predict_lasso(self, cur_phase):
        # get the models.  Number of models should be the number of resources
        models = self.database.get_models_from_phase(cur_phase)
        if len(models) == 0:
            # no models so far, just return the naive result
            return self.prev1_resource
        else:
            # make prediction for each model
            try:
                predictions = []
                for i in range(len(models)):
                    pred = self._predict_individual_lasso(models[i], [[self.prev2_resource[i], self.prev1_resource[i]]])
                    # prediction is returned as a 1D Array
                    predictions.append(float(pred[0]))
                return predictions
            except Exception as e:
                print("[Probably not fitted model] ", e)
                return self.prev1_resource

    def _prediction_helper(self, cur_phase):
        if self.algo == "simple":
            return self._predict_naive(cur_phase)
        elif self.algo == "lasso":
            return self._predict_lasso(cur_phase)
    
    def _add_models(self, cur_phase):
        # intiialize LASSO models with the number of resources
        # print("*** Number of resources during model init ", len(cur_res))
        models = []
        for res in range(NUM_RESOURCES):
            models.append(linear_model.Lasso(alpha=0.1))
        self.database.add_models_to_phase(models, cur_phase)

    def _format_data(self, cur_phase, res_index):
        # format data from the temporary profile collected
        temp_data = self.database.get_data_from_phase(cur_phase)
        X = []
        Y = []

        for i in range(BATCH_SIZE):
            # loop through all the profiling points
            X.append([temp_data[i][res_index][0], temp_data[i][res_index][1]])
            Y.append(temp_data[i][res_index][2])

        return X, Y

    def _generate_synthetic(self, cur_phase, model):
        # generates synthetic data based on existing model so that we can
        # retrieve old model info
        temp_data = self.database.get_data_from_phase(cur_phase)
        num_data_points = 5
        X = []
        Y = []

        for i in range(num_data_points):
            X.append([np.random.randint(low=1, high=100, size=1)[0],
                      np.random.randint(low=1, high=100, size=1)[0]])

        Y = model.predict(X)
        return X, Y

    def _update_lasso(self, cur_phase):
        models = self.database.get_models_from_phase(cur_phase)
        if len(models) == 0:
            self._add_models(cur_phase)

        for i in range(NUM_RESOURCES):
            X, Y = self._format_data(cur_phase, i)
            model = self.database.get_models_from_phase(cur_phase)[i]

            tempX = []
            tempY = []

            try:
                tempX, tempY = self._generate_synthetic(cur_phase, model)
            except Exception as e:
                print("[Probably not fitted model] ", e)

            X.extend(tempX)
            Y.extend(tempY)

            model.fit(X, Y)
            self.database.get_models_from_phase(cur_phase)[i] = model

    def _update_helper(self, cur_phase):
        if self.algo == "lasso":
            self._update_lasso(cur_phase)