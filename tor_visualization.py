import os.path
from os import path
import sys
import time
import os
import socket
import IP2Location
from zipfile import ZipFile
import tarfile

import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

import plotly.graph_objects as go
import plotly.io




def get_tor_session():
    session = requests.session()
    tor_port = 9150
    # Tor uses the 9050 port as the default socks port
    session.proxies = {'http':  'socks5://127.0.0.1:{}'.format(tor_port),
					   'https': 'socks5://127.0.0.1:{}'.format(tor_port)}
    return session

def get_regular_session():
    session = requests.session()
    return session

def init(df, number_of_records): 
    tor_session = get_tor_session()
    reg_session = get_regular_session()
	
    df = make_requests(tor_session, reg_session, df, number_of_records)
    print("results")
    print(df)
    return df



def append_data(data, url, tor_req_time, elapsed_time, type, ip, rec):

    data['url'].append(url)
    data['time'].append(tor_req_time)
    data['elapsed_time'].append(elapsed_time)
    data['type'].append('regular')
    data['ip'].append(ip)
    data['geo'].append(rec)
    if rec is None:
        data['rec'].append(rec)
        data['country'].append(None)
        data['country_code'].append(None)
        data['region'].append(None)
        data['city'].append(None)
        data['latitude'].append(None)
        data['longitude'].append(None)
        data['zipcode'].append(None)
        data['timezone'].append(None)
    else:
        print("rec.country_long:", rec.country_long)
        print("rec.country_short:", rec.country_short)
        print("rec.region:", rec.region)
        print("rec.city:", rec.city)
        print("rec.latitude:", rec.latitude)
        print("rec.longitude:", rec.longitude)
        print("rec.zipcode:", rec.zipcode)
        print("rec.timezone:", rec.timezone)
        data['rec'].append(rec)
        data['country'].append(rec.country_long)
        data['country_code'].append(rec.country_short)
        data['region'].append(rec.region)
        data['city'].append(rec.city)
        data['latitude'].append(rec.latitude)
        data['longitude'].append(rec.longitude)
        data['zipcode'].append(rec.zipcode)
        data['timezone'].append(rec.timezone)
    return data


def make_requests(tor_session, reg_session, df, num_of_records) :
    database = IP2Location.IP2Location("IP2LOCATION-LITE-DB11.BIN")

    data = {'ip': [], 'url' : [] , "time" : [], "elapsed_time" : [], "type": [], "geo": [], "rec": [],
    "country": [], "country_code": [], "region": [], "city": [], "latitude": [], "longitude": [],
    "zipcode": [], "timezone": [] }
    count = 0
    df = df.sample(frac=1)
    for url in df["Domain"][0:num_of_records]: 
        count+=1
        print("\ncount:", count)
        full_url="http://"+url
        print("url:", url)
        try:
            ip = (socket.gethostbyname(url))
            rec = database.get_all(ip)
        except:
            ip = None
            rec = None

        # regular
        try:
            start = time.time()
            reg_req = reg_session.get(full_url)
            end = time.time()
            tor_req_time = reg_req.elapsed.total_seconds()
            elapsed_time = end-start
            data = append_data(data, url, tor_req_time, elapsed_time, 'regular', ip, rec)
            print("reg_req.elapsed.total_seconds():", tor_req_time)
            print("regular_elapsed_time:", elapsed_time)
        except:
            data = append_data(data, url, None, None, 'regular', ip, rec)

        # tor
        try: 
            start = time.time()
            tor_req = tor_session.get(full_url)
            end = time.time()
            tor_req_time = tor_req.elapsed.total_seconds()
            elapsed_time = end-start
            data = append_data(data, url, tor_req_time, elapsed_time, 'tor', ip, rec)
            print("tor_req.elapsed.total_seconds():", tor_req_time)
            print("tor_elapsed_time:", elapsed_time)
        except: 
            data = append_data(data, url, None, None, 'tor', ip, rec)
           
    return pd.DataFrame(data)


def get_data():
    filename = "top10milliondomains"
    extract(filename, 'csv')
    csv_filename = filename+".csv"
    db_filename = "IP2LOCATION-LITE-DB11"
    extract(db_filename, "BIN")
    bin_db_filename = db_filename+".BIN"
    df = read_data(csv_filename)
    print("df:", df)
    print("list(df.columns.values):", list(df.columns.values))
    print(df["Domain"])
    return df

def extract(filename, data_type):
    extract_filename = filename+"."+data_type
    tar_filename = filename+".tar"
    zip_filename = filename+".zip"

    if not os.path.exists(extract_filename):
        '''
        tf = tarfile.open(tar_filename)
        tf.extractall()
        '''
        with ZipFile(zip_filename) as zipObj:
            # Extract all the contents of zip file in current directory
            zipObj.extractall()




def get_c_codes():
    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv')
    print("df")
    print(df)
    print("df[df['COUNTRY'].str.startswith('U')")
    print(df[df['COUNTRY'].str.startswith("U")])
    c_codes_df = df.drop_duplicates(subset=['COUNTRY','CODE'])
    c_codes_df = c_codes_df[['COUNTRY','CODE']]
    #c_codes_df = df.groupby('CODE')[['COUNTRY', 'CODE']].count()
    c_codes_df = c_codes_df.rename(columns={"COUNTRY": "country", "CODE": "country_code"})
    c_codes_df.to_csv('c_codes_df.csv')
    print("dc_codes_df:", c_codes_df )


def dead_zones_viz(df):

    index_cols = ['rec', 'country_code', 'elapsed_time', 'country']
    map_df = df[index_cols]
    map_df.dropna(subset=['rec'])
    dead_zones_df = map_df[map_df['elapsed_time'].isna()]
    dead_zones_df['country_code'] = dead_zones_df['country'].str[:3].str.upper()
    dead_zones_df.to_csv('dead_zones_df.csv')
    map_df['count'] = map_df.groupby('country_code')['country_code'].transform('count')
    z_values = pd.Series( (map_df['count']) )
    BEL_Total = dead_zones_df[dead_zones_df.country_code == "BEL"].size
    grouped_counts = dead_zones_df.groupby(['country']).country_code.count()
    grouped_df = dead_zones_df.groupby(['country'])

    if not path.exists('c_codes_df.csv'):
        get_c_codes()
    c_codes_df = pd.read_csv('c_codes_df.csv') 
    c_unique = c_codes_df.drop_duplicates(subset=['country_code', "country"])
    df_unique = df.drop_duplicates(subset=['country_code', "country"])
    code_dict = {}
    for index, row in c_unique.iterrows():
        country = row.country
        df_code = country[:3].upper()
        c_code = row.country_code
        code_dict[df_code] = row.country_code

  
    dead_zones_df = dead_zones_df.rename(columns={"country_code": "code"})
    dead_zones_df['code'] = dead_zones_df['code'].map(code_dict)

    fig = go.Figure(data=go.Choropleth(
        locations = dead_zones_df['code'],
        z = z_values,
        text = dead_zones_df['country'],
        colorscale = 'Reds',
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_tickprefix = '',
        colorbar_title = 'Tor Dead Zones<br>No Tor Connection',
    ))

    fig.update_layout(
        title_text='Tor Dead Zones',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        ),
        annotations = [dict(
            x=0.55,
            y=0.1,
            xref='paper',
            yref='paper',
            text='Tor: <a href="https://www.torproject.org/">\
                The Tor Project</a>',
            showarrow = False
        )]
    )

    return fig




def map_viz(df):
    index_cols = ['country_code', 'elapsed_time', 'country']
    map_df = df[index_cols]
    map_df = map_df[map_df.notna()]
    map_df = map_df.dropna()
    map_df['country_code'] = map_df['country'].str[:3].str.upper()
    mean = df["elapsed_time"].mean()
    std =  df["elapsed_time"].std()


    map_df = map_df[map_df['elapsed_time'] < map_df['elapsed_time'].quantile(.80)]
    print("map_df")
    print(map_df)
    print("map_df['elapsed_time']")
    print(map_df['elapsed_time'])

    map_df.to_csv('map_df.csv')
    fig = go.Figure(data=go.Choropleth(
        locations = map_df['country_code'],
        z = map_df['elapsed_time'],
        text = map_df['country'],
        colorscale = 'Blues',
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_tickprefix = '',
        colorbar_title = 'Network Speed<br>Elapsed Time',
    ))

    fig.update_layout(
        title_text='Network Speed',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        ),
        annotations = [dict(
            x=0.55,
            y=0.1,
            xref='paper',
            yref='paper',
            text='Tor: <a href="https://www.torproject.org/">\
                The Tor Project</a>',
            showarrow = False
        )]
    )

    return fig



def read_data(filename):
    website_df = pd.read_csv(filename)
    return website_df


def handle_args():
    usage_err_msg = """\n ARGUMENTS ERROR \n\n 
    usage:  \n 
    'python tor_visualization.py --resume true' will load data from previous run and visualize the data on the world map \n \n  
    'python tor_visualization.py --test_size 100' will run the tor network speed tests on 100 different webservers \n \n 
    'python tor_visualization.py --save true' will save the graph to a file \n \n 
    'python tor_visualization.py --outfile mygraph.png' will save the graph to a file called  mygraph.png  \n \n 
    'python tor_visualization.py --display false' will prevent the visualization from being hosted on localhost \n \n 
    'python tor_visualization.py --resume true --mode dead_zones' will display the zones where the Tor network could not connect to a server \n \n
    """ 
    arguments = len(sys.argv) - 1
    print("arguments:", arguments)
    arg_dict = {}
    if( arguments % 2 != 0):
        print(usage_err_msg)
        exit(0)
    
    # output argument-wise
    key_index = 1
    while (arguments >= key_index):
        print("parameter %i: %s" % (key_index, sys.argv[key_index]))
        value_index = key_index + 1
        print("parameter %i: %s" % (value_index, sys.argv[value_index]))
        arg_dict[sys.argv[key_index]] = sys.argv[value_index]
        key_index = key_index + 2

    return arg_dict


'''
usage:   
    'python tor_visualization.py --resume true' will load data from previous run and visualize the data on the world map 
    'python tor_visualization.py --test_size 100' will run the tor network speed tests on 100 different webservers 
    'python tor_visualization.py --save true' will save the graph to a file 
    'python tor_visualization.py --outfile mygraph.png' will save the graph to a file called  mygraph.png 
    'python tor_visualization.py --display false will prevent the visualization from being hosted on localhost 
    'python tor_visualization.py --resume true --mode dead_zones'
'''

if __name__ == '__main__':
    output_filename = 'map_data.csv'
    arg_dict = handle_args()
    print("arg_dict")
    print(arg_dict)
    resume = False
    test_size = False
    size = 50



    if '--resume' in arg_dict:
        if(arg_dict['--resume'] == 'true'):
            resume = True
            df = pd.read_csv(output_filename) 

    if '--test_size' in arg_dict:
        if(arg_dict['--test_size'].isdigit()):
            test_size = True
            size = int(arg_dict['--test_size'])

    if resume == False:
        df = get_data()
        df = init(df, size)
        print("final data")
        print(df)
        print(df.columns)
        df.to_csv(output_filename)


    fig = map_viz(df)
    if '--mode' in arg_dict:
        if(arg_dict['--mode'] == 'dead_zones'):
            fig = dead_zones_viz(df)

            

    display = True
    save = False
    outfile = "tor_map.png"
    if '--display' in arg_dict:
        if(arg_dict['--display'] == 'false'):
            display = False

    if '--save' in arg_dict:
        if(arg_dict['--save'] == 'true'):
            save = True

    if '--outfile' in arg_dict:
        outfile = arg_dict['--outfile']
        save = True

    if display==True:
        fig.show()


    if save==True:
        fig.write_image(outfile)




    

