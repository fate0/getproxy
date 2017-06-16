# -*- coding: utf-8 -*-

import click
from getproxy import GetProxy


@click.command()
@click.option('--in-proxy', help='Input proxy file')
@click.option('--out-proxy', help='Output proxy file')
def main(in_proxy, out_proxy):
    g = GetProxy(in_proxy, out_proxy)
    g.start()


if __name__ == "__main__":
    main()
