#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, division, print_function

import re
import time
import codecs
import base64
import logging
import retrying
import requests


logger = logging.getLogger(__name__)


class Proxy(object):
    def __init__(self):
        self.url = 'http://www.cool-proxy.net/proxies/http_proxy_list/sort:score/direction:desc/page:{page}'
        self.re_ip_encode_pattern = re.compile(r'Base64.decode\(str_rot13\("([^"]+)"\)\)', re.I)
        self.re_port_pattern = re.compile(r'<td>(\d{1,5})</td>', re.I)

        self.cur_proxy = None
        self.proxies = []
        self.result = []

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, page_num):
        try:
            rp = requests.get(self.url.format(page=page_num), proxies=self.cur_proxy, timeout=10)

            re_ip_encode_result = self.re_ip_encode_pattern.findall(rp.text)
            re_port_result = self.re_port_pattern.findall(rp.text)

            if not len(re_ip_encode_result) or not len(re_port_result):
                raise Exception("empty")

            if len(re_ip_encode_result) != len(re_port_result):
                raise Exception("len(host) != len(port)")

        except Exception as e:
            logger.error("[-] Request page {page} error: {error}".format(page=page_num, error=str(e)))
            while self.proxies:
                new_proxy = self.proxies.pop(0)
                self.cur_proxy = {new_proxy['type']: "%s:%s" % (new_proxy['host'], new_proxy['port'])}
                raise e
            else:
                return []

        re_ip_result = []
        for each_result in re_ip_encode_result:
            decode_ip = base64.b64decode(codecs.decode(each_result.strip(), 'rot-13')).strip()
            re_ip_result.append(decode_ip.decode('utf-8'))

        result_dict = dict(zip(re_ip_result, re_port_result))
        return [{"host": host, "port": port, "from": "coolproxy"} for host, port in result_dict.items()]

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
