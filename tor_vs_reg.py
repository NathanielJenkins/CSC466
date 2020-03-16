import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

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

def main(): 
	urls = [
		{"url" : "https://www.google.com/", "label" : "google"},
		{"url" : "https://www.apple.com/", "label" : "apple"},
		{"url" : "https://www.yahoo.com/", "label" : "yahoo"},
		{"url" : "https://www.bing.com/", "label" : "bing"}

	]

	tor_session = get_tor_session()
	reg_session = get_regular_session()
	
	df = make_requests(tor_session, reg_session, urls)
	plot_values(df)

def make_requests(tor_session, reg_session, urls) :
	data = {'url' : [] , "time" : [], "type": []}
	for url_obj in urls: 
		tor_req = tor_session.get(url_obj['url'])
		reg_req = reg_session.get(url_obj['url'])

		# regular
		data['url'].append(url_obj['label'])
		data['time'].append(reg_req.elapsed.total_seconds())
		data['type'].append('regular')

		# tor
		data['url'].append(url_obj['label'])
		data['time'].append(tor_req.elapsed.total_seconds())
		data['type'].append('tor')


	return pd.DataFrame(data)
def plot_values(df):

	ax = sns.catplot(kind="bar", data=df, x='url', y = 'time', hue = 'type')
	ax.set(xlabel= "Destination", ylabel= "Time (seconds)")

	print ('showing the bar chart')
	plt.show()

if __name__ == '__main__':
	main()

