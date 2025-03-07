# MQTT iptables blocker

### Background
Part of my home automation requires the ability to enable / disable Internet access for a subset of hosts easily.  My network firewall is a standard multi-homed Debian 12 box using an iptables firewall.  So, I wrote a simple program to monitor my MQTT messagebus and BLOCK / UNBLOCK a named iptables chain based on MQTT messages.

*Count yourself lucky that I didn't call it __MQTT BLOCKCHAIN__* 😂

### How It Works
The script listens on a topic `firewall/CHAIN/block` for a message of either **0** (to unblock) or **1** (to block).

It reports on a topic of `firewall/CHAIN/blocked` with either a message of **True** (for blocked) or **False** (for unblocked).

It reports with "Retain" set to True, so you can always tell the last status it provided upon subscribing, with the caveat that this might be wrong if the script isn't running and the state has changed out-of-band.

### Installation
#### Requirements
  - python 3
  - paho-mqtt library (available as `python3-paho-mqtt` in Debian repos)

Since this involves the questionable practice of running a script, as root, on your firewall, with outside influance via MQTT, I'm going to let you do it manually rather than providing a footgun installation script.  But to do so:

  - copy `mqtt-block-table.py` into `/usr/local/sbin` and make it executable
  - edit `mqtt-block-table.py` and update the `MQTT_SERVER` and `TOPIC` variables to your desired settings.  (TOPIC specifies the root level mqtt topic, it can be whatever you want).
  - copy `mqtt-block-table@.service` into `/etc/systemd/system`
  - run `systemctl daemon-reload` as root to update systemd

### iptables setup:
**The script expects the chain to be otherwise empty, and in fact the `unblock` function will flush it** 

**The script expects the chain to exist in both iptables and ip6tables**

Ergo, the intended implmentation is to create an empty chain for the purpose of blocking/unblocking whatever access you want to control, and adding it in line with your existing iptables rules.

#### Steps:
 - create an empty chain for the host / net you want to control: `iptables -N MyChain`
 - add a rule to isolate said host / net with that chain: `iptables -I FORWARD -J MyChain -m mac --mac-source 00:00:01:de:ad:1f` to isolate the host with the shown mac address, but you could easily do this for a `-S $network` or even an entire `-i $interface`
 - Repeat with ip6tables, or at least create the empty chain in ip6tables.
 - Run the script specifying the associated chain.

### Enabling / execution
  - Launch the script for your specified chains with `systemd start mqtt-block-table@CHAIN` where CHAIN is the name of the empty chain you created
  - Enable persistent execution with `systemd enable mqtt-block-table@CHAIN`
 
Now you can "turn on or off" blocking for that rule with the appropriate MQTT messages!  Use `journalctl -u mqtt-block-table@CHAIN` to troubleshoot, as per usual systemd operation.. and check the tables with the requisite `iptables -L` / `ip6tables -L` commands.

#### Example use using the **mosquitto-clients** package
Let's say you set the topic to `firewall` and ran it on a iptables chain named `KIDS`, and your MQTT host is named `mqtt`:
In one terminal, you can subscribe to the topic with the mosquitto_sub command.  It will immediately show the last "retained" message from the script, indicating the current state:
```
$ mosquitto_sub -h mqtt -v -t firewall/\#
firewall/KIDS/blocked False
```

In another terminal you can toggle the block rule by sending a message with the mosquitto_pub command:  
```
$ mosquitto_pub -h mqtt -t firewall/KIDS/block -m 1
$
```

The first terminal will now show the update (and your message, since you subscribed to the root of the topic):
```
$ mosquitto_sub -h mqtt -v -t firewall/\#
firewall/KIDS/blocked False
firewall/KIDS/block 1
firewall/KIDS/blocked True
```

## DISCLAIMER
As designed this script runs AS ROOT, on your firewall, and listens for MQTT messages from outside and takes actions on them.  It is your responsibility to ensure that this is appropriate for your network, use case, and security needs.  It is also your responsibility to ensure that this script and its associated dependencies are appropriate for your security posture.  No claims, warranties, or assertions of suitability are made by me, the author.  I'm merely providing this as an example and for convenience in case you find it useful.  As with all free & open source software, Your use is at your own risk.
