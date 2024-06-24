# interface-soil-project
Repository for final task about the project from civil engineering.

Video usage tutorial: https://youtu.be/k7o3h9kNNbA

* utils.py : for preprocessing the data used for machine learning prediction
* main.py  : the general workflow of the website including the data streaming mechanism and the url for the whole page.

## Open Source API:
https://open-meteo.com/en/docs/

## Step by step to add sensor to the website:
1. add sensor coordinate in this code ("index_moisture.html" for moisture and "index_suction.html" for suction")
 ```var markerCoordinates = [
        {id: 'sensor1', coordinates: [-6.3643444, 106.8290695]},
        {id: 'sensor2', coordinates: [-6.3653083, 106.8246415]},
        {id: 'sensor3', coordinates: [-6.3651944, 106.8311499]},
        {id: 'sensor4', coordinates: [-6.367975, 106.830208]},
        {id: 'sensor5', coordinates: [-6.3705264, 106.8268372]},
        {id: 'sensor6', coordinates: [-6.3607737, 106.8265036]},
    ];
```

2. add sensor list to keep the temporary streamed data in this code "main.py"
```
data_store = {
    'sensor1':[], 
    'sensor2':[], 
    'sensor3':[], 
    'sensor4':[], 
    'sensor5':[],
    'sensor6':[], 
}
```

## Step by step on updating the model (if enchanced)
1. Name model for suction as 'suction_model.pkl' and moisture model as 'moisture_model.pkl'

2. Edit needed feature (if needed to match the requirements of the model) for prediction in main.py, 'predict_moisture(args)' for moisture and 'predict_suction(args)' for suction
```
@app.post("/predict/moisture/{latitude}/{longitude}")
async def predict_moisture(latitude: str, longitude: str):
    current_time = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%Y%m%d%H%M%S")
    target_hour  = get_nearest_hour(current_time)
    
    api_dict, feature_cols = get_today_info(latitude=latitude, longitude=longitude)
    index = api_dict['timestamp'].index(target_hour)

    features_data = {}
    features_data['longitude'] = longitude
    features_data['latitude']  = latitude

    # You can filter the feature here
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

    # You can filter the feature here
    features = [longitude, latitude]
    for col in feature_cols:
        features_data[col] = api_dict[col][index]
        features.append(features_data[col])

    with open('app/suction_model.pkl', 'rb') as f:
        model = pickle.load(f)
        features_data['predicted_suction'] = model.predict([features])[0]
    
    features_data['predicted_suction_kriging'] = kriging_calculation(data_store, 'pressure', latitude, longitude)
    return features_data
```
