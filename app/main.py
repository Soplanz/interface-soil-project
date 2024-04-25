from fastapi import FastAPI, Request
from datetime import datetime
from app.utils import get_nearest_hour, get_today_info

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Iterator, List

import pickle
import os
import asyncio
import logging
import random
import sys
import json

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
random.seed()  
app.mount("/static", StaticFiles(directory="app/static"), name="static")

data_store = {
    'suction_sensor1':[], 
    'suction_sensor2':[], 
    'suction_sensor3':[], 
    'suction_sensor4':[], 
    'suction_sensor5':[],
    'moisture_sensor1':[], 
    'moisture_sensor2':[], 
    'moisture_sensor3':[], 
    'moisture_sensor4':[], 
    'moisture_sensor5':[],
}

MAX_DATA_POINTS = 1

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {'request':request})


@app.get("/moisture", response_class=HTMLResponse)
async def moisture_view(request: Request):
    return templates.TemplateResponse("index_moisture.html", {'request': request})


@app.get("/suction", response_class=HTMLResponse)
async def suction_(request: Request):
    return templates.TemplateResponse("index_suction.html", {'request': request})


@app.get("/plot/{sensor_id}", response_class=HTMLResponse)
async def suction_(request: Request, sensor_id: str):
    return templates.TemplateResponse("index_plot.html", {'request': request, 'sensor_id': sensor_id})


@app.post("/predict/moisture/{latitude}/{longitude}")
async def predict_moisture(latitude: str, longitude: str):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    target_hour  = get_nearest_hour(current_time)
    
    api_dict, feature_cols = get_today_info(latitude=latitude, longitude=longitude)
    index = api_dict['timestamp'].index(target_hour)

    features_data = {}
    features_data['longitude'] = longitude
    features_data['latitude']  = latitude

    features = [longitude, latitude]
    for col in feature_cols:
        features_data[col] = api_dict[col][index]
        features.append(features_data[col])

    with open('app/moisture_model.pkl', 'rb') as f:
        model = pickle.load(f)
        features_data['predicted_moisture'] = model.predict([features])[0]
    
    return features_data

@app.post("/predict/suction/{latitude}/{longitude}")
async def predict_suction(latitude: str, longitude: str):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    target_hour  = get_nearest_hour(current_time)
    
    api_dict, feature_cols = get_today_info(latitude=latitude, longitude=longitude)
    index = api_dict['timestamp'].index(target_hour)

    features_data = {}
    features_data['longitude'] = longitude
    features_data['latitude']  = latitude

    features = [longitude, latitude]
    for col in feature_cols:
        features_data[col] = api_dict[col][index]
        features.append(features_data[col])

    with open('app/suction_model.pkl', 'rb') as f:
        model = pickle.load(f)
        features_data['predicted_suction'] = model.predict([features])[0]
    
    return features_data

@app.get("/chart-data/{sensor_id}")
async def chart_data(request: Request, sensor_id:str) -> StreamingResponse:
    response = StreamingResponse(generate_client_data(sensor_id), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.post("/receive-data/{sensor_id}")
async def receive_data(sensor_id:str, data: dict):
    """
    Receive data sent via POST request and store it.
    """

    # Add sensor ID to the data payload
    data_store[sensor_id].insert(0, data)
    logger.info("Received data: %s", data)
    
    # Ensure that data_store does not exceed the maximum number of data points
    if len(data_store[sensor_id]) > MAX_DATA_POINTS:
        data_store[sensor_id].pop()  # Remove the oldest data point from the end of the list

    return {"message": "Data received successfully"}

async def generate_client_data(sensor_id=None) -> Iterator[str]:
    """
    Generates data stored in the data_store list.
    """
    while True:
        try:
            if len(data_store[sensor_id]) > 0:
                data = data_store[sensor_id][0]   
                timestamp = data.get("timestamp")
                humidity = data.get("humidity")
                pressure = data.get("pressure")
                yield f"data:{{\"time\": \"{timestamp}\", \"moisture\": {humidity}, \"suction\": {pressure}}}\n\n"
                await asyncio.sleep(2)
        except Exception as e:
            logger.error("Error processing data: %s", e)
            break
