import collections
import re

# Hack to not save packages to database (which we could do if we want to)
_packages = None

def add_services(services, c):
    for service, data in services.iteritems():
        row = [service,
               data['description'],
               ','.join(data['destport']),
               ','.join(data.get('sourceport',[])) or None]
        c.execute('INSERT INTO service VALUES (NULL, ?, ?, ?, ?)', row)


def add_flows(flows, c):
    for flow in flows:
        row = [flow, flow]
        c.execute('INSERT INTO flow VALUES (NULL, ?, ?)', row)

def add_packages(packages, c):
    global _packages
    _packages = packages

def build(c):
    client_server(c)
    local(c)
    public(c)
    world(c)
    return

def fetch_nodes_and_services(access, c, match=None):
    global _packages
    access_to_sql_map = {
        'server': 's',
        'client': 'c',
        'world': 'w',
        'local': 'l',
        'public': 'p'
    }
    c.execute('SELECT node_id, value FROM option WHERE name = ?', (
        access_to_sql_map[access], ))
    explicit = c.fetchall()

    # Extract service flows from packages
    c.execute('SELECT node_id, value FROM option WHERE name = ?', ('pkg', ))
    package_options = c.fetchall()

    nodes = collections.defaultdict(set)
    for node_id, flow in explicit:
        nodes[node_id].add(flow)

    for node_id, package_name in package_options:
        package = _packages[package_name]
        nodes[node_id] |= set(package.get(access, []))

    for node_id, packages in nodes.iteritems():
        if '-default' in packages:
            packages.remove('-default')
        elif 'default' in _packages:
            for package_name in _packages['default']:
                package = _packages[package_name]
                nodes[node_id] |= set(package.get(access, []))

    for node, services in nodes.iteritems():
        for service in services:
            if match and service != match:
                continue
            yield (node, service)

def client_server(c):
    # Select all servers
    for server in fetch_nodes_and_services('server', c):
        to_node_id = int(server[0])
        service = parse_service(c, to_node_id, server[1])

        for client in fetch_nodes_and_services('client', c,
                                               match=service['full_name']):
            from_node_id = int(client[0])
            row = [from_node_id,
                   to_node_id,
                   service['service_id'],
                   service['flow_id'],
                   service['is_ipv4'],
                   service['is_ipv6']]
            c.execute(
                'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                row)
    return


def local(c):
    # Select all servers providing services to their VLAN
    for server in fetch_nodes_and_services('local', c):
        to_node_id = int(server[0])

        # What service?
        service = parse_service(c, to_node_id, server[1])

        # Which VLAN is this server on?
        c.execute(
            'SELECT network_id FROM host WHERE node_id = ?', (to_node_id,))
        from_node_id = int(c.fetchone()[0])
        row = [from_node_id,
               to_node_id,
               service['service_id'],
               service['flow_id'],
               service['is_ipv4'],
               service['is_ipv6']]
        c.execute(
            'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
            row)
    return


def public(c):
    # List public networks
    network_node_ids = {}
    for network in ['EVENT@DREAMHACK', 'RFC_10', 'RFC_172', 'RFC_192']:
        network_node_ids[network] = get_network_node_id(c, network)

    # Select all servers providing services to their VLAN
    for server in fetch_nodes_and_services('public', c):
        to_node_id = int(server[0])

        # What service?
        service = parse_service(c, to_node_id, server[1])

        for network in network_node_ids:
            from_node_id = network_node_ids[network]
            row = [from_node_id,
                   to_node_id,
                   service['service_id'],
                   service['flow_id'],
                   service['is_ipv4'],
                   service['is_ipv6']]
            c.execute(
                'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                row)
    return


def world(c):
    # Reference for internet
    from_node_id = get_network_node_id(c, "ANY")

    # Select all servers providing services to their VLAN
    for server in fetch_nodes_and_services('world', c):
        to_node_id = int(server[0])

        # What service?
        service = parse_service(c, to_node_id, server[1])
        row = [from_node_id,
               to_node_id,
               service['service_id'],
               service['flow_id'],
               service['is_ipv4'],
               service['is_ipv6']]
        c.execute(
            'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
            row)
    return


def parse_service(c, node_id, service):
    service_version = str(re.compile(r'[^\d.]+').sub('', service))

    c.execute(
        'SELECT network.name FROM network JOIN host '
        'ON network.node_id = host.network_id WHERE host.node_id = ? OR '
        'network.node_id = ?',
        (node_id, node_id))
    network = c.fetchone()[0]
    domain = network.split('@')[0]

    is_ipv4 = 0
    is_ipv6 = 0
    if not service_version:
        is_ipv4 = 1
        is_ipv6 = 1
    if "4" in service_version:
        is_ipv4 = 1
    if "6" in service_version:
        is_ipv6 = 1
    service_name = service.replace(service_version, '')

    # Flow?
    if "-" in service_name:
        flow_name = service_name.split('-')[0]
        service_name = service_name.split('-')[-1]
    else:
        flow_name = domain.lower()
    flow_id = get_flow_id(c, flow_name)

    # Service?
    service_id = get_service_id(c, service_name)

    return {"full_name": service,
            "service_id": service_id,
            "flow_id": flow_id,
            "is_ipv4": is_ipv4,
            "is_ipv6": is_ipv6}


def get_flow_id(c, flow_name):
    c.execute('SELECT id FROM flow WHERE name = ?', (flow_name, ))
    return int(c.fetchone()[0])


def get_service_id(c, service_name):
    c.execute('SELECT id FROM service WHERE name = ?', (service_name, ))
    return int(c.fetchone()[0])


def get_network_node_id(c, network_name):
    c.execute('SELECT node_id FROM network WHERE name = ?', (network_name,))
    return c.fetchone()[0]
