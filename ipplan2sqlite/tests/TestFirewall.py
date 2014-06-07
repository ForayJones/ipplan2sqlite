import os
import sqlite3
import sys
import unittest
from BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)
import firewall
import networks
import parser
import tables


class TestFirewall(BaseTestCase, unittest.TestCase):

    def setUp(self):
        super(TestFirewall, self).setUp()
        firewall.add_services(self._load_JSON('data/services.json'), self.c)
        firewall.add_flows(self._load_JSON('data/flows.json'), self.c)
        networks.add_all(self.c)
        parser.parse(self._load('data/masterNetwork.txt'), self.c)

    def testServerClientRule(self):
        lines = self._load('data/testServerClientRules.txt')
        parser.parse(lines, self.c)
        firewall.build(self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level"""
        )[0]
        self.assertEquals(
            rule[0],
            'jumpgate1.event.dreamhack.se',
            "Wrong source host")
        self.assertEquals(
            rule[1],
            'ddns1.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(rule[2], 'normal', "Wrong flow")
        self.assertEquals(
            rule[3],
            '2022/tcp',
            "Wrong destination port/protocol")

    def testPublicRule(self):
        parser.parse(self._load('data/testPublicRule.txt'), self.c)
        firewall.build(self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 8, "Wrong number of firewall rules")

        rules = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM
               firewall_rule_ip_level WHERE from_node_name = 'DREAMHACK'"""
        )
        self.assertEquals(len(rules), 2, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level
               WHERE from_node_name = 'DREAMHACK'
               AND service_dst_ports = '123/udp,123/tcp'"""
        )
        self.assertEquals(len(rule), 1, "Wrong number of firewall rules")

    def testWorldRule(self):
        parser.parse(self._load('data/testWorldRule.txt'), self.c)
        firewall.build(self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level"""
        )[0]
        self.assertEquals(rule[0], 'ANY', "Wrong source host")
        self.assertEquals(
            rule[1],
            'www.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(rule[2], 'normal', "Wrong flow")
        self.assertEquals(
            rule[3],
            '80/tcp',
            "Wrong destination port/protocol")

    def testLocalRule(self):
        parser.parse(self._load('data/testLocalRule.txt'), self.c)
        firewall.build(self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = rules[0]
        self.assertEquals(rule[0], 1, "Wrong rule id")
        self.assertEquals(rule[2], 'TECH-SRV-6-JUMPNET', "Wrong source host")
        self.assertEquals(
            rule[3],
            '77.80.231.128/28',
            "Wrong source IPv4 address")
        self.assertEquals(
            rule[5],
            'speedtest1mgmt.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(
            rule[11],
            '69/udp',
            "Wrong destination port/protocol")


def main():
    unittest.main()

if __name__ == '__main__':
    main()
