# FAQ Document Processing System

## Quick Start

### 1. Setup LM Studio (Required for Question Generation)
See **[LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)** for complete instructions.

**Quick summary:**
- Install LM Studio from https://lmstudio.ai/
- Download any model (e.g., Llama 3.2 3B)
- Load the model and start local server on port 1234

### 2. Run the Application

```powershell
.\start_network.ps1
```

This will:
- Auto-detect your network IP
- Start the API server
- Start the GUI
- Open your browser

### 3. Share with Team

Share this URL with your team:
```
http://192.168.30.10:8501
```

## Documentation

- **[LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)** - How to setup LM Studio for question generation
- **[NETWORK_FIX.md](NETWORK_FIX.md)** - Network configuration for this machine
- **[doc/CORRECT_NETWORK_SETUP.md](doc/CORRECT_NETWORK_SETUP.md)** - Detailed network setup guide
- **[doc/README_INTERFACE.md](doc/README_INTERFACE.md)** - Interface documentation
- **[doc/QUICK_START.md](doc/QUICK_START.md)** - Quick start guide

## Troubleshooting

### "Connection refused" on port 1234
LM Studio is not running. See [LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)

### Team cannot access the interface
Check your firewall and IP address. See [NETWORK_FIX.md](NETWORK_FIX.md)