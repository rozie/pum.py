#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import json
import logging
import time
import yaml
import requests

from jinja2 import Template

logger = logging.getLogger(__name__)

URL = "https://api.uptimerobot.com/v2/getMonitors"
types = {
    1: 'HTTP(s)',
    2: 'Keyword',
    3: 'Ping',
    4: 'Port'
}
statuses = {
        0: 'paused',
        1: 'not checked yet',
        2: 'up',
        8: 'seems down',
        9: 'down'
}


def get_monitor_data(url, apikey, ratios):
    payload = "api_key={}&format=json&custom_uptime_ratios={}&all_time_uptime_ratio=1".format(apikey, ratios)
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'cache-control': "no-cache"
        }
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        logging.debug("Response code was %s" % response.status_code)
    except Exception as e:
        logger.error("Couldn't fetch JSON %s", e)
    return json.loads(response.text)


def parse_response(response, config_name):
    custom_uptime_ratios = response.get("monitors", [{}])[0].get("custom_uptime_ratio", "").split("-")
    name = response.get("monitors", [{}])[0].get("friendly_name", "")
    check_type = response.get("monitors", [{}])[0].get("type")
    check_status = response.get("monitors", [{}])[0].get("status")
    all_time_uptime_ratio = response.get("monitors", [{}])[0].get("all_time_uptime_ratio", "0")
    alltime = round(float(all_time_uptime_ratio), 2)
    custom_ratios = [round(float(tmp), 2) for tmp in custom_uptime_ratios]
    display_name = name
    if config_name:
        display_name = config_name
    check_data = {
        'name': display_name,
        'check_type': types.get(check_type, "unknown"),
        'check_status': statuses.get(check_status, "unknown"),
        'custom_uptime_ratios': custom_ratios,
        'all_time_uptime_ratio': alltime
    }
    return check_data


def pagerender(template_file, ratios, all_checks):
    date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
    with open(template_file, "r", encoding="utf=8") as tfile:
        template = tfile.read()
    t = Template(template)
    res = t.render(ratios=ratios, all_checks=all_checks, date=date)
    return res


def display(display_type, ratios, all_checks):
    ratios_list = [ratio + 'd' for ratio in ratios.split("-")]
    if display_type == 'html':
        page = pagerender("template.html", ratios_list, all_checks)
        print(page)
    elif display_type == 'bootstrap':
        page = pagerender("template_bootstrap.html", ratios_list, all_checks)
        print(page)
    else:
        header = "Hostname\tStatus\tType\t"
        header += "\t".join(ratios_list) + "\tall time"
        print(header)
        for check in all_checks:
            r_tmp = "\t".join([str(ratio) + '%' for ratio in check.get('custom_uptime_ratios')])
            print("{}\t{}\t{}\t{}\t{}%".format(check.get('name'),
                check.get('check_status'),
                check.get('check_type'),
                r_tmp, check.get('all_time_uptime_ratio')))


def main():
    args = parse_arguments()

    # set verbosity
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # load config file
    try:
        with open(args.config, "r") as config:
            data = yaml.safe_load(config)
    except Exception as e:
        logger.error("Couldn't read config file %s", e)

    ratios = data.get("global", {}).get("ratios", "1-7-30-365")
    requests_per_minute = data.get("global", {}).get("requests_per_minute", 10)
    requests_count = 0
    all_checks = []

    for key in data.get("keys"):
        resp = get_monitor_data(URL, key, ratios)
        config_name = data.get("keys", {}).get(key, {}).get("name")
        check_data = parse_response(resp, config_name)
        all_checks.append(check_data)
        requests_count += 1
        if requests_count % requests_per_minute == 0:
            requests_count = 0
            logging.debug("Sleeping to avoid rate limit")
            time.sleep(60)
    display(args.display, ratios, all_checks)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='PUM - Python Uptime Monitor')

    parser.add_argument(
        '-v', '--verbose', required=False,
        default=False, action='store_true',
        help="Run in verbose mode")
    parser.add_argument(
        '-d', '--display', required=False,
        default='text', choices=['html', 'bootstrap', 'text'],
        help="Display type to use")
    parser.add_argument(
        '-c', '--config', required=False,
        default="config.yaml",
        help="Configuration file"
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
