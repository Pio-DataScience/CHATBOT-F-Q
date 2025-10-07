# Quick Network Setup Guide

## Enable Network Access in 3 Steps

### Step 1: Open Firewall Ports (Run as Administrator)

Open PowerShell as Administrator and run:

```powershell
New-NetFirewallRule -DisplayName "FAQ API Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

New-NetFirewallRule -DisplayName "FAQ GUI Port 8501" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

You only need to do this ONCE.

---

### Step 2: Start Network-Accessible Services

Run the network startup script:

```powershell
.\start_network.ps1
```

The script will:
- Auto-detect your server's IP address
- Display the access URLs
- Start both API and GUI with network access
- Show you the URL to share with your team

---

### Step 3: Share the GUI URL

The script will show something like:

```
============================================
  Network Access URLs:
  ===================
  API:      http://192.168.1.100:8000
  API Docs: http://192.168.1.100:8000/docs
  GUI:      http://192.168.1.100:8501
============================================

Share the GUI URL with your team!
They can access it from: http://192.168.1.100:8501
```

**Share this URL with your colleagues:**
```
http://192.168.1.100:8501
```
(Replace with your actual server IP)

---

## Client Access

From any computer on the same network:

1. Open a web browser (Chrome, Edge, Firefox)
2. Go to: `http://YOUR_SERVER_IP:8501`
3. Use the FAQ system normally!

---

## Troubleshooting

### Can't access from other machines?

**Test 1: Ping the server**
```cmd
ping 192.168.1.100
```
Should reply successfully.

**Test 2: Check if ports are open**
```powershell
Test-NetConnection -ComputerName 192.168.1.100 -Port 8501
```
Should show `TcpTestSucceeded : True`

**Test 3: Check firewall rules**
```powershell
Get-NetFirewallRule -DisplayName "FAQ*"
```
Should show 2 rules enabled.

---

## That's It!

You're now ready for network access. Run `.\start_network.ps1` and share the URL!
