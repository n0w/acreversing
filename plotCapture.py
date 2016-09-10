#!/usr/bin/python3

import csv
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys

if __name__ == "__main__":
    p = argparse.ArgumentParser (description='Extracts values from Rigol CSV.')
    p.add_argument('file', metavar = 'file', type = str, help = 'File to process.')
    args = p.parse_args()


    data = np.genfromtxt(args.file, delimiter=',', skip_header=0, names=['x', 'y'])

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(data['x'], data['y'], color='r', label='the data')

    plt.show()