#! /usr/bin/env python3

import sys
import base64


if len( sys.argv ) == 2:
   print( '{} -> {}'.format( sys.argv[1], base64.b64decode( sys.argv[1] ).decode( 'utf-8'  ) ))
else:
   print( 'usage: encode.py string' )

