# Refoss smart plugs in Home Assistant, locally

*Control your Refoss plugs from Home Assistant and read their power, **without resetting them, without moving them to Meross, and without losing the Refoss app**.*

Most Refoss plugs (MSS210, MSS301, MSS310…) are Meross hardware under another brand. The excellent [Meross LAN](https://github.com/krahabb/meross_lan) integration drives them **directly over your Wi-Fi**, with no cloud, but only if it knows your **account key**. Meross LAN can fetch that key from a *Meross* account. It can't fetch it from a *Refoss* one.

This guide gets the key **once**, from the Refoss app on your own phone, in about 15 minutes. After that everything runs locally, and the Refoss app keeps working as before.

> Tested in September 2026: Home Assistant 2026.9, Meross LAN 5.8, Refoss app on **iPhone**, plugs MSS210 and MSS301 (EU cloud). The Android steps are the standard mitmproxy ones but haven't been tested with the Refoss app yet. Please open an issue with your result.

---

## The problem

Refoss sells two families of plugs, and Home Assistant only handles one of them out of the box:

| Family | Examples | Firmware | Home Assistant |
|---|---|---|---|
| **Refoss's own** | R10, EM06, EM16 | Refoss | ✅ built-in **Refoss** integration, found automatically on the LAN, no key |
| **Meross-based** | MSS210, MSS301, MSS310 | Meross (rebranded) | ❌ the Refoss integration doesn't see them. ⚠️ **Meross LAN** can drive them, but only with the account key, and it can only log into **Meross** accounts, not **Refoss** ones |

So a Meross-based Refoss plug is stuck: HA discovers it, Meross LAN asks for a key, and there is no way to get that key from HA. The usual advice is "reset the plug and pair it with the Meross app". That works, but you lose the Refoss app and have to redo every plug. This guide gets the key instead, and keeps everything as it is.

## Tested plugs

| Model | Hardware | Firmware | Region | Result in HA (Meross LAN 5.8.0) |
|---|---|---|---|---|
| **MSS301** | 12.0.0 | 12.1.8 | EU | ✅ on/off + power (W), voltage, current, energy (Wh, Energy dashboard ready) |
| **MSS210** | 8.0.0 | 8.3.3 | EU | ✅ on/off (this model has no power metering) |
| R10 | 1.0.0 | 1.1.13 | EU | not needed: works keyless with the built-in *Refoss* integration (or [refoss_lan](https://github.com/Refoss/refoss-homeassistant) from HACS) |

Tested September 2026 with Home Assistant 2026.9.3, Meross LAN 5.8.0, mitmproxy 12.2.3, Refoss app on an **iPhone**, account on the EU cloud.

Likely to work, not tested: MSS310 and other Meross-based Refoss models, US/Asia accounts. Please open an issue with model, firmware and result, and we'll add it to the table.

## Requirements and compatibility check

**Your plug is a candidate if:**
- In the Refoss app, device → ⚙ → *Device info*, the model starts with **MSS** (or another Meross code such as MSL, MTS). R10/EM models don't need this guide.
- In Home Assistant, with Meross LAN installed, the plug shows up under **Discovered** as a *Meross LAN* device, or Meross LAN finds it by IP and then asks for a key or says *key error*. That is exactly the situation this guide fixes.

**You need:**
- Home Assistant with [HACS](https://hacs.xyz/) and **Meross LAN** (tested 5.8.0).
- Home Assistant and the plugs on the **same network**. HA talks to each plug over HTTP, port 80. Guest Wi-Fi, client isolation or separate VLANs without a rule block it.
- A computer on the same Wi-Fi as the phone, able to run **mitmproxy** (tested 12.2.3; Mac, Windows or Linux).
- The phone with the **Refoss app** already managing the plugs, and your account login.
- A plug that is **online**: offline plugs can be added later with the same key.

**You don't need:** a Meross account, the Meross app, resets, cloud access for Home Assistant, or root/jailbreak on the phone.

## How it works (30 seconds)

1. A small program on your computer (**mitmproxy**) sits between your phone and the internet for a few minutes.
2. You log into the Refoss app. The app's own login answer contains your account key.
3. The script in this repo keeps **only that key**. It never reads the request, so your password is never seen or stored.
4. You undo everything on the phone and the computer, then paste the key into Meross LAN.

The key belongs to **your account**: one key for all your plugs. You are reading your own data from your own app. Don't use this on accounts or devices that aren't yours.

---

## Two ways to do it

- **By hand:** follow steps 1–5 below.
- **With an AI assistant** doing the computer part for you: see the next section, then do only the phone steps yourself.

## Doing it with an AI assistant

A coding assistant that can run commands on your computer (Claude Code, Codex CLI, Cursor, etc.) can do the computer side for you: install mitmproxy, find your IP, open and close the firewall port, start the capture, and add the plugs to Home Assistant. You only tap on the phone.

Paste this prompt:

```text
Help me add my Refoss smart plugs to Home Assistant locally, following
https://github.com/tlabcustomaudio/refoss-home-assistant-local (read its README first).

Rules:
- Never ask for, type or store my Refoss password. I log in on the phone myself.
- Never print the account key in full: show it only masked (first 3 + last 3 characters).
  Read it from refoss-key.txt when you need it; don't write it anywhere else.
- Before changing my firewall or installing anything, tell me what you're about to do.
- As soon as the key is captured: stop mitmproxy, close the firewall port, delete ~/.mitmproxy,
  and walk me through undoing the proxy and removing the certificate on my phone.

Steps:
1. Check that mitmproxy is installed (install it if not) and download refoss_key.py from the repo.
2. Tell me this computer's IP address, open port 8080 to my local network only,
   and start: mitmdump -q --listen-port 8080 -s refoss_key.py
3. Give me the phone steps for my phone model (I'll tell you: iPhone or Android), one at a time,
   and wait while I do them.
4. When the key is captured, do the cleanup above.
5. Then help me add each plug in Home Assistant with Meross LAN (through the UI, or through
   the Home Assistant API if I give you a token), matching plugs by MAC address.
```

Tips:
- Use an assistant that runs **on your computer**. Don't paste the key into a web chat.
- An assistant with terminal access can read `refoss-key.txt`: that's why the prompt forbids printing it. Watch what it does, and stop it if it tries to send the key anywhere.
- If you give it a Home Assistant token for step 5, create a dedicated one (profile → Security → Long-lived access tokens) and delete it when you're done.

---

## Step 1 — Install Meross LAN in Home Assistant

1. HACS → search **Meross LAN** → Download → restart Home Assistant.
2. Settings → Devices & services. After a few minutes your plugs usually appear under **Discovered** as Meross LAN devices. Leave them there for now.

## Step 2 — Start mitmproxy on your computer

Install mitmproxy (once):

| System | Command |
|---|---|
| macOS | `brew install mitmproxy` (or `pipx install mitmproxy`) |
| Windows | installer from [mitmproxy.org](https://mitmproxy.org/) |
| Linux | `pipx install mitmproxy` (or `uv tool install mitmproxy`) |

Download this repo, open a terminal in its folder and run:

```bash
mitmdump -q --listen-port 8080 -s refoss_key.py
```

`-q` hides the phone's normal traffic, so the terminal only shows what matters: the device list and the key.

Find your computer's IP address (you'll type it on the phone):

| System | Where |
|---|---|
| macOS | System Settings → Wi-Fi → Details → IP address |
| Windows | `ipconfig` → IPv4 Address |
| Linux | `ip -4 addr` or `hostname -I` |

> **Firewall:** the phone must reach port **8080** on the computer.
> - macOS and Windows ask "allow incoming connections?": say **yes**.
> - Linux with ufw: `sudo ufw allow from 192.168.1.0/24 to any port 8080 proto tcp`. Use your own network, and remove the rule at the end.

---

## Step 3 — The phone

Pick your phone. Keep the terminal from step 2 visible.

### 📱 iPhone (tested)

1. **Proxy.** Settings → Wi-Fi → tap **ⓘ** next to your network → **Configure Proxy** → **Manual**
   - Server: your computer's IP
   - Port: `8080`
   - Authentication: off → **Save**
2. **Download the certificate.** Open **Safari** (it must be Safari) and go to **http://mitm.it**. Tap **Get mitmproxy-ca-cert.pem** under *iOS* → **Allow**.
   *If the page says "traffic is not passing through mitmproxy", recheck the proxy and the computer's firewall.*
3. **Install it.** Settings → a new line **Profile Downloaded** appears at the top → **Install** → enter your passcode → **Install** again.
4. **Trust it** (easy to forget). Settings → General → About → scroll to the bottom → **Certificate Trust Settings** → turn **mitmproxy** on → **Continue**.
5. **Refoss app.** Open it → Me / Profile → **Log out** → log **in** again.

### 🤖 Android (not tested yet)

The menu names change a little between brands (Samsung, Pixel, Xiaomi…). If you can't find a menu, search the Settings app for **"certificate"** or **"proxy"**.

1. **Proxy.** Settings → Network & internet → Internet / Wi-Fi → tap your network (or long-press → *Modify*) → **pencil / Advanced options** → **Proxy: Manual**
   - Proxy hostname: your computer's IP
   - Proxy port: `8080` → **Save**
2. **Download the certificate.** Open **Chrome** and go to **http://mitm.it**. Tap **Get mitmproxy-ca-cert.cer** under *Android*. It lands in *Downloads*.
3. **Install it as a CA certificate.** Settings → Security & privacy → More security settings → **Encryption & credentials** → **Install a certificate** → **CA certificate** → **Install anyway** → pick the downloaded file.
   *Samsung:* Settings → Security and privacy → Other security settings → **Install from device storage** → CA certificate.
4. **Refoss app.** Open it → Me / Profile → **Log out** → log **in** again.

> Android only lets apps trust a certificate you install yourself if the app allows it, and many apps don't. If the terminal stays silent after login, use an iPhone: that is the tested path.

### Capturing the data: what happens and what you see

As soon as you log in, the app asks the Refoss cloud *"who is this user?"*. The answer (`/v1/Auth/signIn`) contains, among other things, your **account key**:

```json
{"apiStatus": 0, "data": {"userid": "…", "email": "…", "key": "3f9••••••••••••••••••••••••••a1c", "token": "…", "domain": "https://iotx-eu.refoss.net"}}
```

Right after, the app downloads your device list (`/v1/Device/devList`). The script reads those two answers and nothing else:

```
Your devices (match the MAC suffix in your router to find each IP):
  Bambu Lab H2D                mss301   MAC aa:bb:cc:11:22:33  online
  Aquarium                     mss210   MAC aa:bb:cc:44:55:66  online

*** Refoss key captured: 3f9…a1c (32 chars), saved to /…/refoss-key.txt ***
*** Cloud region: https://iotx-eu.refoss.net. You can stop mitmproxy now (Ctrl+C) and undo the phone settings. ***
```

- **Nothing appears?** You're probably still logged in: the app only signs in when you log out and back in. Also check the certificate is trusted (step 3).
- **Only the device list appears, no key?** Log out and in once more. The key only travels in the sign-in answer.
- Stop mitmproxy with **Ctrl+C**.

**Reading the key** (you paste it in step 5):

| System | Command |
|---|---|
| macOS / Linux | `cat refoss-key.txt` |
| Windows | `type refoss-key.txt` |

It is 32 letters and digits, one line.

<details>
<summary><b>Prefer to see it with your own eyes? Manual capture with mitmweb, no script</b></summary>

1. Instead of `mitmdump`, start `mitmweb --listen-port 8080`. A page opens in the browser (http://127.0.0.1:8081) showing every request as it happens.
2. Do step 3 on the phone (proxy, certificate, log out/in).
3. In the **Search/filter** box type `signIn`.
4. Click the `POST …/v1/Auth/signIn` line → **Response** tab → find `"key": "…"`. That's it.
5. Close mitmweb.

Unlike the script, mitmweb **keeps the whole session in memory while it's open**, including what the phone sent (your password). Close it as soon as you have the key, and don't save the flows.
</details>

---

## Step 4 — Restore the phone and the computer (now, don't postpone)

While the proxy and the certificate are active, your computer can read the phone's encrypted traffic. Put everything back as soon as you have the key. It takes two minutes.

### 📱 iPhone
1. **Proxy off:** Settings → Wi-Fi → **ⓘ** next to your network → Configure Proxy → **Off** → Save.
2. **Remove the certificate:** Settings → General → **VPN & Device Management** → *mitmproxy* → **Remove Profile** → passcode → Remove.
3. **Check:** Settings → General → About → Certificate Trust Settings. *mitmproxy* must no longer be listed.

### 🤖 Android
1. **Proxy off:** Wi-Fi → your network → pencil / Advanced options → Proxy → **None** → Save.
2. **Remove the certificate:** Settings → Security & privacy → More security settings → Encryption & credentials → **User credentials** → *mitmproxy* → **Remove**.
   *Samsung:* Security and privacy → Other security settings → **View security certificates** → *User* → mitmproxy → Remove.
   *Or remove every user certificate at once:* Encryption & credentials → **Clear credentials**. Only if you installed no others you need, e.g. for work.
3. **Check:** Trusted credentials → *User* tab: empty, or no mitmproxy.

### 💻 The computer
1. **Stop mitmproxy:** Ctrl+C in its terminal.
2. **Close the port you opened:**

   | System | How |
   |---|---|
   | macOS | System Settings → Network → **Firewall** → Options → select *mitmdump* (or *Python*) → **−**. If you never saw a firewall prompt, there is nothing to close |
   | Windows | Start → *Allow an app through Windows Firewall* → Change settings → uncheck or **Remove** *mitmdump* / *Python*. PowerShell as admin: `Get-NetFirewallApplicationFilter \| ? Program -like "*mitm*" \| Get-NetFirewallRule \| Remove-NetFirewallRule` |
   | Linux (ufw) | `sudo ufw delete allow from 192.168.1.0/24 to any port 8080 proto tcp` (the exact rule you added; `sudo ufw status numbered` lists them) |

3. **Delete mitmproxy's certificate authority**, so nobody can ever reuse it. It lives in a folder in your home:

   | System | Command |
   |---|---|
   | macOS / Linux | `rm -rf ~/.mitmproxy` |
   | Windows | `rmdir /s /q %USERPROFILE%\.mitmproxy` |

4. **The key file:** keep `refoss-key.txt` somewhere private (a password manager is ideal): you need it again for every new plug (see below). Or delete it: you can always capture it again.
5. *(Optional)* uninstall mitmproxy: `brew uninstall mitmproxy` / `pipx uninstall mitmproxy` / Windows "Add or remove programs".

From here on nothing passes through your computer any more, and the phone is exactly as before.

---

## Step 5 — Add the plugs to Home Assistant

Open `refoss-key.txt` and copy the key.

**If the plugs are under *Discovered*** (most common):
1. Settings → Devices & services → a Meross LAN card → **Configure**.
2. **Host** is already filled in. Paste the **key** → **Submit** → **Submit** again on the last page.
3. Repeat for each plug: the key is the same for all of them.

**If a plug isn't discovered:** Add integration → **Meross LAN** → *Add a device manually* → its IP address + the key.

Which card is which plug? The discovered name is often a wrong router label ("iphone", "camera"…). Match the **MAC suffix** printed in step 3 with the card, or with your router's device list.

Then, optionally:
- **Rename** each device as in the Refoss app: device page → pencil.
- **Energy dashboard:** Settings → Dashboards → Energy → *Individual devices* → add the plug's **Consumption** sensor.

---

## Adding a new plug later

**No new capture needed.** When you pair a plug, the Refoss app writes your **account key** into it. So every plug on the same account uses the same key, the one you already have.

1. **Refoss app:** add the plug as usual (**+** → pick the model → follow the pairing steps). Check that it works in the app.
2. **Router** *(recommended)*: give it a fixed IP (DHCP reservation), so it never moves.
3. **Home Assistant:** within a few minutes it appears under Settings → Devices & services → **Discovered** as a Meross LAN device → **Configure** → paste the **same key** → Submit → Submit.
   Not showing up? Add integration → **Meross LAN** → add the device manually with its IP + the key.
4. Rename it. If it measures power, add its **Consumption** sensor to the Energy dashboard.

If Meross LAN says **key error** on a new plug, the key has changed (see the next section): capture it again.

---

## What happens if…

| You… | What happens | What to do |
|---|---|---|
| **change your Refoss password** | the plugs keep working in HA with the key they have. The account key *may* change: plugs paired **after** the change would then carry the new one | if a new plug gives *key error*, repeat the capture (steps 2–4, 10 minutes). Update old plugs only if they show *key error*: Meross LAN device → **Configure** → new key |
| **log out / log in** to the Refoss app | nothing: same key | nothing |
| **update a plug's firmware** from the Refoss app | normally nothing: local control is part of the firmware | if a plug stops responding in HA after an update, reload it (device page → ⋮ → Reload) and open an issue here with the model and firmware version |
| **factory-reset a plug** or **remove it from the Refoss app** | the plug forgets Wi-Fi and key: offline in HA and in the app | pair it again in the Refoss app. HA picks it up again, sometimes with a new *Discovered* card: configure it with the same key |
| **change router or Wi-Fi password** | plugs go offline everywhere (app and HA) | re-pair them in the Refoss app on the new Wi-Fi. The key doesn't change, so HA reconnects by itself, or via the new Discovered card |
| **move a plug to someone else's Refoss account** | it gets **their** key | HA needs that account's key: they capture it the same way |
| **delete your Refoss account** | the key goes with it. Plugs keep their old key until reset | keep using them as they are, or re-pair them to a new account and capture its key |
| the **Refoss cloud is down** or the internet is out | HA keeps working: everything is local. Only the app stops working when you're away from home | nothing |
| **uninstall the Refoss app** | HA keeps working | nothing. You need the app again only to pair new plugs |
| someone gets your **key** | on your home network they could switch your plugs | keep it private. To invalidate it, change the Refoss password *and* re-pair the plugs, then capture the new key |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| mitm.it says traffic is not passing through mitmproxy | wrong IP or port on the phone, or the computer's firewall blocks 8080 |
| Other apps show "connection not private" while the proxy is on | expected: finish quickly and do step 4 |
| Terminal shows nothing after login | the certificate isn't trusted. iPhone: Certificate Trust Settings (step 3.4). Android: the app may ignore user certificates, try an iPhone |
| Meross LAN says **key error** | wrong or incomplete key: copy it again from `refoss-key.txt`, 32 characters, no spaces. Or the key changed: see *What happens if…* |
| A plug is **offline** in the list | add it later with the same key, once it's back online |
| The plug changes IP later | give it a fixed IP (DHCP reservation) in your router. Meross LAN also follows it by MAC |
| The Refoss app still works? | yes. Nothing on the plug or the account is changed |

## Security notes

- The script only reacts to answers from Refoss/Meross hosts. It keeps the `key` field, in a file only your user can read, and it never looks at what the phone sends.
- While the proxy and certificate are active, your computer could read the phone's HTTPS traffic. That's why step 4 comes straight after, including deleting `~/.mitmproxy`.
- The key allows local control of your plugs. Keep `refoss-key.txt` private, and don't paste it in issues or screenshots.

## Files

| File | What |
|---|---|
| `refoss_key.py` | the mitmproxy script: keeps only the key, lists your devices |
| `test_refoss_key.py` | offline check with fake data: `python test_refoss_key.py` |

MIT licence. Not affiliated with Refoss, Meross or Home Assistant.
