import sys
from pathlib import Path
from urllib.request import urlopen
import time
import re
import numpy as np
import random
import os
import plotly.graph_objects as go
import shutil

import math


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
    fig.write_image(path)

def read_data(filename, dirPath=data_dir, mode='r'):
    path =  Path.cwd().joinpath(dirPath, filename)
    if dirPath is None:
        path = filename
    f = open(path, mode)
    data = f.read()
    print(data)
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


def dark_crawl(fetch_size=50):

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
                received_response = urlopen(full_url)
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
        controller.authenticate("16:95A1A7A9D14B5F216054930577B2E77C206A3FCA654F7546555FA26A94 \\n")
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






def plot_data(metrics, sample_size=20, mode='markers'):
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

    x = np.arange(len(y))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_labels, y=y,
                    mode=mode,
                    name='onion_times'))

    fig.update_layout(
        title="Random Sample of Onion Server Times",
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
""" 
if __name__=='__main__':
    arg_dict = handle_args()
    print("arg_dict")
    print(arg_dict)

    #Default Arguments
    resume = True
    display = True
    save = False
    fetch_size = 30
    sample_size = 20
    mode = 'markers'
    outfile = "onion_graph.png"
    fetch_all = False


    check_paths()

    if '--clear' in arg_dict:
        if (arg_dict['--clear'] == 'true'):
            wipe_data()
            resume = False

    if '--resume' in arg_dict:
        if (arg_dict['--resume'] == 'false'):
            resume = False

    if '--fetch_size' in arg_dict:
        if(arg_dict['--fetch_size'].isdigit()):
            fetch_size = int(arg_dict['--fetch_size'])

    if '--fetch_all' in arg_dict:
        if (arg_dict['--fetch_all'] == 'true'):
            fetch_size = -1

    if not resume:
        init_stem()
        dark_crawl(fetch_size)

    metrics = analyze_results()
    metrics = metrics.split("~")
    print("metrics:", metrics)
    if '--test_size' in arg_dict:
        if(arg_dict['--test_size'].isdigit()):
            sample_size = int(arg_dict['--test_size'])


    if '--mode' in arg_dict:
        if(arg_dict['--mode'] == 'lines'):
            mode = 'lines'
        if(arg_dict['--mode'] == 'scatter_plot'):
            mode = 'scatter_plot'

    fig = plot_data(metrics, sample_size, mode=mode)

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
        write_image(fig, outfile)



    