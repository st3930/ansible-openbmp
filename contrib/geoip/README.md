## Intoroduction
geoip database of mysql is samples. and Not prepaerd import tools.
this script is import tools, this geodata referenced from maxmaind geplite2(free).

maxmaid: https://geolite.maxmind.com/download/geoip/database/

## Required
```
yum install MySQL-python
pip install geoip2
pip install pytz
pip install netaddr
```

## Confirmed version
- CentOS7.6
- Python2.7

## Command
```
python geoip2mysql.py [-c|--config ./config.yaml]
```

## config

```
geolite2:
  mmdb:
    city:
      url: 'https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz'
      mmdb: 'GeoLite2-City.mmdb'
  csv:
    country:
      url: 'https://geolite.maxmind.com/download/geoip/database/GeoLite2-Country-CSV.zip'
      csv:
        - 'GeoLite2-Country-Blocks-IPv4.csv'
        - 'GeoLite2-Country-Blocks-IPv6.csv'
timezone:
  url: 'https://timezonedb.com/files/timezonedb.csv.zip'
  csv:
    - 'zone.csv'
mysql:
  host: 'localhost'
  db: 'openBMP'
  user: 'openbmp'
  passwd: 'openbmp'
  charset: 'utf8mb4'
  init: 'True'
```

## Comments
- maxmaind geplite2 is incorrect.
- when import mysql database, except incorrect words.
