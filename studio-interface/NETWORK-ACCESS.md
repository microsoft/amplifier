# Network Access Guide

**Share your Studio development server with your team on the local network.**

## Quick Start

### 1. Detect Your Network IP

```bash
npm run network:ip
```

This will show you your current network IP address (e.g., `10.17.112.52`).

### 2. Update Environment Variables

Add your network IP to `.env.local`:

```bash
NEXT_PUBLIC_NETWORK_IP=10.17.112.52
```

### 3. Configure Supabase

Go to your [Supabase Dashboard](https://supabase.com/dashboard/project/vjsxvugbsierphhgfslz/auth/url-configuration) and add:

**Redirect URLs:**
```
http://localhost:3000/auth/callback
http://10.17.112.52:3000/auth/callback
```

**Site URL:**
```
ic
```

### 4. Restart Dev Server

```bash
npm run dev:kill
npm run dev
```

### 5. Share with Team

Send your team this URL:
```
http://10.17.112.52:3000
```

---

## How It Works

### Environment Variable
The `NEXT_PUBLIC_NETWORK_IP` variable tells Next.js to:
- Accept connections from your network IP
- Allow server actions from that origin
- Configure magic links with the correct redirect URL

### Dynamic Configuration
When `NEXT_PUBLIC_NETWORK_IP` is set:
- `next.config.ts` adds it to `allowedOrigins`
- Auth callbacks use `window.location.origin` (works automatically)
- All API calls use relative paths (no hardcoding needed)

---

## When Your IP Changes

Your network IP changes when you:
- Reconnect to WiFi
- Switch networks
- Use VPN
- Restart router

**To update:**

```bash
# 1. Detect new IP
npm run network:ip

# 2. Update .env.local with new IP
NEXT_PUBLIC_NETWORK_IP=<new-ip>

# 3. Update Supabase redirect URLs
# Add new IP to: https://supabase.com/dashboard/...

# 4. Restart server
npm run dev:kill
npm run dev
```

---

## Troubleshooting

### "Connection Refused" Error

**Problem:** Team can't access `http://<your-ip>:3000`

**Solutions:**
1. Check firewall settings (allow port 3000)
2. Ensure you're on the same network
3. Verify server is running: `npm run dev:check`

### Magic Links Not Working

**Problem:** Auth redirect goes to localhost instead of network IP

**Solutions:**
1. Verify `NEXT_PUBLIC_NETWORK_IP` is set in `.env.local`
2. Add network IP to Supabase redirect URLs
3. Restart dev server after changing env vars

### "Origin Not Allowed" Error

**Problem:** API calls fail with CORS or origin errors

**Solutions:**
1. Check `NEXT_PUBLIC_NETWORK_IP` is set correctly
2. Restart dev server (Next.js needs to rebuild config)
3. Clear browser cache and reload

---

## Security Notes

### Local Network Only
Your dev server is only accessible on your local network (WiFi/LAN). It's not exposed to the internet.

### Don't Commit IP Addresses
The `.env.local` file is gitignored. Your network IP won't be committed to the repo.

### Production Deployment
This setup is for **development testing only**. Production apps should use proper domain names and SSL certificates.

---

## Alternative: ngrok (Internet Access)

If your team is remote (not on same network), use ngrok:

```bash
# Install ngrok
brew install ngrok

# Start tunnel
ngrok http 3000

# Share the ngrok URL (e.g., https://abc123.ngrok.io)
# Add it to Supabase redirect URLs
```

---

## Scripts Reference

| Command | Description |
|---------|-------------|
| `npm run network:ip` | Detect current network IP |
| `npm run dev` | Start dev server |
| `npm run dev:kill` | Stop all dev servers |
| `npm run dev:check` | Check if server is running |

---

## Example Workflow

**Day 1: Initial Setup**
```bash
# Detect IP
npm run network:ip
# Output: Network IP detected: 10.17.112.52

# Add to .env.local
echo "NEXT_PUBLIC_NETWORK_IP=10.17.112.52" >> .env.local

# Update Supabase dashboard (manual step)

# Start server
npm run dev

# Share with team
# "Hey team, test at: http://10.17.112.52:3000"
```

**Day 2: IP Changed**
```bash
# Detect new IP
npm run network:ip
# Output: Network IP detected: 10.17.115.88

# Update .env.local (manual edit)
# NEXT_PUBLIC_NETWORK_IP=10.17.115.88

# Update Supabase dashboard (manual step)

# Restart
npm run dev:kill && npm run dev

# Update team
# "New URL: http://10.17.115.88:3000"
```

---

## Support

If you run into issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Verify all steps in [Quick Start](#quick-start)
3. Check Supabase logs: https://supabase.com/dashboard/project/vjsxvugbsierphhgfslz/logs

---

**The artifact is the container. The experience is the product.**

Make sure your team has a great testing experience! 🚀
