# Guacamole Native Install — VMConnect Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Apache Guacamole natively on Ubuntu VM (172.31.251.99) with latest FreeRDP to establish working VMConnect connections to Hyper-V VMs on port 2179.

**Architecture:** Native guacd (compiled from source with FreeRDP 3.x) + Guacamole web app (Tomcat) + guacamole-auth-json for token-based auth. No Docker. Direct network access to Hyper-V host (172.31.251.102) on port 2179.

**Tech Stack:** Apache Guacamole 1.5.5, FreeRDP 3.x (compiled from source), Tomcat 9, Java 11+, guacamole-auth-json, Ubuntu 24.04 LTS

**Key Lesson from Docker/WSL2 Failure:** FreeRDP 2.x in the guacd:1.5.5 Docker image cannot connect to VMConnect (port 2179) — `freerdp_post_connect failed`, "Connection reset by peer". Standard RDP on port 3389 works fine. The hypothesis is FreeRDP 3.x fixes this. This plan tests xfreerdp CLI FIRST before installing Guacamole, to validate the hypothesis early.

---

## Reference Information

### Target VM
- **IP:** 172.31.251.99
- **Hostname:** Guaca
- **OS:** Ubuntu 24.04.4 LTS
- **Credentials:** claude / NiebieskiSmok1970!
- **SSH:** Key auth configured (from DEV machine)

### Hyper-V Lab
- **Hyper-V Host:** 172.31.251.102 (HypervLab)
- **VMConnect Port:** 2179
- **NLA:** Enabled (UserAuthentication=1)
- **Test VMs:**
  - CONTOSO-WEB01: `a81bd6fe-e4a6-482e-9aae-6920c753940e`
  - FABRIKAM-APP01: `6513ce81-2c67-47ce-ba3f-574345c997bb`
- **Domain credentials:** ergonet\Administrator (use lab password)

### Guacamole Auth Config
- **JSON Secret Key:** `e28c4dbc51efa9a0df6729b7393c0079` (128-bit hex)
- **Token format:** `base64(AES-CBC-encrypt(HMAC_SHA256 + JSON_plaintext))` — HMAC inside encryption, null IV, no IV prefix
- **Auth flow:** `/?data=TOKEN` query string → server-side auth → auto-connect (single connection)

---

## Chunk 1: System Preparation & FreeRDP Validation

### Task 0: Configure passwordless sudo

**Agent:** modular-builder
**Model:** haiku

**Files:**
- Modify: `/etc/sudoers.d/claude` (create via sudo)

- [ ] **Step 1: Add passwordless sudo for claude user**

```bash
ssh claude@172.31.251.99 "echo 'NiebieskiSmok1970!' | sudo -S bash -c 'echo \"claude ALL=(ALL) NOPASSWD: ALL\" > /etc/sudoers.d/claude && chmod 440 /etc/sudoers.d/claude'"
```

- [ ] **Step 2: Verify passwordless sudo works**

```bash
ssh claude@172.31.251.99 "sudo whoami"
```

Expected: `root` (no password prompt)

---

### Task 1: Install system dependencies

**Agent:** modular-builder

**Purpose:** Install all build dependencies for FreeRDP 3.x and guacd compilation, plus Java/Tomcat for the Guacamole web app.

- [ ] **Step 1: Update system and install build tools**

```bash
ssh claude@172.31.251.99 "sudo apt-get update && sudo apt-get install -y \
  build-essential cmake git pkg-config \
  libssl-dev libpng-dev libjpeg-turbo8-dev libcairo2-dev \
  libpango1.0-dev libssh2-1-dev libvncserver-dev libpulse-dev \
  libvorbis-dev libwebp-dev libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
  libtool-bin autoconf automake uuid-dev freerdp2-dev \
  default-jdk tomcat9 \
  libwebsockets-dev libguac-client-rdp0 2>/dev/null; echo DONE"
```

Note: Some packages may not exist on 24.04 — that's OK, we're compiling FreeRDP from source anyway.

- [ ] **Step 2: Verify Java and Tomcat installed**

```bash
ssh claude@172.31.251.99 "java -version 2>&1 | head -1; systemctl status tomcat9 --no-pager | head -5"
```

---

### Task 2: Compile and install FreeRDP 3.x from source

**Agent:** modular-builder

**Purpose:** Build FreeRDP 3.x which has better VMConnect/Hyper-V compatibility than 2.x. This is the critical component that was missing in the Docker setup.

- [ ] **Step 1: Clone FreeRDP and build**

```bash
ssh claude@172.31.251.99 "cd /tmp && \
  git clone --depth 1 --branch stable-3.0 https://github.com/FreeRDP/FreeRDP.git freerdp-source && \
  cd freerdp-source && \
  cmake -B build -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DWITH_SERVER=OFF -DWITH_SAMPLE=OFF -DWITH_MANPAGES=OFF \
    -DWITH_PULSE=ON -DWITH_CUPS=OFF -DWITH_PCSC=OFF \
    -DWITH_FFMPEG=ON -DWITH_DSP_FFMPEG=ON \
    -DCHANNEL_URBDRC=OFF && \
  cmake --build build -j$(nproc) && \
  sudo cmake --install build && \
  sudo ldconfig && \
  echo 'FreeRDP build complete'"
```

- [ ] **Step 2: Verify FreeRDP 3.x installed**

```bash
ssh claude@172.31.251.99 "/usr/local/bin/xfreerdp3 --version 2>/dev/null || /usr/local/bin/xfreerdp --version 2>/dev/null"
```

Expected: FreeRDP version 3.x.x

---

### Task 3: Test VMConnect via xfreerdp CLI (CRITICAL VALIDATION)

**Agent:** bug-hunter

**Purpose:** Before installing Guacamole, validate that FreeRDP 3.x can actually connect to VMConnect on port 2179. This is the hypothesis we need to test. If this fails, we know the problem is NOT Docker/WSL2-specific and we need a different approach.

- [ ] **Step 1: Test standard RDP first (baseline — should work)**

```bash
ssh claude@172.31.251.99 "/usr/local/bin/xfreerdp3 /v:172.31.251.102 /port:3389 \
  /u:ergonet\\\\Administrator /p:'<LAB_PASSWORD>' \
  /sec:nla /cert:ignore /auth-only +auth-only 2>&1 | tail -20"
```

Expected: Authentication succeeds (exit code 0 or auth-only success message)

- [ ] **Step 2: Test VMConnect on port 2179 with preconnection-blob**

```bash
ssh claude@172.31.251.99 "/usr/local/bin/xfreerdp3 /v:172.31.251.102 /port:2179 \
  /u:ergonet\\\\Administrator /p:'<LAB_PASSWORD>' \
  /sec:nla /cert:ignore \
  /pcb:a81bd6fe-e4a6-482e-9aae-6920c753940e \
  /auth-only +auth-only 2>&1 | tail -30"
```

Expected: Connection succeeds to CONTOSO-WEB01 via VMConnect.

- [ ] **Step 3: Test with different security modes if NLA fails**

If Step 2 fails with NLA, try:
```bash
# Try TLS
/sec:tls /cert:ignore

# Try RDP security
/sec:rdp /cert:ignore

# Try any
/sec:any /cert:ignore
```

- [ ] **Step 4: Document results**

Record which security mode works with VMConnect. This determines the Guacamole connection parameters.

**STOP POINT:** If ALL security modes fail on port 2179, escalate to user. Do NOT proceed with Guacamole installation — the problem is not FreeRDP version-related.

---

## Chunk 2: Guacamole Server (guacd) — Native Build

### Task 4: Compile and install guacd from source

**Agent:** modular-builder

**Purpose:** Build guacd linked against the FreeRDP 3.x we just installed. This ensures guacd uses the newer FreeRDP that (hopefully) works with VMConnect.

- [ ] **Step 1: Download and extract Guacamole server source**

```bash
ssh claude@172.31.251.99 "cd /tmp && \
  wget -q https://apache.org/dyn/closer.lua/guacamole/1.5.5/source/guacamole-server-1.5.5.tar.gz?action=download -O guacamole-server-1.5.5.tar.gz && \
  tar xzf guacamole-server-1.5.5.tar.gz && \
  echo 'Source downloaded'"
```

- [ ] **Step 2: Build guacd with FreeRDP 3.x**

```bash
ssh claude@172.31.251.99 "cd /tmp/guacamole-server-1.5.5 && \
  export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib/x86_64-linux-gnu/pkgconfig:\$PKG_CONFIG_PATH && \
  export LDFLAGS='-L/usr/local/lib -L/usr/local/lib/x86_64-linux-gnu' && \
  export CFLAGS='-I/usr/local/include -I/usr/local/include/freerdp3 -I/usr/local/include/winpr3' && \
  autoreconf -fi && \
  ./configure --with-init-dir=/etc/init.d \
    LDFLAGS=\"\$LDFLAGS\" CFLAGS=\"\$CFLAGS\" PKG_CONFIG_PATH=\"\$PKG_CONFIG_PATH\" && \
  make -j\$(nproc) && \
  sudo make install && \
  sudo ldconfig && \
  echo 'guacd build complete'"
```

**Note:** If guacamole-server 1.5.5 doesn't compile against FreeRDP 3.x (API incompatibility), try the latest guacamole-server from git main branch which may have FreeRDP 3.x support.

- [ ] **Step 3: Verify guacd binary and RDP support**

```bash
ssh claude@172.31.251.99 "guacd -v 2>&1; ldd /usr/local/sbin/guacd 2>/dev/null | grep -i freerdp"
```

Expected: guacd version shown, linked against FreeRDP 3.x libraries

- [ ] **Step 4: Create guacd systemd service**

```bash
ssh claude@172.31.251.99 "sudo tee /etc/systemd/system/guacd.service > /dev/null << 'UNIT'
[Unit]
Description=Guacamole proxy daemon (guacd)
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/sbin/guacd -b 0.0.0.0 -l 4822 -p /var/run/guacd.pid
PIDFile=/var/run/guacd.pid
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload && \
sudo systemctl enable guacd && \
sudo systemctl start guacd && \
sudo systemctl status guacd --no-pager"
```

Expected: guacd running, listening on port 4822

- [ ] **Step 5: Commit progress notes**

No code to commit — this is infrastructure. Record results in memory file.

---

## Chunk 3: Guacamole Web App + JSON Auth

### Task 5: Deploy Guacamole web application

**Agent:** modular-builder

**Purpose:** Install the Guacamole web app (WAR file) into Tomcat, configure guacamole.properties.

- [ ] **Step 1: Download and deploy Guacamole WAR**

```bash
ssh claude@172.31.251.99 "cd /tmp && \
  wget -q https://apache.org/dyn/closer.lua/guacamole/1.5.5/binary/guacamole-1.5.5.war?action=download -O guacamole-1.5.5.war && \
  sudo cp guacamole-1.5.5.war /var/lib/tomcat9/webapps/guacamole.war && \
  echo 'WAR deployed'"
```

- [ ] **Step 2: Create GUACAMOLE_HOME directory and config**

```bash
ssh claude@172.31.251.99 "sudo mkdir -p /etc/guacamole/extensions /etc/guacamole/lib && \
sudo tee /etc/guacamole/guacamole.properties > /dev/null << 'CONF'
guacd-hostname: localhost
guacd-port: 4822
enable-websocket: false
json-secret-key: e28c4dbc51efa9a0df6729b7393c0079
CONF
sudo ln -sf /etc/guacamole /usr/share/tomcat9/.guacamole 2>/dev/null
echo 'Config created'"
```

**Note:** `enable-websocket: false` — keep disabled initially to avoid connection issues. Can enable later once everything works.

- [ ] **Step 3: Download and install guacamole-auth-json**

```bash
ssh claude@172.31.251.99 "cd /tmp && \
  wget -q https://apache.org/dyn/closer.lua/guacamole/1.5.5/binary/guacamole-auth-json-1.5.5.tar.gz?action=download -O guacamole-auth-json-1.5.5.tar.gz && \
  tar xzf guacamole-auth-json-1.5.5.tar.gz && \
  sudo cp guacamole-auth-json-1.5.5/guacamole-auth-json-1.5.5.jar /etc/guacamole/extensions/ && \
  echo 'JSON auth extension installed'"
```

- [ ] **Step 4: Restart Tomcat and verify Guacamole web app**

```bash
ssh claude@172.31.251.99 "sudo systemctl restart tomcat9 && sleep 5 && \
  curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/guacamole/ && echo ''"
```

Expected: HTTP 200

- [ ] **Step 5: Verify JSON auth API endpoint**

```bash
ssh claude@172.31.251.99 "curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8080/guacamole/api/tokens -d 'data=test' && echo ''"
```

Expected: HTTP 403 (invalid token — but endpoint exists and auth-json is loaded)

---

### Task 6: Test VMConnect through Guacamole

**Agent:** integration-specialist

**Purpose:** Generate a valid JSON auth token and test VMConnect connection through the full Guacamole stack.

- [ ] **Step 1: Generate auth token from DEV machine**

Use PowerShell on DEV (172.31.251.100) to generate a token using the same logic as FuseCP's GuacamoleService.cs:

```powershell
# On DEV machine — generate a Guacamole JSON auth token for VMConnect
$jsonSecretKey = "e28c4dbc51efa9a0df6729b7393c0079"
$keyBytes = [System.Convert]::FromHexString($jsonSecretKey)

$json = @{
    username = "ergonet\Administrator"
    expires = [long]([DateTimeOffset]::UtcNow.AddMinutes(10).ToUnixTimeMilliseconds())
    connections = @{
        "vmconnect-test" = @{
            protocol = "rdp"
            parameters = @{
                hostname = "172.31.251.102"
                port = "2179"
                username = "ergonet\Administrator"
                password = "<LAB_PASSWORD>"
                security = "nla"  # Change based on Task 3 results
                "ignore-cert" = "true"
                "preconnection-blob" = "a81bd6fe-e4a6-482e-9aae-6920c753940e"
                "disable-audio" = "true"
                "enable-wallpaper" = "false"
            }
        }
    }
} | ConvertTo-Json -Depth 5

$jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($json)

# HMAC-SHA256
$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = $keyBytes
$signature = $hmac.ComputeHash($jsonBytes)

# Concatenate: signature + JSON (HMAC INSIDE)
$payload = New-Object byte[] ($signature.Length + $jsonBytes.Length)
[Array]::Copy($signature, 0, $payload, 0, $signature.Length)
[Array]::Copy($jsonBytes, 0, $payload, $signature.Length, $jsonBytes.Length)

# AES-128-CBC encrypt with null IV
$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Key = $keyBytes
$aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$aes.IV = New-Object byte[] 16  # null IV
$encryptor = $aes.CreateEncryptor()
$ciphertext = $encryptor.TransformFinalBlock($payload, 0, $payload.Length)

# Base64 encode — NO IV prefix
$token = [Convert]::ToBase64String($ciphertext)
Write-Host "Token: $token"
```

- [ ] **Step 2: Test token against Guacamole on Ubuntu VM**

```bash
# URL-encode the token and POST to Guacamole
TOKEN="<base64-token-from-step-1>"
curl -v "http://172.31.251.99:8080/guacamole/?data=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$TOKEN'))")"
```

Or open in browser: `http://172.31.251.99:8080/guacamole/?data=<URL-encoded-token>`

- [ ] **Step 3: Verify VMConnect connection in Guacamole logs**

```bash
ssh claude@172.31.251.99 "sudo journalctl -u guacd --since '5 minutes ago' --no-pager | tail -30"
ssh claude@172.31.251.99 "sudo journalctl -u tomcat9 --since '5 minutes ago' --no-pager | tail -30"
```

Look for: successful RDP connection to 172.31.251.102:2179 with preconnection-blob

- [ ] **Step 4: Test with browser automation (optional)**

Use Chrome automation to navigate to `http://172.31.251.99:8080/guacamole/?data=<token>` and verify the VM console appears.

---

## Chunk 4: Production Hardening

### Task 7: Configure reverse proxy and firewall

**Agent:** modular-builder
**Model:** haiku

**Purpose:** Set up nginx reverse proxy for clean URLs and basic firewall rules.

- [ ] **Step 1: Install and configure nginx**

```bash
ssh claude@172.31.251.99 "sudo apt-get install -y nginx && \
sudo tee /etc/nginx/sites-available/guacamole > /dev/null << 'NGINX'
server {
    listen 80;
    server_name 172.31.251.99;

    location /guacamole/ {
        proxy_pass http://127.0.0.1:8080/guacamole/;
        proxy_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$http_connection;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    location / {
        return 301 /guacamole/;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/guacamole /etc/nginx/sites-enabled/ && \
sudo rm -f /etc/nginx/sites-enabled/default && \
sudo nginx -t && sudo systemctl restart nginx && \
echo 'Nginx configured'"
```

- [ ] **Step 2: Configure UFW firewall**

```bash
ssh claude@172.31.251.99 "sudo ufw allow 22/tcp && \
sudo ufw allow 80/tcp && \
sudo ufw --force enable && \
sudo ufw status"
```

- [ ] **Step 3: Verify access via nginx**

```bash
curl -s -o /dev/null -w '%{http_code}' http://172.31.251.99/guacamole/
```

Expected: HTTP 200

---

### Task 8: Update FuseCP GuacamoleService.cs configuration

**Agent:** modular-builder

**Purpose:** Point FuseCP at the new Guacamole instance and fix the known bugs in GuacamoleService.cs.

**Files:**
- Modify: `C:\claude\fusecp-enterprise\src\FuseCP.EnterpriseServer\Services\GuacamoleService.cs`
- Modify: `C:\FuseCP\EnterpriseServer\appsettings.json`

- [ ] **Step 1: Update appsettings.json to point to new Guacamole**

Change `GuacamoleBaseUrl` from Docker/WSL2 URL to `http://172.31.251.99/guacamole`

- [ ] **Step 2: Fix URL format bug (line 53)**

Change from hash fragment format `#/client/{id}?data=TOKEN` to query string format `/?data=TOKEN`

- [ ] **Step 3: Fix connection ID format (line 49)**

Change from `$"0\0c\0{vmId}"` to `$"{vmId}\0c\0json"` for JSON auth connections.

- [ ] **Step 4: Deploy and test via FuseCP portal**

Build, deploy to IIS, test VMConnect button in FuseCP.

**DEFER:** This task depends on VMConnect working in Task 6. Only proceed after Task 6 succeeds.

---

## Chunk 5: Cleanup & Verification

### Task 9: Clean up WSL Docker setup

**Agent:** post-task-cleanup
**Model:** haiku

**Purpose:** Remove the deprecated Docker/WSL2 Guacamole setup.

- [ ] **Step 1: Verify WSL containers are stopped (already done)**

```powershell
wsl -d Ubuntu -- docker ps -a --filter "name=guac" --format "{{.Names}} {{.Status}}"
```

- [ ] **Step 2: Remove WSL containers and images**

```powershell
wsl -d Ubuntu -- bash -c "docker rm -f guacamole guacd 2>/dev/null; docker image prune -af 2>/dev/null"
```

- [ ] **Step 3: Disable WSL keep-alive scheduled task**

```powershell
Disable-ScheduledTask -TaskName "WSL Guacamole KeepAlive" -ErrorAction SilentlyContinue
```

- [ ] **Step 4: Remove port proxy rules**

```powershell
netsh interface portproxy delete v4tov4 listenport=8085 listenaddress=127.0.0.1
```

---

### Task 10: Final verification and memory update

**Agent:** integration-specialist
**Model:** haiku

- [ ] **Step 1: Verify all services running on Ubuntu VM**

```bash
ssh claude@172.31.251.99 "systemctl status guacd tomcat9 nginx --no-pager | grep -E '(guacd|tomcat9|nginx).*active'"
```

Expected: All three services active (running)

- [ ] **Step 2: End-to-end test**

Generate token → POST to Guacamole → verify VMConnect session established → screenshot

- [ ] **Step 3: Update memory file**

Update `guacamole.md` with:
- Native install details (paths, versions)
- Working security mode for VMConnect
- Service management commands
- Remove Docker/WSL2 sections or mark as historical

---

## Risk Register

| Risk | Mitigation | Fallback |
|------|-----------|----------|
| FreeRDP 3.x still can't connect to VMConnect | Task 3 tests CLI first before full install | Try building guacd from git main; try FreeRDP nightly |
| guacamole-server 1.5.5 doesn't compile against FreeRDP 3.x | Build from guacamole-server git main branch | Use FreeRDP 2.x system package and accept VMConnect may not work |
| Tomcat 9 not available on Ubuntu 24.04 | Install Tomcat 10 instead, adjust WAR deployment | Use Tomcat from Apache directly (not apt) |
| Token format issues | Reuse verified EncryptToken() logic from FuseCP C# | Test with simple username/password auth first |
| Network connectivity 2179 blocked | Test with `nc -zv 172.31.251.102 2179` from Ubuntu VM | Check Hyper-V host firewall |
