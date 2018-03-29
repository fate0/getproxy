#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, division, print_function

import re
import time
import logging
import retrying
import requests


logger = logging.getLogger(__name__)


class Proxy(object):
    def __init__(self):
        self.urls = ['http://www.xicidaili.com/nn/', 'http://www.xicidaili.com/wt/']
        self.re_ip_pattern = re.compile(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>', re.I)
        self.re_port_pattern = re.compile(r'<td>(\d{1,5})</td>', re.I)

        self.cur_proxy = None
        self.proxies = []
        self.result = []

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, url):
        try:
            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) "
                              "Chrome/21.0.1180.89 Safari/537.1'"
            }
            rp = requests.get(url, proxies=self.cur_proxy, headers=headers, timeout=10)

            re_ip_result = self.re_ip_pattern.findall(rp.text)
            re_port_result = self.re_port_pattern.findall(rp.text)

            if not len(re_ip_result) or not len(re_port_result):
                raise Exception("empty")

            if len(re_port_result) != len(re_port_result):
                raise Exception("len(host) != len(port)")

        except Exception as e:
            logger.error("[-] Request url {url} error: {error}".format(url=url, error=str(e)))
            while self.proxies:
                new_proxy = self.proxies.pop(0)
                self.cur_proxy = {new_proxy['type']: "%s:%s" % (new_proxy['host'], new_proxy['port'])}
                raise e
            else:
                return []

        result_dict = dict(zip(re_ip_result, re_port_result))
        return [{"host": host, "port": port, "from": "xicidaili"} for host, port in result_dict.items()]

    def start(self):
        for url in self.urls:
            page_result = self.extract_proxy(url)
            time.sleep(3)

            if not page_result:
                return

            self.result.extend(page_result)


if __name__ == '__main__':
    p = Proxy()
    p.start()

    for i in p.result:
        print(i)
