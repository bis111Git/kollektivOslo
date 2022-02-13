# -*- coding: utf-8 -*-
"""
Created on Sun Jan 30 07:33:12 2022

@author: bis11
"""

import requests
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import pydeck as pdk
import numpy as np


st.set_page_config(layout = "wide")

#@st.experimental_memo(suppress_st_warning=True) #Funker ikke
@st.cache(ttl=120) #Denne gjør at vi bare henter data når nettsiden lastes inn første gang, for å slippe å plage enTur med masse forespørsler
def hent_data():
    print("Hentet data")
    query = """
        {
          vehicles(codespaceId:"RUT") {
            line {lineRef}
            lastUpdated
            location {
              latitude
              longitude
            }
            delay
          }
        }
    """
    url = "https://api.entur.io/realtime/v1/vehicles/graphql"
    r = requests.post(url, json={'query': query})
    json_data = json.loads(r.text)
    
    
    lat = []
    lon = []
    linje = []
    oppdatert = []
    delay = []
    er_forsinket = []
    
    for kjoretoy in json_data['data']['vehicles']:
        if int(kjoretoy['line']['lineRef'][9:]) < 100:
            lat.append(kjoretoy['location']['latitude'])
            lon.append(kjoretoy['location']['longitude'])
            linje.append(kjoretoy['line']['lineRef'][9:])
            oppdatert.append(kjoretoy['lastUpdated'][:16])
            if kjoretoy['delay']>0:
                delay.append(kjoretoy['delay'])
            else:
                delay.append(0)
            
            if kjoretoy['delay']>120:
                er_forsinket.append(True)
            else:
                er_forsinket.append(False)
        
    
    dataDict = {'lat':lat,'lon':lon, 'linje': linje, 'sist_oppdatert':oppdatert, 'delay':delay, 'er_forsinket':er_forsinket}
    
    df = pd.DataFrame(data=dataDict)
    return df

#@st.experimental_memo(suppress_st_warning=True)
@st.cache(ttl=120)
def lager_linjedata(df):

    forsinkelser = []
    antall_kjoretoy = []
    linjeNr = []
    linje_liste= df.linje.tolist()
    
    for linjen in set(df.linje):
        gjennomsnittlig_forsinkelse = sum(df[df.linje==linjen].delay)//len(df[df.linje==linjen].delay)
        forsinkelser.append(gjennomsnittlig_forsinkelse)
        linjeNr.append(linjen)
        antall_kjoretoy.append(linje_liste.count(linjen))
    
    dataLinjer = {'Linje':linjeNr, 'gjens_forsinkelse':forsinkelser, 'Antall':antall_kjoretoy}
    df_linjer = pd.DataFrame(data=dataLinjer)
    df_linjer.sort_values(by=['Linje'],inplace=True)
    
    return df_linjer

def henter_tid(df):
    tid = list(df['sist_oppdatert'])
    tid.sort()
    aar = tid[-1][0:4]
    mnd = tid[-1][5:7]
    dag = tid[-1][8:10]
    klokken = tid[-1][11:]
    st.sidebar.header("Tall hentet " + dag +"/" + mnd +"/" + aar + " kl: " + klokken)




df = hent_data()

df_linjer = lager_linjedata(df)

henter_tid(df)
#st.sidebar.button("Oppdater",on_click=st.experimental_memo.clear()) Funker ikke
    


#page = st.sidebar.selectbox('Velg type',['Trikker','Busser','Ferger'])

st.title("Kollektivtrafikken i Oslo")

alle_linjer = set(df_linjer['Linje'])
alle_linjer_liste = list(alle_linjer)
alle_linjer_liste.sort()
alle_linjer_liste.insert(0,'Alle linjer')




#andel_forsinket = str(round(100*antall_forsinket/len(df),2)) + '%'
#st.metric(label="Andel forsinket", value=andel_forsinket)

col1, col2 = st.columns(2)

linje_valg = st.sidebar.selectbox("Velg linje",alle_linjer_liste)

if linje_valg == "Alle linjer":
    fig = px.bar(df_linjer, x='Linje', y='gjens_forsinkelse',color='gjens_forsinkelse',color_continuous_scale=["green", "red"],
                 labels={'gjens_forsinkelse':'Sekunder'},title="Gjennomsnittlig forsinkelse på buss og trikkelinjer i Oslo akkurat nå")
else:
    #Tegner kjøretøy på x-aksen og forsinkelse på y.
    df_linje_valg = df[df['linje'] == linje_valg]
    fig = px.bar(df_linje_valg, x=[i for i in range(len(df_linje_valg))], y='delay',color='delay',color_continuous_scale=["green", "red"],
                 labels={'x':'Kjøretøy' , 'delay':'Sekunder'},title="Forsinkelser på linje " + linje_valg)

#px.colors.qualitative.swatches()
fig.update(layout_coloraxis_showscale=False)
col1.plotly_chart(fig, use_container_width=True)


#fig = px.pie(df_linjer, values='Antall',names='Linje',title='Antall kjøretøy')
#col2.plotly_chart(fig, use_container_width=True)

df_pos = df

if linje_valg != "Alle linjer":
    df_pos = df_pos[df_pos['linje'] == linje_valg]
    
df_pos = df_pos.drop(['linje','sist_oppdatert','er_forsinket'],axis=1)
df_pos = df_pos[df_pos['lat']!=0]

#col2.map(df_pos,zoom=10)






col2.pydeck_chart(pdk.Deck(
     map_style='mapbox://styles/mapbox/light-v9',
     initial_view_state=pdk.ViewState(
         latitude=59.91,
         longitude=10.76,
         zoom=10,
         pitch=0,
     ),
     layers=[
         #pdk.Layer(
         #   'HexagonLayer',
         #   data=df_pos,
         #   get_position='[lon, lat]',
         #   radius=200,
         #   elevation_scale=4,
         #   elevation_range=[0, 1000],
         #   pickable=True,
         #   extruded=True,
         #),
         pdk.Layer(
             'ScatterplotLayer',
             data=df_pos,
             get_position='[lon, lat]',
             get_color='[delay, 255-delay, 0, 200]',
             get_radius=100 ,
         ),
     ],
 ))



#kart = st.selectbox("Vil du ha kart?",["ja","nei"],index=1)
