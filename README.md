# interface-soil-project
Repository for final task about the project from civil engineering.

* utils.py => for preprocessing the data used for machine learning prediction
* main.py  => the general workflow of the website including the data streaming mechanism and the url for the whole page.

Step by step to add sensor to the website:
1. add sensor coordinate in this code "index_<metric>.html"
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
```data_store = {
    'sensor1':[], 
    'sensor2':[], 
    'sensor3':[], 
    'sensor4':[], 
    'sensor5':[],
    'sensor6':[], 
}
```

Step by step on updating the model (if enchanced)
1. Name model for suction as 'suction_model.pkl' and moisture model as 'moisture_model.pkl'
2. Edit needed feature (if needed to match the requirements of the model) for prediction in main.py, 'predict_moisture(args)' for moisture and 'predict_suction(args)' for suction