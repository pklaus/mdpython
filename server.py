#!/usr/bin/env python3

import mdstat
from bottle import route, run, view
import socket

@route('/api/mdstat/get_status')
def get_status():
    return mdstat.get_status()

@route('/mdstat/get_status')
@view('get_status')
def render_get_status():
    status = get_status()
    status['hostname'] = socket.gethostname()
    return status

run(host='localhost', port=8080, debug=True)

