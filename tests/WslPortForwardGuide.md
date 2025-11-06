WSL2 Docker Port Forwarding Recovery Guide

Step-by-Step Instructions

1️⃣ Check container in WSL

Open WSL and verify your container is running:

docker ps

Check the port inside WSL:

ss -tlnp | grep <port>

# or

sudo netstat -tlnp | grep <port>

Example:

ss -tlnp | grep 9999

You should see  0.0.0.0:9999  and  docker-proxy  listening.

2️⃣ Get WSL2 IP address

wsl hostname -I

The first IP is the one Windows must connect to, e.g.,  172.25.124.29 .

3️⃣ Open PowerShell as Administrator

You need elevated privileges to set up the portproxy.

4️⃣ Remove old portproxy rules

netsh interface portproxy delete v4tov4 listenport=9999 listenaddress=127.0.

0.1

netsh interface portproxy delete v4tov4 listenport=9999 listenaddress=0.0.0.0

1

Optional: verify rules:

netsh interface portproxy show all

5️⃣ Add new portproxy

Use  ${}  for variables with colons in strings:

$port = 9999

$wsl_ip = (wsl hostname -I).Split(" ")[0]

netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0

connectport=$port connectaddress=$wsl_ip

netsh interface portproxy add v4tov4 listenport=$port listenaddress=127.0.0.1

connectport=$port connectaddress=$wsl_ip

Write-Host "Proxy set: localhost:${port} -> ${wsl_ip}:${port}"

6️⃣ Allow firewall access

netsh advfirewall firewall add rule name="WSL portproxy inbound $port" dir=in

action=allow protocol=TCP localport=$port

7️⃣ Restart IP Helper service

Restart-Service iphlpsvc

8️⃣ Test connection from Windows

curl http://localhost:9999

If it doesn’t work, try connecting directly to the WSL IP:

curl http://${wsl_ip}:9999

2

9️⃣ Optional: Automate with PowerShell script

Create  wsl-port-forward.ps1 :

$port = 9999

$wsl_ip = (wsl hostname -I).Split(" ")[0]

netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.

0

netsh interface portproxy delete v4tov4 listenport=$port listenaddress=127.0.

0.1

netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0

connectport=$port connectaddress=$wsl_ip

netsh interface portproxy add v4tov4 listenport=$port listenaddress=127.0.0.1

connectport=$port connectaddress=$wsl_ip

netsh advfirewall firewall add rule name="WSL portproxy inbound $port" dir=in

action=allow protocol=TCP localport=$port

Restart-Service iphlpsvc

Write-Host "Proxy set: localhost:${port} -> ${wsl_ip}:${port}"

Run as Admin whenever WSL2 IP changes:

.\wsl-port-forward.ps1

🔟 Quick Reference

1.

2.

Verify container is running in WSL ( docker ps  /  ss -tlnp ).
Get WSL2 IP:  wsl hostname -I .

3.

Open PowerShell as Admin.

4.

5.

Delete old portproxy rules.
Add new rules with  ${}  variables.

6.

7.

8.

Allow firewall for port.
Restart  iphlpsvc .
Test with  curl localhost:<port> .

9.

Optional: save as script for next time.

Tip: The key things that usually break are: - WSL2 gets a new IP after reboot. - Portproxy rules reference
old IP. - Firewall blocks inbound connections. -  iphlpsvc  needs restart for rules to take effect.

3

