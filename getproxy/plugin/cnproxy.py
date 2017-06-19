#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, division, print_function

import re
import time
import logging
import retrying
import requests


"""
http://www.cnproxy.com/proxy1.html
"""


logger = logging.getLogger(__name__)


class Proxy(object):
    def __init__(self):
        self.url = 'http://www.cnproxy.com/proxy{page}.html'  # 从1-10
        self.re_ip_pattern = re.compile(r'<tr><td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})<SCRIPT', re.I)
        self.re_port_encode_pattern = re.compile(r'javascript>document.write\(":"([+\w]{2,10})\)</SCRIPT>')

        self.port_dict = {
            'v': '3',
            'm': '4',
            'a': '2',
            'l': '9',
            'q': '0',
            'b': '5',
            'i': '7',
            'w': '6',
            'r': '8',
            'c': '1',
            '+': ''
        }

        self.cur_proxy = None
        self.proxies = []
        self.result = []

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, page_num):
        try:
            rp = requests.get(self.url.format(page=page_num), proxies=self.cur_proxy, timeout=10)

            re_ip_result = self.re_ip_pattern.findall(rp.text)
            re_port_encode_result = self.re_port_encode_pattern.findall(rp.text)

            if not len(re_ip_result) or not len(re_port_encode_result):
                raise Exception("empty")

            if len(re_ip_result) != len(re_port_encode_result):
                raise Exception("len(host) != len(port)")

        except Exception as e:
            logger.error("[-] Request page {page} error: {error}".format(page=page_num, error=str(e)))
            while self.proxies:
                new_proxy = self.proxies.pop(0)
                self.cur_proxy = {new_proxy['type']: "%s:%s" % (new_proxy['host'], new_proxy['port'])}
                raise e
            else:
                return []

        re_port_result = []
        for each_result in re_port_encode_result:
            each_result = each_result.strip()
            re_port_result.append(int(''.join(list(map(lambda x: self.port_dict.get(x, ''), each_result)))))

        result_dict = dict(zip(re_ip_result, re_port_result))
        return [{"host": host, "port": port, "from": "cnproxy"} for host, port in result_dict.items()]

    def start(self):
        for page in range(1, 10):
            page_result = self.extract_proxy(page)
            time.sleep(3)

            if not page_result:
                return

            self.result.extend(page_result)


if __name__ == '__main__':
    p = Proxy()
    p.start()

    for i in p.result:
        print(i)

    print(len(p.result))
