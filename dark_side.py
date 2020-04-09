import sys
from pathlib import Path
from urllib.request import urlopen
import time
import re
import numpy as np
import random
import os
import shutil
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px

import math
from config import get_ds_config

#Importing Stem libraries
from stem import Signal
from stem.control import Controller
import socks, socket

html_dir = "html"
data_dir ="data"
metrics_file = "metrics.log"


def check_paths():
    # define the access rights
    access_rights = 0o755
    html_path =  Path.cwd().joinpath(html_dir)
    print("html_path:", html_path)
    if not os.path.isdir(html_path):
        os.mkdir(html_path, access_rights)

    data_path =  Path.cwd().joinpath(data_dir)
    print("data_path:", data_path)
    if not os.path.isdir(data_path):
        os.mkdir(data_path, access_rights)
        
    metrics_path = Path.cwd().joinpath(data_dir, metrics_file)
    if not os.path.exists(metrics_path):
        with open(metrics_path, 'w'): pass





def write_image(fig, filename):
    path = data_dir+'/'+filename
    print("path:", path)
    fig.write_image(path)

def read_data(filename, dirPath=data_dir, mode='r'):
    path =  Path.cwd().joinpath(dirPath, filename)
    if dirPath is None:
        path = filename
    f = open(path, mode)
    data = f.read()
    #print(data)
    return data

def write_data(data, filename, dirPath=data_dir, mode='a'):
    path =  Path.cwd().joinpath(dirPath, filename)
    print("path:", path)
    if dirPath is None:
        path = filename
    m = open(path, mode)
    m.write(data)
    m.close()




def call_onion_hub():
    onion_hub = "https://github.com/alecmuffett/real-world-onion-sites"

    start_time = time.time()
    received_response = urlopen(onion_hub)
    if 'text/html' in received_response.getheader('Content-Type'):
        data_bytes = received_response.read()
        html_data_string = data_bytes.decode("latin-1")
    end_time = time.time()
    elapsed_time = end_time-start_time
    metrics = onion_hub+":"+str(elapsed_time)
    #print(html_data_string)
    onion_links = re.findall(r'\b(\w+\.onion)\b', html_data_string)
    print(onion_links)
    return onion_links


def dark_crawl(fetch_size=50, timeout=300):

        onion_hub_links = call_onion_hub()
        print("len(onion_hub_links):", len(onion_hub_links))
        print(onion_hub_links)
        #print(onion_links)
        #s=list(range(len(onion_links)))
        random.shuffle(onion_hub_links, random.random)
        #links = random.shuffle(onion_links)
        print(onion_hub_links)
        total_amount = len(onion_hub_links)
        if fetch_size == -1:
            fetch_size = total_amount

        count = -1
        for web_url in onion_hub_links[0:fetch_size]:
            count += 1
            print("count:", count)
            print("fetch_size:", fetch_size)
            print("total_amount:", total_amount)
            try: 
                full_url = "http://"+web_url+"/"
                start_time = time.time()
                received_response = urlopen(full_url, timeout=timeout)
                if 'text/html' in received_response.getheader('Content-Type'):
                    data_bytes = received_response.read()
                    html_data_string = data_bytes.decode("latin-1")
                end_time = time.time()
                elapsed_time = end_time-start_time
                metrics = web_url+":"+str(elapsed_time)+"~"
                filename = re.sub(r'[^\w\s]','', web_url)+".html"

                write_data(metrics, metrics_file)
                write_data(html_data_string, filename, dirPath=html_dir)
                
            except Exception as err:
                print(Exception, err)
                


def init_stem():
    #Initiating Connection
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

    # TOR SETUP GLOBAL Vars
    SOCKS_PORT = 9050  # TOR proxy port that is default from torrc, change to whatever torrc is configured to
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", SOCKS_PORT)
    socket.socket = socks.socksocket

    # Perform DNS resolution through the socket
    def getaddrinfo(*args):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]

    socket.getaddrinfo = getaddrinfo


def analyze_results():
    data = read_data(metrics_file)
    print(data)
    return data




def plot_all_results(metrics):
    random.shuffle(metrics)
    y = []
    x_labels = []
    for metric in metrics:
        vals = metric.split(":")
        if len(vals) > 1:
            y.append(float(vals[1]))
            x_labels.append(vals[0].split(".")[0])

    x = np.arange(len(y))
    title_info = str(len(y))+" Dark Web Sample Requests with a Mean Request Time of "+str(np.mean(y))+" Seconds"
    d = {"time(seconds)": y, "website": x_labels}
    df = pd.DataFrame(data=d)
    print("len(x_labels):", len(x_labels))
    fig = px.scatter(df, x="time(seconds)", y="website")
    fig.update_layout(
        title_text=title_info
    )
    return fig



def plot_data(metrics, sample_size=20, mode='markers'):
    print("mode", mode)
    if(mode=='all'):
        return plot_all_results(metrics)

    print("len(metrics):", len(metrics))
    print("metrics:", metrics)
    random.shuffle(metrics)
    chosen_metric = metrics[0:sample_size]
    y = []
    x_labels = []
    for metric in chosen_metric:
        vals = metric.split(":")
        if len(vals) > 1:
            y.append(float(vals[1]))
            x_labels.append(vals[0].split(".")[0])

    
    title = "Random Sample of "+str(len(y))+" Onion Server Requests with a Mean Time of "+str(np.mean(y))+" Seconds"
    x = np.arange(len(y))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_labels, y=y,
                    mode=mode,
                    name='onion_times'))

    fig.update_layout(
        title=title,
        xaxis_title="Onion Website Request",
        yaxis_title="Onion Request Elapsed Time (Seconds)",
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="#7f7f7f"
        )
    )
    return fig


def wipe_data():
    metrics_path =  Path.cwd().joinpath(data_dir, metrics_file)
    html_folder = Path.cwd().joinpath(html_dir)
    if os.path.exists(metrics_path):
        os.remove(metrics_path) 
    if os.path.isdir(html_folder):
        shutil.rmtree(html_folder)


def handle_args():
    usage_err_msg = """\n ARGUMENTS ERROR \n\n 
    usage:  \n 
    'python dark_side.py --resume false' fetch new data to graph \n \n  
    'python dark_side.py --test_size 100' will plot x amount of the results from different .onion sites \n \n 
    'python dark_side.py --save true' will save the graph to a file \n \n 
    'python dark_side.py --outfile mygraph.png' will save the graph to a file called  mygraph.png  \n \n 
    'python dark_side.py --display false' will prevent the visualization from being hosted on localhost \n \n 
    'python dark_side.py --mode lines' will display the results on a line plot \n \n
    'python dark_side.py --clear true' will clear all the stored data \n \n
    'python dark_side.py --fetch_all true' will crawl all the ~550 .onion sites \n \n
    'python dark_side.py --mode all' will plot the request speeds to all the .onion site in the metrics.log and not just a sample of the sites \n \n
    'python dark_side.py --timeout 100' will set the timeout for the request to 100 seconds \n \n
    """ 
    arguments = len(sys.argv) - 1
    print("arguments:", arguments)
    arg_dict = {}
    if( arguments % 2 != 0 ):
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



"""
usage:  
'python dark_side.py --resume true' fetch new data to graph
'python dark_side.py --test_size 100' will plot x amount of the results from different .onion sites 
'python dark_side.py --save true' will save the graph to a file
'python dark_side.py --outfile mygraph.png' will save the graph to a file called  mygraph.png 
'python dark_side.py --display false' will prevent the visualization from being hosted on localhost
'python dark_side.py --resume true --mode line_plot' will display the results on a line_plot
'python dark_side.py --mode lines' will display the results on a line plot 
'python dark_side.py --clear true' will clear all the stored data
'python dark_side.py --fetch_all true' will fetch all onion links
'python dark_side.py --mode all' will plot the request speeds to all the .onion site in the metrics.log and not just a sample of the sites
'python dark_side.py --timeout 100' will set the timeout for the request to 100 seconds
""" 
if __name__=='__main__':

    config, unparsed = get_ds_config()

    check_paths()

    if config.clear:
        wipe_data()
        config.resume = False

    print("config.fetch_all:", config.fetch_all)
    if config.fetch_all:
        config.fetch_size = -1
        config.resume = False

    if not config.resume:
        init_stem()
        dark_crawl(config.fetch_size, config.timeout)

    metrics = analyze_results()
    metrics = metrics.split("~")
    print("metrics:", metrics)

    fig = plot_data(metrics, config.sample_size, mode=config.mode)

    print("config.display:", config.display)
    if config.display==True:
        fig.show()

    if config.save==True:
        write_image(fig, config.outfile)



    