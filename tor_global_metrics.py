import time
import os
from pathlib import Path
import os.path
from os import path
import sys
import time
import socket
import IP2Location
from zipfile import ZipFile
import tarfile

import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

data_dir ="data"

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

def init(df): 
    tor_session = get_tor_session()
    reg_session = get_regular_session()
	
    df = make_requests(tor_session, reg_session, df)
    print("results")
    print(df)

def make_requests(tor_session, reg_session, df) :
    database = read_bin("IP2LOCATION-LITE-DB11.BIN")

    data = {'ip': [], 'url' : [] , "time" : [], "elapsed_time" : [], "type": [], "geo": []}
    count = 0
    df = df.sample(frac=1)
    for url in df["Domain"][0:20]: 
        count+=1
        print("\ncount:", count)
        full_url="http://"+url
        print("url:", url)
        try:
            ip = (socket.gethostbyname(url))
            rec = database.get_all(ip)
            print("rec.country_long:", rec.country_long)
            print("rec.region:", rec.region)
            print("rec.city:", rec.city)
            print("rec.latitude:", rec.latitude)
            print("rec.longitude:", rec.longitude)
            print("rec.zipcode:", rec.zipcode)
            print("rec.timezone:", rec.timezone)
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
            data['url'].append(url)
            data['time'].append(tor_req_time)
            data['elapsed_time'].append(elapsed_time)
            data['type'].append('regular')
            data['ip'].append(ip)
            data['geo'].append(rec)
            print("reg_req.elapsed.total_seconds():", tor_req_time)
            print("regular_elapsed_time:", elapsed_time)
        except:
            data['url'].append(url)
            data['time'].append(None)
            data['elapsed_time'].append(None)
            data['type'].append('regular')
            data['ip'].append(ip)
            data['geo'].append(rec)


        # tor
        try: 
            start = time.time()
            tor_req = tor_session.get(full_url)
            end = time.time()
            tor_req_time = tor_req.elapsed.total_seconds()
            elapsed_time = end-start
            data['url'].append(url)
            data['time'].append(tor_req_time)
            data['elapsed_time'].append(elapsed_time)
            data['type'].append('tor')
            data['ip'].append(ip)
            data['geo'].append(rec)
            print("tor_req.elapsed.total_seconds():", tor_req_time)
            print("tor_elapsed_time:", elapsed_time)
        except: 
            data['url'].append(url)
            data['time'].append(None)
            data['elapsed_time'].append(None)
            data['type'].append('tor')
            data['ip'].append(ip)
            data['geo'].append(rec)
           
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
    extract_filename =  Path.cwd().joinpath(data_dir, filename+"."+data_type)
    #tar_filename = data_dir+"/"+filename+".tar"
    zip_filename =  Path.cwd().joinpath(data_dir, filename+".zip")

    if not os.path.exists(extract_filename.absolute()):
        '''
        tf = tarfile.open(tar_filename)
        tf.extractall()
        '''
        with ZipFile(zip_filename.absolute()) as zipObj:
            # Extract all the contents of zip file in current directory
            zipObj.extractall(path=data_dir)



def read_data(filename, inDataDir=True):
    path =  Path.cwd().joinpath(data_dir, filename)
    if not inDataDir:
        path = filename
    df = pd.read_csv(path)
    return df

def read_bin(filename, inDataDir=True):
    path =  Path.cwd().joinpath(data_dir, filename)
    if not inDataDir:
        path = filename
    database = IP2Location.IP2Location(path)
    return database

def write_csv(df, filename):
    path = data_dir+'/'+filename
    df.to_csv(path)
    return df

def write_image(fig, filename):
    path = data_dir+'/'+filename
    fig.write_image(path)

if __name__ == '__main__':
    df = get_data()
    init(df)

