# coding: utf-8

# pip install requests
# pip install geoip2
# pip install pyyaml
# yum install MySQL-python

import os
import re
import sys
import datetime
import pytz
import csv
import yaml
import argparse
import requests
import zipfile
import tarfile
import geoip2.database
import socket
from netaddr import *
import MySQLdb

def main():
    """ load arguments """
    parser = argparse.ArgumentParser(description=u"this script args...")
    parser.add_argument("-c", "--config", type=str, default="./config.yaml", help=u"defautl is ./config.yaml")
    args = parser.parse_args()

    """ load config yaml """
    conf_file= args.config
    config = def_load_config(conf_file)
    conf_geo = config['geolite2']
    conf_tz = config['timezone']
    conf_mysql = config['mysql']

    """ mmdb,csv_geo download url, destination filename variable """
    geo_mmdb_url = conf_geo['mmdb']['city']['url']
    geo_mmdb_dst = geo_mmdb_url.split('/')[-1]
    geolite2_mmdb = conf_geo['mmdb']['city']['mmdb']
    geo_csv_url = conf_geo['csv']['country']['url']
    geo_csv_dst = geo_csv_url.split('/')[-1]
    geo_csv_list =  conf_geo['csv']['country']['csv']

    """ timezone csv download url, destination filename variable """
    tz_url = conf_tz['url']
    tz_csv_dst = tz_url.split('/')[-1]
    tz_csv_list = conf_tz['csv']

    """ download and unarchive """
    def_download(geo_mmdb_url, geo_mmdb_dst)
    def_download(geo_csv_url, geo_csv_dst)
    def_download(tz_url, tz_csv_dst)

    mmdb_read_city = def_unarchive_mmdb(geo_mmdb_dst, geolite2_mmdb)

    geo_csv_read_list = def_unarchive_zip(geo_csv_dst, geo_csv_list)
    geo_csv_read_ipv4 = geo_csv_read_list[0]
    geo_csv_read_ipv6 = geo_csv_read_list[1]
    ipv4_prefix_list = def_read_csv(0, geo_csv_read_ipv4)
    ipv6_prefix_list = def_read_csv(0, geo_csv_read_ipv6)

    csv_read_tz = def_unarchive_zip(tz_csv_dst, tz_csv_list)
    tz_list = def_read_csv(2, csv_read_tz[0])

    """ create import geo_ip data """
    ipv4_datas = def_create_datas(mmdb_read_city, tz_list, ipv4_prefix_list)
    ipv6_datas = def_create_datas(mmdb_read_city, tz_list, ipv6_prefix_list)

    """ import mysql table geo_ip iniialize... """
    if conf_mysql['init'] == 'True':
        def_truncate_mysql(conf_mysql)

    """ import mysql table geo_ip database openBMP:(defaultname) """
    def_import_mysql(conf_mysql, ipv4_datas)
    def_import_mysql(conf_mysql, ipv6_datas)

def def_load_config(conf_file):
    try:
        with open(conf_file, 'r') as f:
            config = yaml.load(f)
    except:
        print "Error... read file error %s" % yaml
        sys.exit(1)

    return config

def def_download(url, dstfile):
    res = requests.get(url)
    if res.status_code == 200:
        with open(dstfile, 'wb') as localfile:
            localfile.write(res.content)
        print "Succeed... download succeed %s" % url
    else:
        print "Error... download error %s" % url
        sys.exit(1)

def def_unarchive_mmdb(t_file, geolite2_mmdb):
    try:
        with tarfile.open(t_file) as t:
            t.extractall()
        print "Succeed... unarchive %s" % t_file
    except:
        print "Error... unarchive %s" % t_file
        sys.exit(1)

    mmdb_list = []
    for tarinfo in t:
        mmdb_list.append(tarinfo.name)
    geolite2mmdbfile = [m for m in mmdb_list if geolite2_mmdb in m]

    return geolite2mmdbfile[0]

def def_unarchive_zip(z_file, files):
    try:
        with zipfile.ZipFile(z_file) as z:
            unarchive_list = z.namelist()
            if z_file == 'timezonedb.csv.zip':
                unarchive_list.remove('timezone.csv')
            file_list = []
            for f in files:
                csvfile = [s for s in unarchive_list if f in s]
                z.extract(csvfile[0])
                file_list.append(csvfile[0])

        print "Succeed... unarchive %s" % z_file
#        print file_list
    except:
        print "Error... unarchive %s" % z_file
        sys.exit(1)

    return file_list

def def_read_csv(index, csvfile):
    if os.path.exists(csvfile):
        pass
    else:
        print "Error... %s does not exit" % csvfile
        sys.exit(1)

    with open(csvfile) as f:
        csv_reader = csv.reader(f)
        prefix_list = []
        for row in csv_reader:
            prefix_list.append(row[index])
    prefix_list.pop(0)

    return prefix_list

def def_create_record(mmdb_geolite2, tz_list, ip):
    ip_start = str(ip.network)
    ip_end = str(ip.broadcast)
    addr_type = 'ipv' + str(ip.version)
    if addr_type == 'ipv4':
        addressfamily = 2
    elif addr_type == 'ipv6':
        addressfamily = 10

    reader = geoip2.database.Reader(mmdb_geolite2, ['en'])
    record = reader.city(ip_start)

    """ country insert validate """
    n = record.country.iso_code
    if n is None:
        country = str('')
    elif len(str(n.encode('utf-8'))) > 2:
        country = str('')
    else:
        country = str(n)

    """ city insert validate """
    u = record.city.name
    if u is None:
        city = "None"
    elif len(str(u.encode('utf-8'))) > 80:
        city = "None"
    elif re.match(r'^[-(),a-zA-Z0-9\s]*$', str(u.encode('utf-8'))):
        city = u
    else:
        city = "None"

    """ latitude,longitude insert validate """
    la = record.location.latitude
    lo = record.location.longitude
    if la is None or lo is None:
        latitude = 0
        longitude = 0
    else:
        latitude = la
        longitude = lo

    """ connection type enum filter """
    connection_type_list = [
        'dialup',
        'isdn',
        'cable',
        'dsl',
        'fttx',
        'wireless'
    ]

    if str(record.traits.user_type) in connection_type_list:
        connection_type = record.traits.user_type
    else:
        connection_type = None

    """ get utc offset from timezone """
    t = record.location.time_zone
    if t in tz_list:
        pacific_now = datetime.datetime.now(pytz.timezone(t))
        timezone_offset = pacific_now.utcoffset().total_seconds()/60/60
    else:
        timezone_offset = 0

    """ mapping into mysql base tables `geo_ip`
    addr_type: enum('ipv4','ipv6')
        - addr_type
    ip_start: varbinary(16)
        - socket.inet_pton(addressfamily, ip_start)
    ip_end: varbinary(16)
        - socket.inet_pton(addressfamily, ip_end)
    country:    char(2)
        - str(record.country.iso_code)
    stateprov: varchar(80)
        - str(record.subdivisions.most_specific.iso_code)
    city:       varchar(80)
        - str(record.city.name)
    latitude: float
        - record.location.latitude
    longitude: float
        - record.location.longitude
    timezone_offset: float
        - timezone_offset
    timezone_name: varchar(64)
        - str(record.location.time_zone)
    isp_name: varchar(128)
        - str(record.traits.isp)
    connection_type: enum('dialup','isdn','cable','dsl','fttx','wireless')
        - ecord.traits.user_type
    organization_name: varchar(128)
        - record.traits.organization
    """

    geo_data = [
        addr_type,
        socket.inet_pton(addressfamily, ip_start),
        socket.inet_pton(addressfamily, ip_end),
        country,
        str(record.subdivisions.most_specific.iso_code),
        city,
        latitude,
        longitude,
        timezone_offset,
        str(record.location.time_zone),
        str(record.traits.isp),
        connection_type,
        record.traits.organization
    ]

    return geo_data

def def_create_datas(mmdb_read_city, tz_list, prefix_list):
    datas = []
    for ipaddress in prefix_list:
        ip = IPNetwork(ipaddress)
        r = def_create_record(mmdb_read_city, tz_list, ip)
        datas.append(r)

    return datas

def def_truncate_mysql(conf_mysql):
    conn = MySQLdb.connect(
        user = conf_mysql['user'],
        passwd = conf_mysql['passwd'],
        host = conf_mysql['host'],
        db = conf_mysql['db'],
        charset = conf_mysql['charset'],
        use_unicode = True
    )

    c = conn.cursor()
    sql_truncate = """
    TRUNCATE TABLE geo_ip;
    """

    try:
        print 'start mysql truncate table geo_ip'
        c.execute(sql_truncate)
    except Exception as e:
        print(e)

def def_import_mysql(conf_mysql, datas):
    conn = MySQLdb.connect(
        user = conf_mysql['user'],
        passwd = conf_mysql['passwd'],
        host = conf_mysql['host'],
        db = conf_mysql['db'],
        charset = conf_mysql['charset'],
        use_unicode = True
    )
    c = conn.cursor()
    sql_select_count4 = """
    SELECT COUNT(*) FROM geo_ip WHERE addr_type = 'ipv4'
    """
    sql_select_count6 = """
    SELECT COUNT(*) FROM geo_ip WHERE addr_type = 'ipv6'
    """
    sql_insert = """
    INSERT INTO geo_ip
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        print 'start mysql insert... %s record ' % datas[0][0]
        c.executemany(sql_insert, datas)
        conn.commit()
    except Exception as e:
        print(e)

    try:
        if datas[0][0] == 'ipv4':
            sql_select = sql_select_count4
        elif datas[0][0] == 'ipv6':
            sql_select = sql_select_count6
        c.execute(sql_select)
        print '%s record Num: ' % datas[0][0] + str(c.fetchone()[0])

    except Exception as e:
        print(e)

    finally:
        c.close()
        conn.close()

main()
