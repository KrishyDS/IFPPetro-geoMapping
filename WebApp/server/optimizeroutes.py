import sys
import numpy as np
import pandas as pd
import math 
import pulp
import itertools
import gmaps
import googlemaps
import matplotlib.pyplot as plt
import time
pd.options.mode.chained_assignment = None  # default='warn'

'''API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
gmaps.configure(api_key=API_KEY)
googlemaps = googlemaps.Client(key=API_KEY)'''

# customer count ('0' is depot) 
customer_count = 10

# the number of vehicle
vehicle_count = int(sys.argv[1])

# the capacity of vehicle
vehicle_capacity = int(sys.argv[2])

# fix random seed
np.random.seed(seed=779)

# set depot latitude and longitude
depot_latitude = 30.748817
depot_longitude = -67.985428

# make dataframe which contains vending machine location and demand
df = pd.DataFrame({"latitude":np.random.normal(depot_latitude, 0.007, customer_count), 
                   "longitude":np.random.normal(depot_longitude, 0.007, customer_count), 
                   "demand":np.random.randint(10, 20, customer_count)})


# set the depot as the center and make demand 0 ('0' = depot)
df.iloc[0,0] = depot_latitude
df.iloc[0,1] = depot_longitude
df.iloc[0,2] = 0

# function for plotting on google maps
def _plot_on_gmaps(_df):
    
    _marker_locations = []
    for i in range(len(_df)):
        _marker_locations.append((_df['latitude'].iloc[i],_df['longitude'].iloc[i]))
    
    _fig = gmaps.figure()
    _markers = gmaps.marker_layer(_marker_locations)
    _fig.add_layer(_markers)

    return _fig

# function for calculating distance between two pins
def _distance_calculator(_df):
    
    _distance_result = np.zeros((len(_df),len(_df)))
    _df['latitude-longitude'] = '0'
    for i in range(len(_df)):
        _df['latitude-longitude'].iloc[i] = str(_df.latitude[i]) + ',' + str(_df.longitude[i])
    
    for i in range(len(_df)):
        for j in range(len(_df)):
            
            # calculate distance of all pairs
            '''_google_maps_api_result = googlemaps.directions(_df['latitude-longitude'].iloc[i],
                                                            _df['latitude-longitude'].iloc[j],
                                                            mode = 'driving')'''
            # append distance to result list
            '''_distance_result[i][j] = _google_maps_api_result[0]['legs'][0]['distance']['value']'''
            _distance_result[i][j] = math.sqrt((_df.latitude[i] - _df.latitude[j])**2 + (_df.longitude[i] - _df.longitude[j])**2)
    
    return _distance_result

distance = _distance_calculator(df)
plot_result = _plot_on_gmaps(df)
plot_result


# solve with pulp
for vehicle_count in range(1,vehicle_count+1):
    
    # definition of LpProblem instance
    problem = pulp.LpProblem("CVRP", pulp.LpMinimize)


    # definition of variables which are 0/1
    x = [[[pulp.LpVariable("x%s_%s,%s"%(i,j,k), cat="Binary") if i != j else None for k in range(vehicle_count)]for j in range(customer_count)] for i in range(customer_count)]

    # add objective function
    problem += pulp.lpSum(distance[i][j] * x[i][j][k] if i != j else 0
                          for k in range(vehicle_count) 
                          for j in range(customer_count) 
                          for i in range (customer_count))

    # constraints
    # foluma (2)
    for j in range(1, customer_count):
        problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                              for i in range(customer_count) 
                              for k in range(vehicle_count)) == 1 

    # foluma (3)
    for k in range(vehicle_count):
        problem += pulp.lpSum(x[0][j][k] for j in range(1,customer_count)) == 1
        problem += pulp.lpSum(x[i][0][k] for i in range(1,customer_count)) == 1

    # foluma (4)
    for k in range(vehicle_count):
        for j in range(customer_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                                  for i in range(customer_count)) -  pulp.lpSum(x[j][i][k] for i in range(customer_count)) == 0

    #foluma (5)
    for k in range(vehicle_count):
        problem += pulp.lpSum(df.demand[j] * x[i][j][k] if i != j else 0 for i in range(customer_count) for j in range (1,customer_count)) <= vehicle_capacity 


    # fomula (6)
    subtours = []
    for i in range(2,customer_count):
         subtours += itertools.combinations(range(1,customer_count), i)

    for s in subtours:
        problem += pulp.lpSum(x[i][j][k] if i !=j else 0 for i, j in itertools.permutations(s,2) for k in range(vehicle_count)) <= len(s) - 1

    
    # print vehicle_count which needed for solving problem
    # print calculated minimum distance value
    if problem.solve(pulp.PULP_CBC_CMD(msg = 0)) == 1:

        ###### visualization : plotting with matplolib  ######
        plt.figure(figsize=(8,8))
        for i in range(customer_count):    
            if i == 0:
                plt.scatter(df.latitude[i], df.longitude[i], c='green', s=200)
                plt.text(df.latitude[i], df.longitude[i], "depot", fontsize=12)
            else:
                plt.scatter(df.latitude[i], df.longitude[i], c='orange', s=200)
                plt.text(df.latitude[i], df.longitude[i], str(df.demand[i]), fontsize=12)

        l = []
        for i in range(0, vehicle_count+1):
            l.append(tuple(np.random.choice(range(0, 2), size=3)))

        for k in range(vehicle_count):
            for i in range(customer_count):
                for j in range(customer_count):
                    if i != j and pulp.value(x[i][j][k]) == 1:
                        plt.plot([df.latitude[i], df.latitude[j]], [df.longitude[i], df.longitude[j]], c=l[k])
        
        plt.savefig("optimizedroutes.jpg")

        print('{','\"trucks\":', vehicle_count,",",'\"distance\":', pulp.value(problem.objective),'}')
        break

sys.stdout.flush()
        
        