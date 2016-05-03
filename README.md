[![Build Status](https://travis-ci.org/nlindblad/ipplan2sqlite.svg)](https://travis-ci.org/nlindblad/ipplan2sqlite)
[![Coverage Status](https://coveralls.io/repos/nlindblad/ipplan2sqlite/badge.svg?branch=nl-add-coveralls)](https://coveralls.io/r/nlindblad/ipplan2sqlite?branch=nl-add-coveralls)

ipplan2sqlite
=============

Because plain text is awesome, but sometimes cumbersome.

Forked from Dreamhack crew, modifications made by ForayJones.

The host FQDN will be generated from the ipplan.  

Requirements:
    sqlite3 database at /etc/ipplan.db
    manifest.yml file - defines your flows, services, and packages. See ./tests/data/manifest.yml for example 
    seatmap.json file - defines tables/switches for dhmap 
    ipplan text file  - defines your networks and hosts. 

!!! Use --debug for very helpful information if something isn't working right !!!    
    
## Example ipplan text file

The file needs to use tabs for alignment, size 8 is recommended. UTF8 and UNIX line feed are required.


    #Domain                          #Net
    @@ IPV4-EVENT.LANPARTY-NET       10.0.0.0/16  
    @@ IPV6-EVENT.LANPARTY-NET       fd00:::/48
    
    #Network           #Terminator   #Net              #VLAN(number, '-' = none)     #Options
    ADMINZONE          GW1           10.0.0.0/24       -                             sw=0;
    
    #Host                            #IPv4                                           #Options
    $$GW1                            10.0.0.1                                        pkg=dns   
    $$adminzone-sw0                  10.0.0.10                                       pkg=switch;layer=access
    
    #Switches must be lower case 'network' -sw 'opt sw=?' 
    #Multiple switches can be set active for each network.     
   
    # For tables the letter is the hall and the number is the table. 
    
    #Table             #Terminator   #Net              #VLAN(number, '-' = none)     #Options
    A01                GW1           10.0.1.0/24       -                             sw=0;
    
    #Host                            #IPv4                                           #Options
    $$a01-sw0                        10.0.1.0                                        pkg=switch;layer=access 


