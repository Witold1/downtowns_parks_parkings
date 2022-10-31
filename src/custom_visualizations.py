import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import geopandas as gpd
import networkx as nx
# !pip install pywaffle
# from pywaffle import Waffle
# import folium

def plot_interim_maps(area, waterways, water, save=False):
    """Plots the far and close looks on a city

    Parameters
    ----------
    area : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with shape of a place to get max and min .bounds from
    waterways : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with footprints of waterways in selected area
        {'water': True, 'natural' : ['bay', 'strait', 'water'], 'waterway' : True}
    water : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with polygon of big water in selected area
    save : bool
        if save image
    ----------
    """
    # https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Rectangle.html
    # https://stackoverflow.com/questions/13013781/how-to-draw-a-rectangle-over-a-specific-region-in-a-matplotlib-graph
    # https://wiki.openstreetmap.org/wiki/Tag:natural%3Dcoastline

    if not water.empty:
        fig, axes = plt.subplots(1, 3, figsize=(14, 18), dpi=600, facecolor='white')
    else:
        fig, axes = plt.subplots(1, 2, figsize=(14, 18), dpi=600, facecolor='white')
    axes = axes.flatten()

    # Plot 1
    if not water.empty:
        water.plot(ax=axes[0])
        axes[0].add_patch(Rectangle(xy=(area.bounds.minx[0], area.bounds.miny[0]),
                                        width=area.bounds.maxx[0] - area.bounds.minx[0],
                                        height=area.bounds.maxy[0] - area.bounds.miny[0],
                                        facecolor="none", ec='k', lw=1, alpha=0.5)
                             )

        axes[0].scatter([area.bounds.minx[0], area.bounds.maxx[0]], [area.bounds.miny[0], area.bounds.maxy[0]],
                            s=25, color='red', alpha=0.7)
        axes[0].grid(alpha=0.05, color='grey', linestyle='--', zorder=10)

    # Plot 2
    # (bN, bS, bE, bW)
    _ = ox.plot_footprints(gdf=water, bbox=(area.bounds.maxy[0], area.bounds.miny[0], area.bounds.maxx[0], area.bounds.minx[0]), #(bN, bS, bE, bW),
                           color='lightblue', bgcolor='white',
                           save=False, show=False, close=False,
                           ax=axes[-2])
    waterways[waterways.geom_type != 'Point'].plot(ax=axes[-2], zorder=5, color='lightblue', alpha=0.8)
    axes[-2].spines[['left', 'right', 'top', 'bottom']].set_visible(True)
    axes[-2].set_title('close look', loc='left', family='monospace')

    # Plot 3
    _ = ox.plot_footprints(gdf=water, bbox=(area.bounds.maxy[0], area.bounds.miny[0], area.bounds.maxx[0], area.bounds.minx[0]), #(bN, bS, bE, bW),
                           color='lightblue', bgcolor='white',
                           save=False, show=False, close=False,
                           ax=axes[-1])
    waterways[waterways.geom_type != 'Point'].plot(ax=axes[-1], zorder=5, color='lightblue', alpha=1.)
    area.plot(ax=axes[-1], zorder=10, color='grey', alpha=0.2)
    axes[-1].spines[['left', 'right', 'top', 'bottom']].set_visible(True)
    axes[-1].set_title('city area', loc='right', family='monospace')

    fig.tight_layout()
    if save:
        fig.savefig('Look oceanfront city.png', format='png', dpi=600, bbox_inches='tight')

def plot_pictorial_map(area, edges, buildings, parkings, parks, waterways, water, axis):
    """Plots the pictoral map which shows the selected features of a city

    Parameters
    ----------
    area : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with shape of a place to get max and min .bounds from
    edges : geopandas.geodataframe.GeoDataFrame
        selected types of road network edges from `networkx.MultiDiGraph`
    buildings : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with footprints of buildings in selected area
        {'building': True}
    parkings : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with footprints of parking in selected area
        {'amenity': 'parking'}
    parks : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with footprints of parkis in selected area
        {'leisure': 'park', 'landuse': 'grass'}
        # wetland , meadow, golf_course, landuse	recreation_ground
    waterways : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with footprints of waterways in selected area
        {'water': True, 'natural' : ['bay', 'strait', 'water'], 'waterway' : True}
    water : geopandas.geodataframe.GeoDataFrame
        GeoDataFrame with polygon of big water in selected area
    axis : matplotlib.pyplot.axis
        axis object, where to plot
    """
    # Plot the footprint
    area.plot(ax=axis, facecolor='black', zorder=0)
    # Plot street edges
    edges[edges.bridge.isna()].plot(ax=axis, linewidth=0.9, edgecolor='dimgray', alpha=1., zorder=4)
    edges[~edges.bridge.isna()].plot(ax=axis, linewidth=0.9, edgecolor='dimgray', alpha=0.85, zorder=10)

    # Plot buildings
    buildings[buildings.geom_type != 'Point'].plot(ax=axis, facecolor='silver', alpha=0.7, zorder=6)
    # Plot parkings
    parkings[parkings.geom_type != 'Point'].plot(ax=axis, color='yellow', alpha=0.7, markersize=10, zorder=6)
    # Plot the parks
    parks[(parks.geom_type != 'Point') & (parks.landuse != 'grass')].plot(facecolor='green', ax=axis, zorder=2)
    parks[(parks.geom_type != 'Point') & (parks.landuse == 'grass')].plot(facecolor='lightgreen', ax=axis, alpha=0.8, zorder=1)

    # DEPRICATED: Plot the general coastline
    # coastline[coastline.geom_type != 'Point'].plot(ax=ax, color='grey', alpha=0.8, lw=0.5, zorder=0)
    # Plot the water and waterways
    waterways[waterways.geom_type != 'Point'].plot(ax=axis, color='lightblue', edgecolors=None, alpha=1.0, lw=0.5, zorder=3)
    ox.plot_footprints(water, bbox=(area.bounds.maxy[0], area.bounds.miny[0], area.bounds.maxx[0], area.bounds.minx[0]), #(bN, bS, bE, bW),
                       #dpi=300, figsize=(18, 18),
                       color='lightblue', bgcolor='white', ax=axis)

    return ax

def plot_pictorial_maps_vignette(path, group_start, group_end, group_num, enumerate_charts=True, save=True):
    """Plots a collective chart out of many pictoral maps

        # Chart enumeration idea credits to : unicode Circled Numbers
            http://xahlee.info/comp/unicode_circled_numbers.html

    Parameters
    ----------
    path : str
        path to pictorial maps folder
    group_start : int
        start index of current group of pictorial maps, regarding path
    group_end : int
        end index of current group of pictorial maps, regarding path
    group_num : int
        index of current group of pictorial maps
    enumerate_charts : bool
        if add numbers to a title of pictorial maps in vignette
    save : bool
        if save image
    """
    import re

    plt.ioff()
    fig, axes = plt.subplots(3, 3, figsize=(14, 14), dpi=1800, facecolor='white')
    axes = axes.flatten()

    for indx, image_path in enumerate(path):
        print(f'{indx} \t {image_path}')
        image = plt.imread(image_path, format='png')
        city = re.search('Parks-Parkings (.*).png', image_path, re.IGNORECASE).group(1)

        axes[indx].imshow(image)
        axes[indx].set_title(label=re.sub(', USA?$|, United States$', '', city), loc='center')
        if enumerate_charts:
            axes[indx].set_title(label=f"{group_start + indx + 1}.", loc='left', family='serif', alpha=0.5)

        axes[indx].spines[['top', 'left', 'right', 'bottom']].set_visible(False)
        axes[indx].axis('off')
        #break

    # remove unused axes
    if indx < (9 - 1):
        for iter_axis_num in range(indx + 1, 9):
            axes[iter_axis_num].remove()

    fig.tight_layout()

    if save is True:
        print('saving the final vignette')
        save_path_name = f'pictoral_vignette_group_{group_num}'
        # https://stackoverflow.com/questions/16183462/saving-images-in-python-at-a-very-high-quality
        fig.savefig(f'../figures/internal/{save_path_name}.png', format='png', dpi=600)
        # https://stackoverflow.com/questions/15713279/calling-pylab-savefig-without-display-in-ipython
        plt.close(fig)
    else:
        print('showing the final vignette')
        plt.show()

def _plot_pictorial_map_legend(save_path='legend_colors.png'):
    """Plots fancy legend boxes

        ### Alternative:
        # HTML alternative
        # <svg width="100" height="100">
        #     <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="white" />
        #     <text fill="#000000" font-size="14" font-family="Verdana"x="15" y="55">#b5b536</text>
        # </svg>

    Parameters
    ----------
    save_path : str
        path where to save an image
    """
    import matplotlib
    import matplotlib.pyplot as plt
    # !pip install pywaffle
    from pywaffle import Waffle
    colors = ['dimgray', 'silver', 'green', 'lightgreen', 'lightblue', 'yellow', '#b5b536', 'black']
    dark_color_indexes = [0, 7] # [0, 1, 7]
    tags = ['motorways\nbridges', 'buildings', 'parks', 'grass', 'water', 'parkings', 'parking\nbuildings', 'city\nlimits']

    fig = plt.figure(figsize=(10, 20), facecolor='white', dpi=600,
                FigureClass=Waffle,
                columns=len(colors),
                values=[1] * len(colors),
                colors=colors,
                )

    pos_x = 0.015 # 0.035
    for indx in range(len(colors)):
        try:
            color_code = matplotlib.colors.cnames[colors[indx]]
        except:
            color_code = colors[indx]
        fig.text(x=pos_x, y=0.497, s=color_code, c='black' if indx not in dark_color_indexes else 'white', family='monospace')
        fig.text(x=pos_x, y=0.468 if '\n' not in tags[indx] else 0.46, s=tags[indx], c='black', family='monospace')
        pos_x += 1 / 8.07

    plt.title('colorboxes legend', loc='left', family='monospace')

    fig.savefig(save_path, format='png', bbox_inches='tight')

def plot_general_map_interactive(data={'Atlanta, Georgia': [33.7489924, -84.3902644]},
                                save_path='../figures/internal/general_map_interactive.html'):
    """Plots interactive map of cities locations

    Parameters
    ----------
    data : dict
        dict with coordinates of cities
        Example: {'Atlanta, Georgia': [33.7489924, -84.3902644]}
    save_path
        path where to save an image
    """
    import folium

    # Build the default map for a specific location
    chart = folium.Map(location=[39.50, -98.35],
                       tiles='cartodbpositron',
                       zoom_start=4.,
                       min_zoom=2,
                       prefer_canvas=True,
                       control_scale=False,
                       zoom_control=True,
                       scrollWheelZoom=False,
                       dragging=True,
                       max_bounds=True) #[-90.458444, -70.458444]

    for tiles in ['Stamen Terrain', 'Stamen Toner', 'Stamen Water Color', 'cartodbpositron',
                 'cartodbdark_matter']:
        folium.TileLayer(tiles, detect_retina=True).add_to(chart)
    folium.LayerControl().add_to(chart)

    for indx, (key, val) in enumerate(data.items()):
        marker = folium.CircleMarker(location=val, popup=key, radius=3,
                                     color="#3186cc", fill=True, fill_color="#3186cc")
        marker.add_to(chart)

    chart.save(save_path)
    return chart
