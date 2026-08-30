import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import psutil
from asyncua.sync import Client as SyncClient

from plc_monitor.config.settings import (
    DEFAULT_OPCUA_PORT,
    OPCUA_PROBE_TIMEOUT,
    SCAN_MAX_WORKERS,
    SCAN_TIMEOUT,
)


@dataclass
class DiscoveredDevice:
    ip: str
    port: int
    endpoint_url: str
    name: str
    application_uri: str = ""


def list_local_subnets():
    subnets = []
    for addrs in psutil.net_if_addrs().values():
        for addr in addrs:
            if addr.family != socket.AF_INET:
                continue
            if addr.address.startswith("127."):
                continue
            if not addr.netmask:
                continue
            try:
                network = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
            except ValueError:
                continue
            if network.prefixlen < 16:
                continue
            cidr = str(network)
            if cidr not in subnets:
                subnets.append(cidr)
    return subnets


def _port_open(ip, port, timeout):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_opcua(ip, port, port_timeout, opcua_timeout):
    if not _port_open(ip, port, port_timeout):
        return None
    endpoint_url = f"opc.tcp://{ip}:{port}"
    try:
        client = SyncClient(endpoint_url, timeout=opcua_timeout)
        endpoints = client.connect_and_get_server_endpoints()
    except Exception:
        return None
    name = ip
    application_uri = ""
    if endpoints:
        app_desc = endpoints[0].Server
        if app_desc.ApplicationName and app_desc.ApplicationName.Text:
            name = app_desc.ApplicationName.Text
        application_uri = app_desc.ApplicationUri or ""
    return DiscoveredDevice(ip=ip, port=port, endpoint_url=endpoint_url, name=name, application_uri=application_uri)


def scan_for_opcua(
    subnet,
    port=DEFAULT_OPCUA_PORT,
    port_timeout=SCAN_TIMEOUT,
    opcua_timeout=OPCUA_PROBE_TIMEOUT,
    max_workers=SCAN_MAX_WORKERS,
):
    network = ipaddress.IPv4Network(subnet, strict=False)
    hosts = list(network.hosts())
    found = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for result in pool.map(lambda ip: _probe_opcua(str(ip), port, port_timeout, opcua_timeout), hosts):
            if result:
                found.append(result)
    return found
