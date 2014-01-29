#!/usr/bin/env python
# -*- coding: utf-8 -*-

#       mdstat.py
#       
#       Copyright 2011 Alexey Zotov <alexey.zotov@gmail.com>
#       Copyright 2014 Philipp Klaus <philipp.klaus@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       mdstat.py is originally from code.google.com/p/softraid-monitor :
#       http://code.google.com/p/softraid-monitor/source/browse/contents/code/mdstat.py

def get_status():
    result = {
        'personalities': '',
        'devices': {},
        'unused devices': ''
    }

    try:
        with open('/proc/mdstat') as mdstat:
            parse_mdstat(mdstat, result)
    except IOError:
        pass

    return result

def parse_mdstat(mdstat, result):
    last_dev = None
    
    for line in mdstat:
        if line.startswith('Personalities : '):
            result['personalities'] = line[16:]
        elif line.startswith('unused devices: '):
            result['unused devices'] = line[16:]
        elif line.startswith(' '):
            if not last_dev:
                continue
            parse_line(line.strip(), result['devices'][last_dev])
        else:
            last_dev = parse_dev(line, result)

def parse_dev(line, result):
    parts = line.split(' : ', 1)
    if len(parts) != 2:
        return

    dev_name = parts[0]
    dev_line = parts[1]

    device = {
        'active': False,
        'read_only': '',
        'pers': '',
        'disks': {},
        'blocks': 0,
        'super': '',
        'resync': {
            'type': ''
        },
        'bitmap': {}
    }

    if dev_line.startswith('active'):
        device['active'] = True
        dev_line = dev_line[7:]
    elif dev_line.startswith('inactive'):
        dev_line = dev_line[9:]
    else:
        return

    if device['active']:
        if dev_line.startswith('('):
            parts = dev_line.split(') ', 1)
            if len(parts) != 2:
                return

            device['read_only'] = parts[0][1:]
            dev_line = parts[1]

        parts = dev_line.split(' ', 1)
        device['pers'] = parts[0]
        dev_line = len(parts) > 1 and parts[1] or ''

    if dev_line.startswith('super'):
        device['super'] = dev_line[6:]
    else:
        for disk in dev_line.split():
            parts = disk.split('[')
            if len(parts) != 2:
                return

            disk_name = parts[0]

            parts = parts[1].split(']')
            try:
                disk_number = int(parts[0])
            except ValueError:
                return

            disk_type = len(parts) > 1 and parts[1] or ''

            device['disks'][disk_number] = {
                'name': disk_name,
                'type': disk_type
            }

    result['devices'][dev_name] = device
    return dev_name

def parse_line(line, device):
    if line.startswith('['):
        parse_resync(line, device['resync'])
    elif line.startswith('resync='):
        parts = line.split('=', 1)
        if len(parts) != 2:
            return
        if parts[1] not in ('DELAYED', 'PENDING'):
            return

        device['resync']['type'] = 'resync'
        device['resync']['finish'] = parts[1]
    elif line.startswith('bitmap: '):
        pass # TODO: parse_bitmap
    else:
        parse_blocks(line, device)

def parse_resync(line, resync):
    parts = line.split(']  ', 1)
    if len(parts) != 2:
        return

    parts = parts[1].split(' =', 1)
    if len(parts) != 2:
        return
    if parts[0] not in ('reshape', 'check', 'resync', 'recovery'):
        return

    result = {
        'type': parts[0]
    }

    parts = parts[1].split('% (', 1)
    if len(parts) != 2:
        return

    try:
        result['percent'] = float(parts[0].strip())
    except ValueError:
        return

    parts = parts[1].split(') ', 1)
    if len(parts) != 2:
        return

    blocks = parts[0].split('/')
    if len(blocks) != 2:
        return

    try:
        result['blocks'] = int(blocks[0])
        result['max_blocks'] = int(blocks[1])
    except ValueError:
        return

    parts = parts[1].split()
    if len(parts) != 2:
        return

    finish = parts[0].split('=')
    if len(finish) != 2:
        return

    result['finish'] = finish[1]

    speed = parts[1].split('=')
    if len(speed) != 2:
        return

    result['speed'] = speed[1]

    resync.update(result)

def parse_blocks(line, device):
    parts = line.split(' blocks')
    if len(parts) != 2:
        return

    try:
        device['blocks'] = int(parts[0])
    except ValueError:
        return

    line = parts[1].strip()

    if line.startswith('super '):
        line = line[6:]
        parts = line.split(' ', 1)
        device['super'] = parts[0]

        line = len(parts) == 2 and parts[1] or ''

    if line and device['active']:
        if device['pers'] == 'raid1':
            parse_raid1_status(line, device)
        elif device['pers'] in ('raid4', 'raid5', 'raid6'):
            parse_raid5_status(line, device)
        elif device['pers'] == 'raid10':
            parse_raid10_status(line, device)
        
def parse_raid1_status(line, device):
    parts = line.split('] [')
    if len(parts) != 2:
        return

    result = {
        'raid': {
            'status': parts[1][:-1]
        }
    }

    disks = parts[0][1:].split('/')
    if len(disks) != 2:
        return

    try:
        result['raid'].update({
            'total': int(disks[0]),
            'nondegraded': int(disks[1]),
            'degraded': int(disks[0]) - int(disks[1])
        })
    except ValueError:
        return

    device.update(result)

def parse_raid5_status(line, device):
    parts = line.split('] [')
    if len(parts) != 2:
        return

    result = {
        'raid': {
            'status': parts[1][:-1]
        }
    }

    parts = parts[0].split(' [')
    if len(parts) != 2:
        return

    attrs = parts[0].split(', ')
    if len(attrs) != 3:
        return

    level = attrs[0].split('level ')
    if len(level) != 2:
        return

    chunk = attrs[1].split(' chunk')
    if len(chunk) != 2:
        return

    algorithm = attrs[2].split('algorithm ')
    if len(algorithm) != 2:
        return

    result['raid'].update({
        'level': level[1],
        'chunk': chunk[0],
        'algorithm': algorithm[1]
    })

    disks = parts[1].split('/')
    if len(disks) != 2:
        return

    try:
        result['raid'].update({
            'total': int(disks[0]),
            'nondegraded': int(disks[1]),
            'degraded': int(disks[0]) - int(disks[1])
        })
    except ValueError:
        return

    device.update(result)

def parse_raid10_status(line, device):
    parts = line.split('] [')
    if len(parts) != 2:
        return

    result = {
        'raid': {
            'status': parts[1][:-1]
        }
    }

    parts = parts[0].split(' [')
    if len(parts) != 2:
        return

    line = parts[0]

    if line:
        chunks = line.split(' chunks')
        if len(chunks) == 2:
            result['raid']['chunk'] = chunks[0].strip()
            line = chunks[1]

    if line:
        near_copies = line.split(' near-copies')
        if len(near_copies) == 2:
            try:
                result['raid']['near-copies'] = int(near_copies[0].strip())
            except ValueError:
                return
            line = near_copies[1]

    if line:
        offset_copies = line.split(' offset-copies')
        if len(offset_copies) == 2:
            try:
                result['raid']['offset-copies'] = int(offset_copies[0].strip())
            except ValueError:
                return
            line = offset_copies[1]

    if line:
        far_copies = line.split(' far-copies')
        if len(far_copies) == 2:
            try:
                result['raid']['far-copies'] = int(far_copies[0].strip())
            except ValueError:
                return

    disks = parts[1].split('/')
    if len(disks) != 2:
        return

    try:
        result['raid'].update({
            'total': int(disks[0]),
            'nondegraded': int(disks[1]),
            'degraded': int(disks[0]) - int(disks[1])
        })
    except ValueError:
        return

    device.update(result)


if __name__ == '__main__':
    import pprint
    pprint.pprint(get_status())

