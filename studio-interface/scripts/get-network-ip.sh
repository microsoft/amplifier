#!/bin/bash

# Get network IP address for team testing
# This script detects your local network IP and updates .env.local

echo "🔍 Detecting network IP address..."

# Try to get IP from common network interfaces (macOS)
NETWORK_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | grep -v "inet 169.254" | awk '{print $2}' | head -n 1)

if [ -z "$NETWORK_IP" ]; then
  echo "❌ Could not detect network IP address"
  echo "   Make sure you're connected to WiFi or Ethernet"
  exit 1
fi

echo "✅ Network IP detected: $NETWORK_IP"
echo ""
echo "📋 Next steps:"
echo "   1. Add this line to .env.local:"
echo "      NEXT_PUBLIC_NETWORK_IP=$NETWORK_IP"
echo ""
echo "   2. Add this URL to Supabase redirect URLs:"
echo "      http://$NETWORK_IP:3000/auth/callback"
echo ""
echo "   3. Restart dev server: npm run dev"
echo ""
echo "   4. Share with team: http://$NETWORK_IP:3000"
echo ""

# Optional: Auto-update .env.local (commented out for safety)
# read -p "Update .env.local automatically? (y/n) " -n 1 -r
# echo
# if [[ $REPLY =~ ^[Yy]$ ]]; then
#   # Update or add NEXT_PUBLIC_NETWORK_IP
#   if grep -q "NEXT_PUBLIC_NETWORK_IP=" .env.local; then
#     sed -i '' "s/NEXT_PUBLIC_NETWORK_IP=.*/NEXT_PUBLIC_NETWORK_IP=$NETWORK_IP/" .env.local
#   else
#     echo "NEXT_PUBLIC_NETWORK_IP=$NETWORK_IP" >> .env.local
#   fi
#   echo "✅ Updated .env.local"
# fi
