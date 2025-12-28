═══════════════════════════════════════════════════════════════
    N4LR DX CLIENT - Real-time DX Spot Monitor with DXCC Tracking
═══════════════════════════════════════════════════════════════

INSTALLATION
────────────────────────────────────────────────────────────────
1. Extract all files from this ZIP to a folder on your computer
   Example: C:\N4LR-DXClient\

2. Double-click N4LR-DXClient.exe to run

3. On first run:
   - Go to the Settings tab
   - Enter your callsign (e.g., W1AW)
   - Enter your grid square (e.g., FN31pr or EM50)
   - Click "Save Settings"

4. The app will automatically:
   - Connect to the VE7CC DX cluster
   - Download LoTW user activity data (~225,000 callsigns, takes 10 seconds)
   - Start displaying live DX spots


FEATURES
────────────────────────────────────────────────────────────────
✓ Real-time DX spots from VE7CC cluster (FT8, FT4, CW, SSB, etc.)
✓ LoTW user indicators (green + = active user)
✓ DXCC Challenge tracking with visual alerts
✓ Band filtering (160m through 6m)
✓ Solar propagation data (SFI, A-index, K-index)
✓ Sunrise/sunset times for your location
✓ Grid square and DXCC filtering
✓ Challenge progress table showing all 340 entities × 9 bands


UNDERSTANDING THE DISPLAY
────────────────────────────────────────────────────────────────
Live Spots Tab:
  • Green + before callsign = Active LoTW user (uploaded within 90 days)
  • Orange + before callsign = Inactive LoTW user (>90 days since upload)
  • No + = Not a LoTW user (paper QSL required)
  • Amber/yellow highlighted rows = DXCC entities you need for Challenge

Challenge Tab:
  • Shows your complete DXCC progress across all HF bands
  • Green checkmarks = Confirmed on that band
  • Empty cells = Needed for that band
  • Summary stats at top


SETTING UP YOUR DXCC CHALLENGE DATA
────────────────────────────────────────────────────────────────
To see YOUR Challenge progress and get alerts for needed entities:

1. Go to https://lotw.arrl.org
2. Log in to your LoTW account
3. Go to "Your Account" → "DXCC Account"
4. Click "Download ADIF" (get the full DXCC credits file)
5. Save the .adi file to your computer

6. You need a Python script to process it:
   Contact N4LR (gordy@n4lr.com) for the conversion script
   OR if you're comfortable with Python, use this command:
   
   python process_lotw.py your_file.adi
   
   This creates challenge_data.json which the app needs.

7. Copy challenge_data.json to the same folder as N4LR-DXClient.exe

8. Restart the app - you'll now see amber highlights for needed spots!


FILTERS & CONTROLS
────────────────────────────────────────────────────────────────
Band Selection (right panel):
  • Check/uncheck bands to show or hide
  • Use "All" or "None" buttons for quick selection

Top Filters:
  • Grid - Filter by grid square prefix (e.g., "FN" for New England)
  • DXCC substring - Filter by country prefix (e.g., "JA" for Japan)
  • Reject K,VE - Quick filter to hide USA/Canada spots
  • Reset Filters - Clear all filters

Cluster Command:
  • Enter DX cluster commands (e.g., "sh/dx", "sh/wwv")
  • Click Send or press Enter

Settings Tab:
  • Change your callsign or grid square
  • Select different DX cluster server
  • Connect/Disconnect from cluster
  • Toggle auto-connect on startup


TIPS FOR BEST RESULTS
────────────────────────────────────────────────────────────────
• Use band filters to focus on bands you're working
• Watch for green + callsigns - LoTW confirmations are automatic!
• Amber highlighted spots are your TOP PRIORITY for Challenge
• Click Challenge tab to see which bands need the most work
• Solar data helps predict propagation:
    SFI > 150 = Great conditions
    K-index < 3 = Stable conditions
    A-index < 20 = Quiet geomagnetic field


TROUBLESHOOTING
────────────────────────────────────────────────────────────────
Q: App won't start
A: Make sure all files from the ZIP are in the same folder

Q: "No LoTW cache file found" message repeats
A: Normal on first run. The app will download it automatically.
   Takes about 10 seconds. Wait for "Downloaded 225282 LoTW users"

Q: No spots appearing
A: Check Settings tab - make sure you're "Connected"
   If not, click Disconnect then Connect

Q: Challenge tab shows no data
A: You need to load your LoTW ADIF file (see instructions above)
   Or contact N4LR for help setting this up

Q: Spots appear but no amber highlights
A: You haven't loaded your Challenge data yet
   Follow "SETTING UP YOUR DXCC CHALLENGE DATA" section above

Q: Connection says "Connecting..." forever
A: Check your internet connection
   Try clicking Disconnect then Connect in Settings tab


SYSTEM REQUIREMENTS
────────────────────────────────────────────────────────────────
• Windows 10 or 11 (64-bit)
• Internet connection
• 200 MB free disk space
• 1280×720 minimum screen resolution recommended


DATA FILES
────────────────────────────────────────────────────────────────
The app uses these files (included):
  • cty.dat - Country prefix database (29,000+ entries)
  • dxcc_mapping.json - DXCC entity mappings
  • challenge_data.json - YOUR Challenge data (you must create this)

The app creates these files:
  • config.ini - Your settings (callsign, grid, server, etc.)
  • lotw_users.json - LoTW user database (refreshes weekly)


UPDATES
────────────────────────────────────────────────────────────────
Check with N4LR for updates to:
  • cty.dat (updated when new DXCC entities are added)
  • App executable (bug fixes and new features)

To update your Challenge data:
  • Download fresh ADIF from LoTW
  • Process it with the conversion script
  • Replace challenge_data.json
  • Restart the app


SUPPORT & FEEDBACK
────────────────────────────────────────────────────────────────
Created by: N4LR (Gordy)
Email: gordy@n4lr.com

Found a bug? Want a feature?
Contact N4LR with your feedback!


73 and Good DX!
═══════════════════════════════════════════════════════════════
Version 1.0 - December 2025
