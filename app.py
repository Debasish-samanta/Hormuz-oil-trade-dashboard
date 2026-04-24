import dash
from dash import dcc, html, Input, Output
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json

app = dash.Dash(__name__)
server = app.server

# LOAD DATA
# =========================
df = pd.read_excel("data/Chokepoints_FY2026_F5.xlsx")
df2 = pd.read_excel("data/import.xlsx")

world = gpd.read_file("data/World_enegy_transportation2.shp").to_crs(epsg=4326)
points = gpd.read_file("data/Checkpoints2.shp").to_crs(epsg=4326)

# Convert to GeoJSON
worldgeojson = json.loads(world.to_json())

hormuz_lat = 26.566
hormuz_lon = 56.25

def create_arc(lon1, lat1, lon2, lat2, n_points=60):
    lons = np.linspace(lon1, lon2, n_points)
    lats = np.linspace(lat1, lat2, n_points)

    curve = np.sin(np.linspace(0, np.pi, n_points)) * 4
    lats = lats + curve

    return lons, lats

# → 1_MAP
fig_map = go.Figure()

fig_map.add_trace(go.Choropleth(
    geojson=worldgeojson,
    locations=world.index,
    z=[1]*len(world),
    colorscale=[[0, "#CFCFCF"], [1, "#CFCFCF"]],
    showscale=False,
    hoverinfo='skip',

     marker=dict(
        line=dict(
            color="white",  
            width=1
        )
    )
))

# Chekepoints
fig_map.add_trace(go.Scattergeo(
    lon=points.geometry.x,
    lat=points.geometry.y,
    mode='markers+text',
    text=points["name"],
    textposition="top center",
    marker=dict(size=8, color='red'),
    textfont=dict(color= "black"),   
    hovertemplate=
    "<b>%{text}</b><br>" +
    "Transit volumes: %{customdata:.2f} Mb/d<extra></extra>",

    customdata=points["y1H25"] if "y1H25" in points.columns else None,
    showlegend=False
))

fig_map.update_geos(
    projection_type="orthographic",
    projection_rotation=dict(lat=26, lon=56),
    showland=True,
    landcolor="#CFCFCF",
    showocean=True,
    oceancolor="rgb(7, 191, 247)", 
    showcountries=True,        
    countrycolor="white",      
    countrywidth=1,          
    showcoastlines=True,
    coastlinecolor="white"
)

fig_map.update_layout(
    template="plotly_dark",
    title="Daily Transit Volumes of Petroleum and Other Liquids Through World Maritime Oil Chokepoints <br>" "(mb/d) (1st Half of 2025)",
    font=dict(family="Times New Roman",color='white', size=12),
    margin=dict(l=0, r=0, t=40, b=40),
    showlegend=False,
    annotations=[dict(text="<i>" "Source: U.S. Energy Information Administration (EIA), Short-Term Energy Outlook, February 2026<br>"
                 "EIA analysis based on Vortexa tanker tracking and Panama Canal Authority data" "</i>",   
            x=0,            
            y=-0.01,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="top",
            showarrow=False,
            font=dict(family="Times New Roman",
                      size=10,
                      color="white")
        )
    ]
)

# PAGE 1_BAR GRAPH
fig_bar = px.bar(
    df,
    x="Location",
    y="1H25",
    color="1H25",
    color_continuous_scale="Viridis"
)

fig_bar.update_layout(
    template= "plotly_dark",
    title= "Oil Transit Volume across Major Chokepoints (million barrels per day)",
    xaxis_title="Locations",
    yaxis_title="Transit Volume (Mb/d)",
    coloraxis_showscale=False,
    font=dict(family="Times New Roman",color='white'), 
    margin=dict(l=10, r=0, t=40, b=0)
)

fig_bar.update_traces(hovertemplate="<b>%{x}</b><br>" +"Transit Volume: %{y:.2f} Mb/d<extra></extra>")


# PAGE 2 → FLOW MAP
fig_flow = go.Figure()

# Origin
fig_flow.add_trace(go.Scattergeo(
    lon=[hormuz_lon],
    lat=[hormuz_lat],
    mode='markers+text',
    marker=dict(size=14, color='green'),
    text=["<b>" "Strait of Hormuz" "<b>"],
    textfont=dict(color='black', size=12),
    textposition="top center",
    showlegend=False
))

# Flows
for i, row in df2.iterrows():

    lons, lats = create_arc(
        hormuz_lon, hormuz_lat,
        row['Lon'], row['Lat']
    )

    fig_flow.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        mode='lines',
        line=dict(width=max(1, row['1H25'] * 0.4),
            color='red'),
            opacity=0.7,
        hovertemplate="<b>%{text}</b><br>" +"Imports: %{customdata:.2f} Mb/d<extra></extra>",
        text=[row['country']]*len(lons),
        customdata=[row['1H25']]*len(lons),
        showlegend=False
    ))

    # Arrow head
    fig_flow.add_trace(go.Scattergeo(
        lon=[row['Lon']],
        lat=[row['Lat']],
        mode='markers',
        marker=dict(size=6 + np.sqrt(row['1H25']) * 3,
            color='yellow',
            symbol='triangle-up'),        
        hovertemplate="<b>%{text}</b><br>" +"Imports: %{customdata:.2f} Mb/d<extra></extra>",
        text=[row['country']],
        customdata=[row['1H25']],
        showlegend=False
    ))

# Labels
fig_flow.add_trace(go.Scattergeo(
    lon=df2['Lon'],
    lat=df2['Lat'],
    mode='text',
    text=df2['country'],
    textfont=dict(color= "black"),
    textposition="top center",
    showlegend=False
))

fig_flow.update_geos(
    projection_type="equirectangular",
    showland=True,
    landcolor="#CFCFCF",
    showocean=True,
    oceancolor="rgb(7, 191, 247)",
    showcountries=True,
    countrycolor="white",
    showcoastlines=True,
    coastlinecolor="white"
)

fig_flow.update_layout(
    template= "plotly_dark",
    title="Volume of Oil Transpoted Through Strait of Hormuz",
    font=dict(family="Times New Roman", color='white'),
    margin=dict(l=0, r=0, t=40, b=40),
    showlegend=False,
        annotations=[dict(text="<i>" "Source: U.S. Energy Information Administration (EIA), Short-Term Energy Outlook, February 2026<br>"
                 "EIA analysis based on Vortexa tanker tracking and Panama Canal Authority data" "</i>",   
            x=0,            
            y=-0.01,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="top",
            showarrow=False,
            font=dict(family="Times New Roman",
                      size=10,
                      color="white")
        )
    ]
)


# PAGE 2 → BAR GRAPH
fig_country =go.Figure(data=[go.Pie(labels=df2["country"],
                                   values=df2["1H25"], 
                                   textinfo= 'label+value',
                                    textfont=dict(color= "white"),
                                    texttemplate="%{label}<br>%{value:.2f} Mb/d<br>(%{percent})",
                                   insidetextorientation= 'radial',
                                   hovertemplate="<b>%{label}</b><br>" +
                                                 "Imports: %{value:.2f} Mb/d<br>" +
                                                 "Share: %{percent}<extra></extra>")])



fig_country.update_layout(
    template= "plotly_dark",
    title="Country-wise Oil Imports via Strait of Hormuz",
    font=dict(family="Times New Roman", color='white'),
    margin=dict(l=0, r=0, t=40, b=0),
)


# DASH LAYOUT

app.layout = html.Div([
    html.H1("Analysis of Global Oil Trade through the Strait of Hormuz",
            style={'textAlign': 'center', 'color': 'Black', 'textShadow': '2px 2px 4px rgba(0,0,0,0.8)'}),
    dcc.RadioItems(
        id='page-selector',
        options=[
            {'label': 'Global Chokepoints', 'value': 'map'},
            {'label': 'Import Through Strait of Hormuz', 'value': 'flow'}
        ],
        value='map',
        inline=True,
        style={'textAlign': 'center'}
    ),

    html.Div(id='page-content')

])

# =========================
# CALLBACK
# =========================
@app.callback(
    Output('page-content', 'children'),
    Input('page-selector', 'value')
)
def display_page(page):
    if page == 'map':
        return html.Div([html.Div([dcc.Graph(figure=fig_map, style={'height': '83vh'})
            ], style={'width': '70%'}),
            html.Div([dcc.Graph(figure=fig_bar,style={'height': '83vh'})
            ], style={'width': '30%'})
    
        ], style={
            'display': 'flex',  
            'flexDirection': 'row'
        })
        
    elif page == 'flow':
        return html.Div([html.Div([dcc.Graph(figure=fig_flow, style={'height': '83vh'}, 
                                             config={'modeBarButtonsToRemove': ['resetGeo'],'displaylogo': False})
            ], style={'width': '70%'}),
    
            html.Div([dcc.Graph(figure=fig_country, style={'height': '83vh'})
            ], style={'width': '30%'})
    
        ], style={
            'display': 'flex',  
            'flexDirection': 'row'
        })
        
if __name__ == '__main__':
    app.run_server(debug=False)
