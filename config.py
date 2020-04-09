
import argparse

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

ds_parser = argparse.ArgumentParser()

ds_parser.add_argument("--fetch_all", type=str2bool,
                      default=False,
                      help="Fetch all the onion links")

ds_parser.add_argument("--clear", type=str2bool,
                      default=False,
                      help="Clear all saved data")

ds_parser.add_argument("--resume", type=str2bool,
                      default=False,
                      help="Visualize already saved data")

ds_parser.add_argument("--display", type=str2bool,
                      default=True,
                      help="Display the graph")

ds_parser.add_argument("--save", type=str2bool,
                      default=True,
                      choices=[False, True],
                      help="Save the graph to a file")

ds_parser.add_argument("--outfile", type=str,
                      default="onion_graph.png",
                      help="filename to save the graph")

ds_parser.add_argument("--timeout", type=int,
                       default=300,
                       help="Default timeout for trying to connect to a server")

ds_parser.add_argument("--fetch_size", type=int,
                       default=30,
                       help="Amount of sites to fetch")

ds_parser.add_argument("--sample_size", type=int,
                       default=20,
                       help="Amount of sites to graph")

ds_parser.add_argument("--mode", type=str,
                       default='markers',
                       choices=['markers', 'lines', 'all'],
                       help="Mode to plot the data")



def get_ds_config():
    config, unparsed = ds_parser.parse_known_args()
    return config, unparsed


