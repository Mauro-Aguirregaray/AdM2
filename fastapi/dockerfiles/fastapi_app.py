import pickle
import boto3
import mlflow

import pandas as pd

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


def load_model(model_name: str, alias: str):
    """
    Load a trained model and associated data dictionary.

    This function attempts to load a trained model specified by its name and alias. If the model is not found in the
    MLflow registry, it loads the default model from a file. Additionally, it loads information about the ETL pipeline
    from an S3 bucket. If the data dictionary is not found in the S3 bucket, it loads it from a local file.

    :param model_name: The name of the model.
    :param alias: The alias of the model version.
    :return: A tuple containing the loaded model, its version, and the data dictionary.
    """

    try:
        # Load the trained model from MLflow
        mlflow.set_tracking_uri('http://mlflow:5005')
        client_mlflow = mlflow.MlflowClient()

        model_data_mlflow = client_mlflow.get_model_version_by_alias(model_name, alias)
        model_ml = mlflow.sklearn.load_model(model_data_mlflow.source)
        version_model_ml = int(model_data_mlflow.version)
        print(f'Modelo cargado exitosamente: Versión {version_model_ml}')
    except MlflowException as e:
        print(f'Error al conectar a MLflow: {e}')
    except Exception as e:
        print(f'Error al cargar el modelo: {e}')

    try:
        # Descargar el StandardScaler desde S3
        s3 = boto3.client('s3')
        bucket_name = 'data'
        scaler_filename = '/scalers/scaler_X.pkl'
        response = s3.get_object(Bucket=bucket_name, Key=scaler_filename)
        scaler_data = response['Body'].read()

        # Deserializar el objeto StandardScaler
        scaler_X = pickle.loads(scaler_data)

        scaler_filename = '/scalers/scaler_y.pkl'
        response = s3.get_object(Bucket=bucket_name, Key=scaler_filename)
        scaler_data = response['Body'].read()

        # Deserializar el objeto StandardScaler
        scaler_y = pickle.loads(scaler_data)

        data_dictionary = {
            'scaler_X': scaler_X,
            'scaler_y': scaler_y
        }
    except:
        print('Informacion de estandarizado no encontrada')
        data_dictionary = {}

    return model_ml, version_model_ml, data_dictionary


# Definir el modelo de entrada
class ModelInput(BaseModel):
    expenses_amount: float
    total_mts: float
    covered_mts: float
    rooms: int
    bedrooms: int
    bathrooms: int
    garages: int
    antique: int


# Load the model before start
model, version_model, data_dict = load_model("precio_propiedades_model_prod", "prod")


app = FastAPI()


@app.get("/")
async def read_root():
    """
    Root endpoint of the Heart Disease Detector API.

    This endpoint returns a JSON response with a welcome message to indicate that the API is running.
    """
    return JSONResponse(content=jsonable_encoder({"message": "Bienvenidos a la API para predecir el precio de las propiedades de CABA"}))


# Definir la ruta para predicciones
@app.post("/predict/")
async def predict(input_data: ModelInput):
    # Convertir los datos de entrada a un DataFrame de pandas
    df = pd.DataFrame([input_data.dict()])

    scaler_X = data_dict['scaler_X']
    scaler_y = data_dict['scaler_y']

    df = scaler_X.transform(df)

    # Hacer la predicción usando el modelo cargado desde MLflow
    prediction = model.predict(df)

    unstandarize_prediction = float(scaler_y.inverse_transform(prediction.reshape(-1, 1))[0][0])

    # Retornar el resultado como JSON
    return {"prediction": round(unstandarize_prediction,2)}