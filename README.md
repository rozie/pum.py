pum.py
========
This is tool for reading data from Uptime Robot (external free uptime montior service; account required) written in Python.

Features
--------
* runs from cron - separates backend from output
* keys to API objects are hidden
* allows to hide (overwrite) hostnames/IPs/URLs
* configurable rate limiter
* simple static HTML as output - no JS support in browser required [live version](https://zakr.es/pum.html)

Usage
-------
Usual Python way. Install requirements. Take a look on sample_config.yaml. Configure as you need. 
Run the script, enjoy the output. Use -h for help.

_global_ section parameters
-------
* ratios - days, separated with minus sign - for what periods get uptime ratio
* requests_per_minute - how much API requests perform before sleeping for 60 seconds

_keys_ section parameters
-------
* apikey - API key (from Uptime Robot)
* name - optional display name. Allows to overwrite friendlyName from Uptime Robot, which is used by default.

Typical usage
-------
Add script to cron, redirect output to location readable by HTTP server.

*/30 * * * * ~/pum.py/venv/bin/python ~/pum.py/pum.py -d bootstrap > /tmp/pum.html && /bin/mv /tmp/pum.html /var/www/pum.html

License
-------
See LICENSE file.
