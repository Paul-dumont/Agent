#!/usr/bin/env python-real

import sys
import argparse


def main(input):
    print("je suis content")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('prompt',type=str)
    parser.add_argument("inputfolder",type=str)
    parser.add_argument('outputfolder',type=str)

    args = parser.parse_args()
    main(args)
