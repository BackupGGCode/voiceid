#!/usr/bin/env python

from voiceid import split_gmm

import sys, struct


if __name__ == '__main__':
	split_gmm( sys.argv[1] , '.')
