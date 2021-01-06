from sklearn import linear_model
import numpy as np

class Predictor:
    
    def __init__(self):
        self.num_resources = 2  # currently support CPU and memory
        self.batch_size = 3     # batch size for model update
        self.algo = "lasso"     # algorithm used for predictions

        # we use the resource usage of prev 2 phases for building the machine learning
        # model.  These are the meta-inputs
        self.prev1_resource = []
        self.prev2_resource = []

        # store resources
        self.predicted_resources = []
        self.actual_resources = []

    def get_algo(self):
        return self.algo

    def set_algo(self, algo):
        self.algo = algo

    def get_actual_resources(self):
        return self.actual_resources

    def get_predicted_resources(self):
        return self.predicted_resources

    def get_prev1_resource(self):
        return self.prev1_resource
    
    def set_prev1_resource(self, resouce):
        self.prev1_resource = resouce

    def get_prev2_resource(self):
        return self.prev2_resource

    def set_prev2_resource(self, resource):
        self.prev2_resource = resource

    def predict_naive(self, cur_phase):
        return self.prev1_resource

    def predict_individual_lasso(self, model, X):
        return model.predict(X)

    def predict_individual_agg(self, model, X):
        return model.predict(X)

    def predict_lasso(self, phase_database, cur_phase):
        # get the models.  Number of models should be the number of resources
        models = phase_database[cur_phase]["models"]
        if len(models) == 0:
            # no models so far, just return the naive result
            return self.prev1_resource
        else:
            # make prediction for each model
            try:
                predictions = []
                for i in range(len(models)):
                    pred = predict_individual_lasso(models[i], [[self.prev2_resource[i], self.prev1_resource[i]]])
                    # prediction is returned as a 1D Array
                    predictions.append(float(pred[0]))
                return predictions
            except Exception as e:
                print("[Probably not fitted model] ", e)
                return self.prev1_resource

    def predict_agg(self, phase_database, cur_phase):
        # get the models.  Number of models should be the number of resources
        models = phase_database[cur_phase]["models"]
        if len(models) == 0:
            # no models so far, just return the naive result
            return self.prev1_resource
        else:
            # make prediction for each model
            try:
                predictions = []
                for i in range(len(models)):
                    pred = models[i]
                    # prediction is returned as a 1D Array
                    predictions.append(pred)
                # check if something went wrong
                if any(predictions):
                    return predictions
                else:
                    return self.prev1_resource
            except Exception as e:
                print("[Probably not fitted model]", e)
                return self.prev1_resource

    def prediction_helper(self, phase_database, cur_phase):
        if self.algo == "simple":
            return self.predict_naive(cur_phase)
        elif self.algo == "lasso":
            return self.predict_lasso(phase_database, cur_phase)
        elif self.algo == "agg":
            return self.predict_agg(phase_database, cur_phase)
    
    def get_prediction(self, phase_database, cur_phase):
        # if no phase available
        if cur_phase == "":
            # print(" Empty current phase")
            return [0] * self.num_resources
        # if not there yet
        if cur_phase not in phase_database:
            # print(" Not in Phase DB yet")
            return self.prev1_resource, "unseen"
        # print("Existing phase in DB")
        # if no model has been built yet, just use naive prediction
        if len(phase_database[cur_phase]["models"]) == 0:
            return self.prev1_resource, "seen"
        else:
            return prediction_helper(cur_phase), "seen"

    def add_models(self, phase_database, cur_phase, cur_res):
        # intiialize LASSO models with the number of resources
        # print("*** Number of resources during model init ", len(cur_res))
        for res in cur_res:
            if self.algo == 'lasso':
                phase_database[cur_phase]["models"].append(linear_model.Lasso(alpha=0.1))
            elif self.algo == 'agg':
                phase_database[cur_phase]["models"].append(0)

    def format_data(self, phase_database, cur_phase, res_index):
        # format data from the temporary profile collected
        # res_index tells the resource we are modeling for e.g. CPU or memory
        temp_data = phase_database[cur_phase]["temp_data"]
        X = []
        Y = []

        for i in range(self.batch_size):
            # loop through all the profiling points
            X.append([temp_data[i][res_index][0], temp_data[i][res_index][1]])
            Y.append(temp_data[i][res_index][2])

        return X, Y

    def generate_synthetic(self, phase_database, cur_phase, model):
        # generates synthetic data based on existing model so that we can
        # retrieve old model info
        temp_data = phase_database[cur_phase]["temp_data"]
        num_data_points = 5
        X = []
        Y = []

        for i in range(num_data_points):
            X.append([np.random.randint(low=1, high=100, size=1)[0],
                      np.random.randint(low=1, high=100, size=1)[0]])

        Y = model.predict(X)
        return X, Y

    def update_lasso(self, phase_database, cur_phase):
        # update using the batch of data
        # do it for individual resources

        for i in range(len(self.prev1_resource)):
            X, Y = self.format_data(phase_database, cur_phase, i)
            print(X, Y)
            
            model = phase_database[cur_phase]["models"][i]
            
            tempX = []
            tempY = []

            try:
                tempX, tempY = self.generate_synthetic(phase_database, cur_phase, model)
            except Exception as e:
                print("[Probably not fitted model] ", e)

            X.extend(tempX)
            Y.extend(tempY)

            model.fit(X, Y)
            phase_database[cur_phase]["models"][i] = model

    def update_agg(self, phase_database, cur_phase):
        # update using the batch of data
        # do it for individual resources

        for i in range(len(self.prev1_resource)):
            X, Y = format_data(phase_database, cur_phase, i)

            flatten = lambda l: [item for sublist in l for item in sublist]
            X = flatten(X)

            # Aggregate with previous aggregate stored
            X.append(phase_database[cur_phase]["models"][i])
            phase_database[cur_phase]["models"][i] = np.average(X)

    def update_helper(self, phase_database, cur_phase):
        # update ML model for the batch collected
        if self.algo == "lasso":
            self.update_lasso(phase_database, cur_phase)
        elif self.algo == "simple":
            pass
        elif self.algo == "agg":
            self.update_agg(phase_database, cur_phase)

    def update_ml_model(self, phase_database, phase_string):
        # do not build model for an idle phase (no trace string)
        if phase_string == "":
            return

        print("updating the model", hash(phase_string))
        self.update_helper(phase_database, phase_string)

        # reset the profiling data
        phase_database[phase_string]["temp_data"] = []

    def mean_absolute_percentage_error(self, y_true, y_pred):
        # replace 0 with a small number to avoid div by zero
        y_true = [i if i != 0 else 0.001 for i in y_true]
        y_pred= [i if i != 0 else 0.001 for i in y_pred]

        y_true, y_pred = np.array(y_true), np.array(y_pred)
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    def SMAPE(self, y_true, y_pred):
        y_true, y_pred = np.array(y_true), np.array(y_pred) # convert to numpy arrays
        return np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100
        