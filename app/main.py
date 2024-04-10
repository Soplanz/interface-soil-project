from fastapi import FastAPI, Request
from datetime import datetime
from app.utils import get_nearest_hour, get_today_info

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

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
random.seed()  
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {'request':request})


@app.get("/moisture", response_class=HTMLResponse)
async def moisture_view(request: Request):
    return templates.TemplateResponse("index_moisture.html", {'request': request})


@app.get("/suction", response_class=HTMLResponse)
async def suction_(request: Request):
    return templates.TemplateResponse("index_suction.html", {'request': request})


@app.get("/plot", response_class=HTMLResponse)
async def suction_(request: Request):
    return templates.TemplateResponse("index_plot.html", {'request': request})


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

async def generate_random_data(request: Request) -> Iterator[str]:
    """
    Generates random value between 0 and 100

    :return: String containing current timestamp (YYYY-mm-dd HH:MM:SS) and randomly generated data.
    """
    client_ip = request.client.host

    logger.info("Client %s connected", client_ip)

    while True:
        json_data = json.dumps(
            {
                "time": datetime.now().strftime("%Y%m%d%H%M"),
                "value": random.random() * 100,
            }
        )
        yield f"data:{json_data}\n\n"
        await asyncio.sleep(2)


@app.get("/chart-data")
async def chart_data(request: Request) -> StreamingResponse:
    response = StreamingResponse(generate_random_data(request), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

