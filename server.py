#!/usr/bin/env python3

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

