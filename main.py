import folium
from folium.plugins import GroupedLayerControl
import json 
import math
import os
import glob
import requests


LOCATION_DATA = 'location_data.json' # Airports | Name | Coords | page
ROUTE_DATA = 'route_data.json'  # Year | Orig Aiport | Destination Airprot -> total passengers
START_PAGE = 'index.html'

def getGeoData(): # unused. can draw bounding boxes around states
    geo_json_data = requests.get(
    "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"
).json()
    return geo_json_data


def dist(miles): # folium works with meters, so converts mile value -> meter
    return 1609.34*miles


def load_json(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error: The file '{file_name}' does not contain valid JSON.")
        raise


def delete_old_html_files(folder):
    html_files = glob.glob(os.path.join(folder, "*.html"))
    for file_path in html_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Could not delete {file_path}: {e}")


def circleMaker(map,location=[0,0],radius=100,fill=True,stroke=False,fill_opacity=0.8,tooltip=None,popup=None,metric=False,repeat=False):
    if not metric:
        radius = dist(radius)



    folium.Circle(
        radius=radius,
        location=location,
        fill=fill,
        stroke=stroke,
        color='#3186cc',        # don't change color !! currenlty used to make hyperlinks
        fillColor='#3186cc',    
        fill_opacity=fill_opacity,
        tooltip=tooltip
    ).add_to(map)
    


def makeRedirects(map,data):

    js_code = f"""
    <script>
    // Store city data
    const cityData = {json.dumps(data)};
    // Function to add click handlers
    function addCircleClickHandlers() {{
        const paths = document.querySelectorAll('path');
        let circleIndex = 0;
        
        paths.forEach(function(path) {{
  
            // Check if this is one of our blue circles
            if (path.getAttribute('fill') === '#3186cc') {{ //TODO: Change color????
                path.style.cursor = 'pointer';
                
                // Get city name from our predefined order 
                // TODO: might want to change this to make going back easier / deselecting.
                const cityNames = Object.keys(cityData);
                if (circleIndex < cityNames.length) {{
                    const cityName = cityNames[circleIndex];
                    const page = cityData[cityName];
                    
                    path.addEventListener('click', function(e) {{
                        console.log('Navigating to:', page);
                        window.location.href = page;
                        e.stopPropagation();
                    }});
                    
                    circleIndex++;
                }}
            }}
        }});
        
        // If we didn't find all circles, try again
        if (circleIndex < Object.keys(cityData).length) {{
            setTimeout(addCircleClickHandlers, 500);
        }}
    }}
    
    // Initialize when page loads
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(addCircleClickHandlers, 1000);
    }});
    </script>
    """
    
    map.get_root().html.add_child(folium.Element(js_code))



def genArcCoords(start, end, num_points=100):
    lat1, lon1 = map(math.radians, start)
    lat2, lon2 = map(math.radians, end)

    delta = 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2)**2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2)**2
    ))

    if delta == 0:
        return [(start[0], start[1])] * num_points

    points = []
    for i in range(num_points):
        f = i / (num_points - 1)
        A = math.sin((1 - f) * delta) / math.sin(delta)
        B = math.sin(f * delta) / math.sin(delta)

        x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
        y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
        z = A * math.sin(lat1) + B * math.sin(lat2)

        new_lat = math.atan2(z, math.sqrt(x**2 + y**2))
        new_lon = math.atan2(y, x)
        points.append((math.degrees(new_lat), math.degrees(new_lon)))


    lons = [lon for _, lon in points]
    max_lon = max(lons)
    min_lon = min(lons)


    if max_lon - min_lon > 180:
        adjusted = []
        for lat, lon in points:
            if lon < 0:
                lon += 360
            adjusted.append((lat, lon))
        points = adjusted

    return points


def drawArc(map,start,end,num_points=100,color="#000000",weight=3):
  
    coords = getRepeatCoords(genArcCoords(start,end,num_points=100))

    for universe in coords:  # draw three times to make loop seemlessly
        folium.PolyLine(
        locations=universe,
        color=color,
        weight=weight,
        
        ).add_to(map)
    

def getRepeatCoords(coords):
    out = [coords] 

    for x in range(1,4):
        out.append( [[coord[0], coord[1]+360*x] for coord in coords]   )
        out.append( [[coord[0], coord[1]-360*x] for coord in coords]   )
    return out
    


#  deleting old html speeds up things. likely do to writing vs overwriting ?  
delete_old_html_files("maps/")

m = folium.Map(location=[41.9, -97.3], zoom_start=5,world_copy_jump=True) # would like to change this making maps is a function... 


locations = load_json(LOCATION_DATA)
routes = load_json(ROUTE_DATA) 

# re-directs
city_data = {city["name"]: city["page"] for city in locations}
# coords
city_coords = {c['name']:(c['lat'], c['lon']) for c in locations} 




for city in locations:
 
    lat = city["lat"]
    lon = city["lon"]
    name = city["name"]

    print(f"Adding {name} to main map")
    color = "#0034C5"

    tooltip = folium.Tooltip(text= F"Flight Routes from: {name}",
    style=F"""width:{20*len("Flight Routes from: {name}")}; 
             height:30px; 
             padding: 2.5px,7.5px;
             font-size: 25px;    
             """,)
    

    circleMaker(m,location=[lat,lon],radius=20,tooltip=tooltip,repeat = True)


for city in locations:
    
    lat = city["lat"]
    lon = city["lon"]
    origin_name = city["name"]
    origin_coords = [lat, lon]

    print(f"--- Generating map for {origin_name} ---")
    
    
    cur_m = folium.Map(location=[lat,lon], zoom_start=5,world_copy_jump=True) 
    #folium.GeoJson(geo_json_data).add_to(cur_m) <-- unused. Can make indivdiual objects for areas (states)

    cur_city_data = city_data.copy()
    cur_city_data[origin_name] = START_PAGE
    

    fg_years = []
    for year in range(2004, 2023):
        if year==2004:
            fg = folium.FeatureGroup(name="blank",show=True)

            cur_m.add_child(fg)
            fg_years.append(fg)

            continue
        year_str = str(year) 
        
        fg = folium.FeatureGroup(name=year_str,show=False)
        
        if year_str in routes and origin_name in routes[year_str]:
            origin_routes = routes[year_str][origin_name]
            
        
            max_passengers = max(origin_routes.values()) or 1
            min_passengers = min(origin_routes.values()) or 0

            for dest_name, passengers in origin_routes.items():
                if dest_name in city_coords:
                    dest_coords = city_coords[dest_name]
                    
                    if passengers <= 0:
                        weight = 0
                    else:

                        w = (passengers - min_passengers) / (max_passengers - min_passengers) * 9 + 1
                        # normalizes passengers (min = 0 max = 1) to have range of weights 
                        # there's likely better weight functions but this one gets the job done.
                        weight = int(round(w))
                    
                    
                    drawArc(fg, origin_coords, dest_coords, weight=weight, color="#000000")

        cur_m.add_child(fg)
        fg_years.append(fg)
   
    GroupedLayerControl(groups={F"Flights from what year": fg_years}).add_to(cur_m) 
   


    for sub_city in locations.copy():
        if sub_city['name'] != city['name']:
            tooltip = folium.Tooltip(
                text=f"Flight Routes from: {sub_city['name']}",
                style=f"""
                    width:{20*len(f"Flight Routes from: {sub_city['name']}")};
                    height:30px; 
                    padding:2.5px 7.5px;
                    font-size:25px;
                """
            )
        else:
            tooltip = folium.Tooltip(
                text="Return to base.",
                style=f"""
                    width:{20*len("Return to base.")};
                    height:30px; 
                    padding:2.5px 7.5px;
                    font-size:25px;
                """
            )
        
    
        circleMaker(cur_m, location=[sub_city['lat'], sub_city['lon']], radius=20, tooltip=tooltip)

 
    makeRedirects(cur_m, cur_city_data)
           
    cur_m.save(f'maps/{city['page']}')
    

print(F"Saving main map (maps/{START_PAGE})")
makeRedirects(m,city_data)
m.save(F'maps/{START_PAGE}')

print("Done.")