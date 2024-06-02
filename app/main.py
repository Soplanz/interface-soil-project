from fastapi import FastAPI, Request
from datetime import datetime
from app.utils import get_nearest_hour, get_today_info, kriging_calculation

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Iterator

import pickle
import os
import asyncio
import logging
import random
import sys
import json
import pytz

from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
random.seed()  
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# If any sensor added, add the sensor id here
data_store = {
    'sensor1':[], 
    'sensor2':[], 
    'sensor3':[], 
    'sensor4':[], 
    'sensor5':[],
    'sensor6':[], 
}

MAX_DATA_POINTS = 1
BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
GROUP_ID = os.getenv("GROUP_ID")
AUTO_OFFSET_RESET = os.getenv("AUTO_OFFSET_RESET")


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
    current_time = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
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
    
    features_data['predicted_moisture_kriging'] = kriging_calculation(data_store, 'humidity', latitude, longitude)
    return features_data

@app.post("/predict/suction/{latitude}/{longitude}")
async def predict_suction(latitude: str, longitude: str):
    current_time = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
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
    
    features_data['predicted_suction_kriging'] = kriging_calculation(data_store, 'pressure', latitude, longitude)
    return features_data

@app.get("/chart-data/{sensor_id}")
async def chart_data(request: Request, sensor_id:str) -> StreamingResponse:
    response = StreamingResponse(generate_client_data(sensor_id), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

# Define Kafka consumer task
async def kafka_consumer_task():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVER,
        group_id=GROUP_ID,
        auto_offset_reset=AUTO_OFFSET_RESET,
        value_deserializer=lambda m: json.loads(m.decode('ascii')),
        loop=asyncio.get_running_loop()
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                data = message.value
                process_data(data)
            except Exception as e:
                logger.error("Error processing Kafka message: %s", e)
    finally:
        await consumer.stop()

def process_data(data):
    logger.info("Received data for data processing: %s", data)
    sensor_id = data.get("sensor_id")
    data_store[sensor_id].insert(0, data)

def process_data_for_sensor(data):
    logger.info("Received data: %s", data)
    sensor_id = data.get("sensor_id")
    if len(data_store[sensor_id]) > MAX_DATA_POINTS:
        data_store[sensor_id].pop() 
    
# Start Kafka consumer task on application startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer_task())

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
                await asyncio.sleep(1)
        except Exception as e:
            logger.error("Error processing data: %s", e)
            break
