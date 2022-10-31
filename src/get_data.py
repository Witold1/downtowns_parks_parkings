import logging
#   https://docs.python.org/3/howto/logging.html
#   https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
import datetime
import glob

import osmnx as ox
ox.config(log_console=False, use_cache=True, timeout=10000)
import geopandas as gpd
import networkx as nx

from . import custom_visualizations as visuals

CITIES_LIST = ['Detroit, Michigan, USA', 'Lansing, Michigan, US', 'Grand Rapids, Michigan',
               'Columbus, Ohio, United States', 'Cleveland, Ohio', 'Denver, Colorado',
               'Las Vegas, Nevada', 'Tucson, Arizona', 'Indianapolis, Indiana, USA', 'Pittsburgh, Pennsylvania',
               'Nashville, Tennessee, United States', 'Sacramento, California', 'New Orleans, Louisiana',
               'Philadelphia, Pennsylvania, United States', 'Miami, Florida', 'District of Columbia, United States',
               'Seattle, Washington', 'San Francisco, California, United States', 'Portland, Oregon', 'Dallas, Texas',
               'Atlanta, Georgia', 'Phoenix, Arizona', 'Minneapolis, Minnesota', 'San Diego, California',
               'Tampa, Florida', 'Baltimore, Maryland', 'St. Louis, Missouri, United States', 'Charlotte, North Carolina', 'San Antonio, Texas',
               'Boston, Massachusetts', 'Los Angeles, California', 'New York City, New York, United States',
               'Chicago, Illinois, United States', 'Berlin, Deutschland', 'Paris, France', 'Bangalore (ಬೆಂಗಳೂರು, Bengaluru)', 'Moscow, Russia']
BIG_CITIES_BBOXES = {'Los Angeles, California' : [34.15, 33.94, -118.2, -118.28],
                    'Chicago, Illinois, United States' : [41.925359, 41.821333, -87.582386, -87.686600],
                    'New York City, New York, United States' : [40.771311, 40.671314, -73.951456, -74.055138],
                    'Santiago, Chile' : [-33.371278, -33.515664,-70.572588, -70.730517]}

def _get_list_of_cities(cities=None):
    """Returns a list of test cities

    Parameters
    ----------
    cities : list
        Custom list of cities which to query to access data
    """
    if cities is None: # if no links provided, use hardcoded list
        cities = ['Detroit, Michigan, USA', 'Miami, Florida', 'Seattle, Washington']

    return cities

def get_road_netrowk_graph(place : str):
    """Downloads road network for selected place
        from Open Street Maps via Overpass API using osmnx package

        Returns edges of next classes:
            * motorways (i.e. interstates)
            * bridges of secondary roads
                f.e. see Miami, FL

        For extra information regarding OSM road network classes and filters, see:
            * OSM key documentation https://wiki.openstreetmap.org/wiki/Key:highway
            Stackoverflow
            * https://stackoverflow.com/questions/56666987/download-osm-network-with-osmnx-filtering-based-on-the-union-of-tag-values
            * https://stackoverflow.com/questions/66264776/correct-osmnx-custom-filter-syntax
            * https://stackoverflow.com/questions/47784074/trying-to-plot-two-or-more-infrastructures-in-the-same-figure-using-osmnx/62239377#62239377

        ### NOTE : No need to do two separate queries for one type of network.
            Easier to get the whole network filtered later

    Parameters
    ----------
    place : str
        Place (location) name in OSM format to extract geometries from
    """
    # get motorway type-roads, i.e. interstates
    custom_filter = '["highway"~"motorway|motorway_link"]' #|primary|primary_link|trunk #secondary|secondary_link|ternaty|residential #|trunk
    graph = ox.graph_from_place(place, simplify=True, custom_filter=custom_filter)

    # get all other car roads
    custom_filter_2 = '["highway"~"primary|primary_link|secondary|secondary_link|ternaty|service|residential|trunk"]'
    graph_secondary = ox.graph_from_place(place, simplify=True, custom_filter=custom_filter_2)

    graph = nx.compose(graph, graph_secondary)
    del graph_secondary

    # Retrieve nodes and edges
    nodes, edges = ox.graph_to_gdfs(graph)
    del graph

    # get only motorways and bridges or secondary roads (i.e. see Miami, FL case)
    print('\t\t selecting highways or bridges only')
    edges = edges[edges['highway'].isin(['motorway', 'motorway_link']) |
          ((~edges['highway'].isin(['motorway', 'motorway_link'])) & (~edges.bridge.isna()))]

    return edges

def get_big_water_polygon(area, path_big_water_polygon_file):
    """Attaches big water (oceans and seas) polygon for bbox of selected area
        using pre-calculated Water polygons (https://osmdata.openstreetmap.de/data/water-polygons.html)
            * Format: Shapefile, Projection: WGS84 (Large polygons are split)

        Returns big water (oceans and seas) polygon for selected area

        For extra information, see:
            * https://stackoverflow.com/questions/62285134/how-to-fill-water-bodies-with-osmnx-in-python
            * https://osmdata.openstreetmap.de/data/water-polygons.html

    Parameters
    ----------
    area : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with shape of a place to get max and min .bounds from
    path_big_water_polygon_file : str
        path to big water polygon; tested for raw, about ~700Mb, file
    """
    # Load big water polygons
    path_big_water_polygon_small = '../input/water-polygons/simplified-water-polygons-split-3857/simplified_water_polygons.shp'
    path_big_water_polygon_large = '../input/water-polygons-big/water-polygons-split-4326/water_polygons.shp'

    water_polygon_bbox = (area.bounds.minx[0], area.bounds.miny[0], area.bounds.maxx[0], area.bounds.maxy[0])

    water = gpd.read_file(path_big_water_polygon_large,
                            bbox=water_polygon_bbox) # Tuple is (minx, miny, maxx, maxy)
    if water.crs.name != 'WGS 84':
        water.to_crs(epsg=4326, inplace=True)

    # https://stackoverflow.com/questions/18089667/how-to-estimate-how-much-memory-a-pandas-dataframe-will-need
    print(f"{water.memory_usage(index=True, deep=True).sum()} bites")

    return water

def get_many_city_data(place):
    """Downloads many features for selected area
        from Open Street Maps via Overpass API using osmnx package

        Returns
            * city area polygon
                - GeoDataFrame with shape of a place
            * road network edges
                - selected types of road network edges
            * buildings footprints
                - {'building': True}
            * parkings footprints
                - {'amenity': 'parking'}
            * parks footprints
                - {'leisure': 'park', 'landuse': 'grass'}
            * waterways polygons
                - {'water': True, 'natural' : ['bay', 'strait', 'water'], 'waterway' : True}
            * big water polygons
                - polygon of big water in selected area
        all are  `geopandas.geodataframe.GeoDataFrame` type

    Parameters
    ----------
    place : str
        Place (location) name in OSM format to extract geometries from
    """

    print(f'{datetime.datetime.now()} location - {place}')
    area = ox.geocode_to_gdf(place)
    bN, bS, bE, bW = area.bounds.maxy[0], area.bounds.miny[0], area.bounds.maxx[0], area.bounds.minx[0]

    print(f'\t {datetime.datetime.now()} extracting roads')
    edges = get_road_netrowk_graph(place)

    print(f'\t {datetime.datetime.now()} extracting buildings')
    tags = {'building': True}
    if place not in BIG_CITIES_BBOXES:
        buildings = ox.geometries_from_place(place, tags)
    else:
        buildings = ox.geometries_from_bbox(*BIG_CITIES_BBOXES[place], tags)
    #     print(f'\t\t num objects: {len(buildings)}')

    print(f'\t {datetime.datetime.now()} extracting parkings')
    tags = {'amenity': 'parking'}
    parkings = ox.geometries_from_place(place, tags)
    print(f'\t\t num objects: {len(parkings)}')

    print(f'\t {datetime.datetime.now()} extracting parks')
    tags = {'leisure': 'park', 'landuse': 'grass'} # wetland , meadow, golf_course, landuse	recreation_ground
    parks = ox.geometries_from_place(place, tags)
    print(f'\t\t num objects: {len(parks)}')

    print(f'\t {datetime.datetime.now()} extracting waterways')
    tags = {'water': True, 'natural' : ['bay', 'strait', 'water'], 'waterway' : True}
    waterways = ox.geometries_from_place(query=place, tags=tags, buffer_dist=50)

    print(f'\t {datetime.datetime.now()} extracting big water')
    path_big_water_polygon_file = '../input/water-polygons-big/water-polygons-split-4326/water_polygons.shp'
    water = get_big_water_polygon(area, path_big_water_polygon_file)

    return area, edges, buildings, parkings, parks, waterways, water

def _main(cities=_get_list_of_cities(None), get_features=False):
    """Run throught cities list
        get city features and plot city pictoral maps

    """
    for place in cities[:]:
        now = datetime.datetime.now()

        # get data features
        if get_features:
            area, edges, buildings, parkings, parks, waterways, water = get_many_city_data(place)

        # plot data features
        print(f'\t {datetime.datetime.now()} plotting interim cartograms')
        visuals.plot_interim_maps(area, waterways, water, False)

        print(f'\t {datetime.datetime.now()} plotting chart')
        # Create a subplot object for plotting the layers onto a common map
        fig, ax = plt.subplots(figsize=(16, 16), dpi=400) # dpi=600
        visuals.plot_pictorial_map(area, edges, buildings, parkings, parks, waterways, water, ax)
        fig.tight_layout()
        print(f'\t {datetime.datetime.now()} saving chart')
        # fig.savefig(f"Parks-Parkings {place}.svg", format = 'svg', dpi=1800)
        fig.savefig(f"Parks-Parkings {place}.jpg", format = 'jpg', dpi=1800)
        del(fig, area, edges, buildings, parkings, parks, waterways, water)
        print(f'\t {datetime.datetime.now() - now} executed')
