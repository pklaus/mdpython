#!/usr/bin/env python

# server.py - An application serving the software raid status as web page
#
# Copyright 2014 Philipp Klaus <philipp.klaus@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import mdstat
from bottle import Bottle, route, run, view, redirect
import socket

api = Bottle()
@api.route('/mdstat/get_status')
def get_status():
    return mdstat.get_status()

app = Bottle()
@app.route('/mdstat/get_status')
@view('get_status.html')
def render_get_status():
    status = get_status()
    status['hostname'] = socket.gethostname()
    return status

@app.route('/')
def refer():
    redirect('/mdstat/get_status')

app.mount('/api', api)

def main():
    #run(app, host='localhost', port=8080, debug=True)
    run(app, host='', port=8080)

if __name__ == "__main__":
    main()

