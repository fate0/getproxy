#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, division, print_function

import os
import sys
import json
import time
import copy
import signal
import logging

import requests
import gevent.pool
import gevent.monkey
import geoip2.database

from .utils import signal_name, load_object


gevent.monkey.patch_all()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GetProxy(object):
    base_dir = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, input_proxies_file=None, output_proxies_file=None):
        self.pool = gevent.pool.Pool(500)
        self.plugins = []
        self.web_proxies = []
        self.valid_proxies = []
        self.input_proxies = []
        self.input_proxies_file = input_proxies_file
        self.output_proxies_file = output_proxies_file
        self.proxies_hash = {}
        self.origin_ip = None
        self.geoip_reader = None

    def _collect_result(self):
        for plugin in self.plugins:
            if not plugin.result:
                continue

            self.web_proxies.extend(plugin.result)

    def _validate_proxy(self, proxy, scheme='http'):
        country = proxy.get('country')
        host = proxy.get('host')
        port = proxy.get('port')

        proxy_hash = '%s://%s:%s' % (scheme, host, port)
        if proxy_hash in self.proxies_hash:
            return

        self.proxies_hash[proxy_hash] = True
        request_proxies = {
            scheme: "%s:%s" % (host, port)
        }

        request_begin = time.time()
        try:
            response_json = requests.get(
                "%s://httpbin.org/get?show_env=1&cur=%s" % (scheme, request_begin),
                proxies=request_proxies,
                timeout=5
            ).json()
        except:
            return

        request_end = time.time()

        if str(request_begin) != response_json.get('args', {}).get('cur', ''):
            return

        anonymity = self._check_proxy_anonymity(response_json)
        country = country or self.geoip_reader.country(host).country.iso_code

        return {
            "type": scheme,
            "host": host,
            "port": port,
            "anonymity": anonymity,
            "country": country,
            "response_time": round(request_end - request_begin, 2),
            "from": proxy.get('from')
        }

    def _validate_proxy_list(self, proxies, timeout=300):
        valid_proxies = []

        def save_result(p):
            if p:
                valid_proxies.append(p)

        for proxy in proxies:
            self.pool.apply_async(self._validate_proxy, args=(proxy, 'http'), callback=save_result)
            self.pool.apply_async(self._validate_proxy, args=(proxy, 'https'), callback=save_result)

        self.pool.join(timeout=timeout)
        self.pool.kill()

        return valid_proxies

    def _check_proxy_anonymity(self, response):
        via = response.get('headers', {}).get('Via', '')

        if self.origin_ip in json.dumps(response):
            return 'transparent'
        elif via and via != "1.1 vegur":
            return 'anonymous'
        else:
            return 'high_anonymous'

    def _request_force_stop(self, signum, _):
        logger.warning("[-] Cold shut down")
        self.save_proxies()

        raise SystemExit()

    def _request_stop(self, signum, _):
        logger.debug("Got signal %s" % signal_name(signum))

        signal.signal(signal.SIGINT, self._request_force_stop)
        signal.signal(signal.SIGTERM, self._request_force_stop)

        logger.warning("[-] Press Ctrl+C again for a cold shutdown.")

    def init(self):
        logger.info("[*] Init")
        signal.signal(signal.SIGINT, self._request_stop)
        signal.signal(signal.SIGTERM, self._request_stop)

        rp = requests.get('http://httpbin.org/get')
        self.origin_ip = rp.json().get('origin', '')
        logger.info("[*] Current Ip Address: %s" % self.origin_ip)

        self.geoip_reader = geoip2.database.Reader(os.path.join(self.base_dir, 'data/GeoLite2-Country.mmdb'))

    def load_input_proxies(self):
        logger.info("[*] Load input proxies")

        if self.input_proxies_file and os.path.exists(self.input_proxies_file):
            with open(self.input_proxies_file) as fd:
                for line in fd:
                    try:
                        self.input_proxies.append(json.loads(line))
                    except:
                        continue

    def validate_input_proxies(self):
        logger.info("[*] Validate input proxies")
        self.valid_proxies = self._validate_proxy_list(self.input_proxies)

    def load_plugins(self):
        logger.info("[*] Load plugins")
        for plugin_name in os.listdir(os.path.join(self.base_dir, 'plugin')):
            if os.path.splitext(plugin_name)[1] != '.py' or plugin_name == '__init__.py':
                continue

            try:
                cls = load_object("getproxy.plugin.%s.Proxy" % os.path.splitext(plugin_name)[0])
            except Exception as e:
                logger.info("[-] Load Plugin %s error: %s" % (plugin_name, str(e)))
                continue

            inst = cls()
            inst.proxies = copy.deepcopy(self.valid_proxies)
            self.plugins.append(inst)

    def grab_web_proxies(self):
        logger.info("[*] Grab proxies")

        for plugin in self.plugins:
            self.pool.spawn(plugin.start)

        self.pool.join(timeout=8 * 60)
        self.pool.kill()

        self._collect_result()

    def validate_web_proxies(self):
        logger.info("[*] Validate web proxies")
        valid_proxies = self._validate_proxy_list(self.web_proxies)
        self.valid_proxies.extend(valid_proxies)

    def save_proxies(self):
        logger.info("[*] Check %s proxies, Got %s valid proxies" % (len(self.proxies_hash), len(self.valid_proxies)))
        if self.output_proxies_file:
            outfile = open(self.output_proxies_file, 'w')
        else:
            outfile = sys.stdout

        for item in self.valid_proxies:
            outfile.write("%s\n" % json.dumps(item))

        outfile.flush()

    def start(self):
        self.init()
        self.load_input_proxies()
        self.validate_input_proxies()
        self.load_plugins()
        self.grab_web_proxies()
        self.validate_web_proxies()
        self.save_proxies()


if __name__ == '__main__':
    g = GetProxy()
    g.start()
