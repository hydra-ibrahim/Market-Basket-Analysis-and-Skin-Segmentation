
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import joblib as jl
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# Create your views here.
class KNNView(APIView):

    def get(self, request, R, G, B):

        # Load the KNN model
        knn = jl.load('Backend/KNNAPI/static/KNNAPI/pickles/KNN2.pkl')

        data = pd.read_csv('Backend/KNNAPI/test/dataset.csv')
        
        X = data.drop('y', axis=1)
        y = data['y']
        
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        # Convert the url parameters to a DataFrame
        d = pd.DataFrame({'B':[R],'G':[G],'R':[B]})

        # Scale the DataFrame
        sample = scaler.transform(d)

        # Predict the result
        y_pred = knn.predict(sample)
        
        # Serialize JSON after converting NumPy array to list
        y_pred_json = pd.Series(y_pred).to_json(orient='values')

        return Response(y_pred_json, status=status.HTTP_200_OK)

    # Adjusts model parameter
    def post(self, request, k):

        data = pd.read_csv('Backend/KNNAPI/test/dataset.csv')
        
        X = data.drop('y', axis=1)
        y = data['y']
        
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        
        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y.values.ravel(), test_size=0.2)

        # Initialize KNN classifier
        knn = KNeighborsClassifier(n_neighbors=k, weights='distance')  # Set the number of neighbors (K)

        # Train the model
        knn.fit(X_train, y_train)

        # Save the model
        jl.dump(knn, 'Backend/KNNAPI/static/KNNAPI/pickles/KNN2.pkl')

        return Response(status=status.HTTP_201_CREATED)
