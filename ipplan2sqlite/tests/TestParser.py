import os
import sqlite3
import sys
import unittest

path = os.path.abspath( os.path.join( os.path.dirname( __file__ ), '../lib' ) )
sys.path.insert( 1, path )
import parser
import tables

class TestParser(unittest.TestCase):

  def _query(self, q):
    return self.c.execute( q ).fetchall()

  def setUp(self):
    self.conn = sqlite3.connect(':memory:')
    self.c = self.conn.cursor()
    tables.create( self.conn )

  def tearDown(self):
    self.conn.close()
    self.c = None

  def testParseIPv4(self):
    self.assertEquals( parser.ip2long( '8.8.8.8', 4 ), 134744072 )
    self.assertEquals( parser.ip2long( '77.80.251.247/32', 4 ), 1297153015 )

  def testParserMapping(self):
    self.assertEquals( parser.parser_func( ["#$ d20--b.event.dreamhack.local\t\t\t10.0.3.45\t\t\tipv4f;ipv4r;tblswmgmt"] ), "host" )
    self.assertEquals( parser.parser_func( ["""TECH-SRV-1-INT 						D-FW-V		77.80.231.0/27		921	othernet"""]) , "network" )
    self.assertEquals( parser.parser_func( ["""#@ IPV4-NET      77.80.128.0/17"""] ), "master_network" )

  def testParseNetworkAndHost(self):
    network_line = """TECH-SRV-1-INT 						D-FW-V		77.80.231.0/27		921	othernet"""

    host_line = """#$ ddns1.event.dreamhack.se						77.80.231.201			ipv4f;ipv4r;ipv6f;ipv6r;s=dhssh64,ddns-dhssh64;c=ldaps64,log64,pgdb64,mydb64,ddns-mydb64;p=dns64,ntp64,smtp64,dhcp64"""

    vlan = parser.network( network_line.split(), self.c, None )
    
    self.assertEquals( vlan, 921, "Wrong VLAN" )
    
    parser.host( host_line.split(), self.c, vlan )

    self.assertEquals( self._query( 'SELECT COUNT(*) FROM node' )[0][0], 2, "Wrong number of nodes")

    host = self._query( 'SELECT * FROM host' )[0]
    self.assertEquals( host[0], 2, "Wrong node id" )
    self.assertEquals( host[1], 'ddns1.event.dreamhack.se', "Wrong hostname" )
    self.assertEquals( host[2], 1297147849, "Wrong IPv4 long" )
    self.assertEquals( host[3], '77.80.231.201', "Wrong IPv4 address" )
    self.assertEquals( host[4], '2001:67c:24d8:921::201', "Wrong IPv6 address" )
    self.assertEquals( host[5], 1, "Wrong network id" )
  
    options = self._query( 'SELECT * FROM option' )
    self.assertEquals( len( options ), 16, "Wrong number of options" )
    correct_options = set( [ 'ipv4f', 'ipv4r', 'ipv6f', 'ipv6f', 'p', 's', 'c', 'othernet' ] )
    parsed_options = set( [ str(o[2]) for o in options ] )
    self.assertEquals( len( correct_options.union( parsed_options ) ), 8, "Missing or additional options" )

  def testParseNetwork(self):
    network_line = """TECH-SRV-1-INT 						D-FW-V		77.80.231.0/27		921	othernet"""
    vlan = parser.network( network_line.split(), self.c, None )
    network = self._query( 'SELECT * FROM network' )[0]
    self.assertEquals( network[0], 1, "Wrong node id" )
    self.assertEquals( network[1], 'TECH-SRV-1-INT', "Wrong network name" )
    self.assertEquals( network[2], 921, "Wrong VLAN" )
    self.assertEquals( network[3], 'D-FW-V', "Wrong terminator" )
    self.assertEquals( network[4], 1297147648, "Wrong IPv4 long" )
    self.assertEquals( network[5], "77.80.231.0/27", "Wrong IPv4 address" )
    self.assertEquals( network[6], "2001:67c:24d8:921::/64", "Wrong IPv6 address" )
    self.assertEquals( network[7], 4294967264, "Wrong IPv4 netmask long" )
    self.assertEquals( network[8], "255.255.255.224", "Wrong IPv4 netmask" )
    self.assertEquals( network[9], "64", "Wrong IPv6 netmask decimal" )
    self.assertEquals( network[10], 1297147649, "Wrong IPv4 gateway long" )
    self.assertEquals( network[11], "77.80.231.1", "Wrong IPv4 gateway address ")
    self.assertEquals( network[12], "2001:67c:24d8:921::1", "Wrong IPv6 gateway address" )
    self.assertEquals( network[13], 27, "Wrong IPv4 netmask decimal" )
    self.assertEquals( network[14], 1, "Wrong IPv6 capability" )

def main():
  unittest.main()

if __name__ == '__main__':
  main()