# BLE-SCALE

- [BLE-SCALE](#ble-scale)
	- [Einführung](#einführung)
	- [Installation des Raspberry Pi Zero 2 W mit BLE-SCALE](#installation-des-raspberry-pi-zero-2-w-mit-ble-scale)
		- [Konfiguration des WLANs](#konfiguration-des-wlans)
		- [SSH konfigurieren](#ssh-konfigurieren)
		- [UFW-Firewall installieren \& konfigurieren](#ufw-firewall-installieren--konfigurieren)
		- [Bluetooth aktivieren](#bluetooth-aktivieren)
		- [BLE-Scale installieren](#ble-scale-installieren)
			- [Abhängigkeiten installieren](#abhängigkeiten-installieren)
			- [Installation BLE-Scale](#installation-ble-scale)
			- [Starten der Schntitstelle](#starten-der-schntitstelle)
			- [Service-Installation](#service-installation)
			- [Dienst aktivieren](#dienst-aktivieren)
	- [Optionales](#optionales)
		- [Täglicher Reboot konfigurieren](#täglicher-reboot-konfigurieren)
		- [Overlay aktivieren](#overlay-aktivieren)

## Einführung

Das BLE-SCALE-Modul ermöglicht die Verwendung einer Bluetooth-Waage für das [POT-Plugin](https://plugin.pot.ch/). Dazu kann beispielsweise ein [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) verwendet werden.

## Installation des Raspberry Pi Zero 2 W mit BLE-SCALE

- Erstelle mit [Raspberry Pi Imager](https://www.raspberrypi.com/software/) eine bootbare MicroSD-Karte. Verwende das Lite-Image ohne GUI. [Hier](https://www.raspberrypi.com/documentation/computers/getting-started.html) findest du eine Anleitung.
- Boote den Raspberry Pi.

### Konfiguration des WLANs

Mittels

```
sudo raspi-config
```

WLAN Country auf CH einstellen

Mit folgenden Anweisungen kannst du den Raspberry Pi mit einem Netzwerk verbinden.

```
nmcli dev wifi list
sudo nmcli --ask dev wifi connect <example_ssid>
```

### SSH konfigurieren

- Erstelle ein Zertifikat und hinterlege den Public Key im ~/.ssh/authorized_keys.
- Ändere die Einstellungen von /etc/sshd/sshd_config:

  - Port 2299
  - PermitRootLogin no
  - MaxAuthTries 5
  - MaxSessions 3
  - PubkeyAuthentication yes
  - PasswordAuthentication no
  - PermitEmptyPasswords no
  - AllowTcpForwarding no
  - GatewayPorts no
  - X11Forwarding no

### UFW-Firewall installieren & konfigurieren

```
sudo apt install ufw
sudo ufw enable
sudo ufw allow 2299
sudo ufw status
```

### Bluetooth aktivieren

```
rfkill unblock bluetooth
```

### BLE-Scale installieren

#### Abhängigkeiten installieren

```
sudo apt install python3-bleak
```

#### Installation BLE-Scale

```
cd 
mkdir ble-scale
cd ble-scale
wget https://raw.githubusercontent.com/lars-schultz/ble-scale/refs/heads/master/main.py
```

#### Starten der Schntitstelle

```
python main.py https://your.pot.instance.ch/receiver.php waage1
```

#### Service-Installation

Datei /lib/systemd/system/blescale.service mit folgendem Inhalt befüllen:

```
[Unit]
Description=BLE Scale Service
After=multi-user.target
Requires=bluetooth.service

[Service]
Type=simple
ExecStart=/usr/bin/python /home/scale/ble-scale/main.py https://your.pot.instance.ch/receiver.php waage1
StandardOutput=file:/tmp/blescale.log
StandardError=file:/tmp/blescale_error.log
Restart=always
#ProtectSystem=true
#ProtectHome=true
#PrivateTmp=true
#RestrictAddressFamilies=AF_NETLINK AF_UNIX AF_QIPCRTR
#NoNewPrivileges=true
User=scale

[Install]
WantedBy=multi-user.target
```

#### Dienst aktivieren

```
sudo systemctl daemon-reload
sudo systemctl enable blescale.service
sudo systemctl start blescale.service
```

## Optionales

### Täglicher Reboot konfigurieren

Crontab bearbeiten:
```
crontab -e
```

Folgende Zeile anfügen:
```
59 23   * * *   root    reboot
```

### Overlay aktivieren

Damit keine Schreiboperationen auf der MicroSD-Karte durchgeführt werden, kann das Overlay aktiviert werden

```
sudo raspi-config
```
- Aktivieren des Overlays