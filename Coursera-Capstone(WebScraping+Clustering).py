#!/usr/bin/env python
# coding: utf-8

# In[77]:


import requests
from bs4 import BeautifulSoup
import pandas as pd


# # 1. WebScraping to Get Data

# In[78]:


# passing the wikipedia url where we have the data tables
Toronto_neighbors_url = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

req = requests.get(Toronto_neighbors_url, headers) # Get the data using requests
soup = BeautifulSoup(req.content, 'html.parser')  #Creating BeautifulSoup object to pull data in html format
soup.contents


# In[79]:


table_contents = []
table = soup.find('table')  #now using soup object we can acess the tables present in data

for row in table.findAll('td'):  #getting the td->table data of each row
    cell = {}  #creating an empty dictionary 
    if row.span.text == 'Not assigned':
        pass
    else:
        cell['PostalCode'] = row.p.text[:3] #filling the data(value) of 'postalCode' giving this as key to the dictionary 
        cell['Borough'] = (row.span.text).split('(')[0] #same
        cell['Neighborhood'] = (((((row.span.text).split('(')[1]).strip(')')).replace('/',',')).replace(')',' ')).strip(' ')
        table_contents.append(cell)
print(table_contents[:5]) #now we have the data of each row in this list object but the list elements are dictionaries  
df = pd.DataFrame(table_contents)  #convert that list to dataframe
df['Borough']=df['Borough'].replace({'Downtown TorontoStn A PO Boxes25 The Esplanade':'Downtown Toronto Stn A',
                                             'East TorontoBusiness reply mail Processing Centre969 Eastern':'East Toronto Business',
                                             'EtobicokeNorthwest':'Etobicoke Northwest','East YorkEast Toronto':'East York/East Toronto',
                                             'MississaugaCanada Post Gateway Processing Centre':'Mississauga'})
df.head()


# In[80]:


df['Neighborhood'] = df.groupby('PostalCode')['Neighborhood'].transform(lambda x: ','.join(x))
df = df.drop_duplicates()


# # 2. Get The Latitude and Longitude Coordinates of Each From Geospatial_coordinates.csv

# In[81]:


Geospatial_coordinates_df = pd.read_csv("Geospatial_coordinates.csv")
Geospatial_coordinates_df.head()


# In[82]:


df = df.merge(Geospatial_coordinates_df, left_on = 'PostalCode', right_on='Postal Code')
df = df.drop(df.columns[3], axis=1)
df.head()


# # Explore Cluster The Neighborhoods in Toronto

# In[83]:


toronto_df = df[df['Borough'].str.contains('Toronto')]
toronto_df = toronto_df.reset_index()
toronto_df = toronto_df.drop('index',axis = 1)
toronto_df.head()


# In[84]:


toronto_df.groupby('Borough').count()


# In[85]:


for borough in list(set(toronto_df['Borough'])):
    borough_neighborhood_df = toronto_df[toronto_df['Borough']==borough]
    print(borough_neighborhood_df)
    print("\n--------------------------------------\n")


# In[86]:


# Create Map using folium

import folium
map_network = folium.Map(location = [43.6532, 79.3832], zoom_start =0)

# add markers to map
for lat,lng,borough,neighborhood in zip(toronto_df['Latitude'], toronto_df['Longitude'], toronto_df['Borough'], toronto_df['Neighborhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_tml=True)
    folium.CircleMarker(
        [lat, lng],
        radius = 5,
        popup = label,
        color = 'blue',
        fill = True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_network)

map_network


# # Clustering

# In[87]:


# set number of clusters
kclusters = 5

toronto_grouped_clustering = toronto_df.drop('Neighborhood', axis=1)
toronto_grouped_clustering = toronto_grouped_clustering.drop('PostalCode', axis=1)
toronto_grouped_clustering = toronto_grouped_clustering.drop('Borough', axis=1)

#run k-means clustering
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors

kmeans = KMeans(n_clusters = kclusters, random_state = 0).fit(toronto_grouped_clustering)
kmeans.labels_[0:10]


# In[88]:



toronto_df.insert(0,'Cluster Labels', kmeans.labels_)

toronto_df


# In[89]:


# create map
map_clusters = folium.Map(location = [43.6532, 79.3832], zoom_start=0)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to map
markers_colors=[]
for lat,lng,neighborhood,cluster in zip(toronto_df['Latitude'], toronto_df['Longitude'], toronto_df['Neighborhood'], toronto_df['Cluster Labels']):
    label = folium.Popup(str(neighborhood)+', Cluster'+str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius = 5,
        popup = label,
        color = rainbow[cluster-1],
        fill=True,
        fil_color = rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)
    

map_clusters


# In[ ]:




