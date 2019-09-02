#! /usr/bin/env python3

import sys
import base64

if len( sys.argv ) == 2:
   print( '{} -> {}'.format( sys.argv[1], base64.b64encode(sys.argv[1].encode( 'ascii' )) ) )
else:
   print( 'usage: encode.py string' )

