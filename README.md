# Turnout Controller

A Ryu controller application that redirects traffic following user's decisions. 
Specifically, we can redirect a traffic to various computers connected to the switch managed by the controller: each of these computers performs an analysis on that traffic, without modifying it, and then, it spits out that traffic on the switch again through a different Ethernet port (these computers have 2 Ethernet ports, one receives the traffic to analyze, the other spits out that same traffic on the switch).
For each traffic, we can create a route, that maps each traffic to various computers, as selected by the users.
In particular, we offer the possibility to set a route for a traffic in real time, visualize existing routes and modify them.


## How it works

Based on Ryu component-based framework, we created three modules (in **modules** folder) to be loaded through run.sh.
### my_fileserver.py 
It creates a server that answer user's request to certain URLs: like this, we realize a Web GUI, through which a user can send request to the controller application and set a route for a new traffic.
**live.html** is a page that once in a while send an Ajax request to the controller application, to see if, meanwhile, the controller detected new traffic. If it's the case, a popup will appear to inform the user, that can exploit that popup to send a request to the controller application to set a route for that traffic. In particular, a user will choose which analyzing functions have to be activated on the traffic.
**index.html** is a page that once loaded asks the controller application for existing routes, and displays all these returned routes in a table. Each row contains a button, that a user can click to modify that route through a popup, that will appear as soon as a user clicks a button.
### turnout.py
It realizes the core logic of the app: it memorizes interesting traffics (those coming from a particular port of the managed switch), existing routes, and configure, through OpenFlow, the switch, to set user's desired behaviour.
For each traffic memorized, a popup will appear in live.html (if a user is on the page) and a user will be able to set a route.
### turnout_rest.py
It maps, through WSGI, each request from the Web GUI to turnout.py.

## Tests

In the folder **tests**, there are two shell scripts that will let you emulate two different network, to test how this controller application works. Try communicating between those two computers using different protocols and see how this controller application behaves.

## License and more

Turnout Controller is published under **GNU General Public License v3.0**. Special thanks to Srini Seetharaman from http://sdnhub.org for his Ryu related works.

Copyright (©) [**MrOverfl00w**](https://github.com/MrOverflOOw) & [**iFedix**](https://github.com/iFedix) 2017
