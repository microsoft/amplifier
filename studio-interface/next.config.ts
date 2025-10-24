import type { NextConfig } from "next";

// Build allowed origins list dynamically
const allowedOrigins = ['localhost:3000'];
const allowedDevOrigins: string[] = [];

if (process.env.NEXT_PUBLIC_NETWORK_IP) {
  allowedOrigins.push(`${process.env.NEXT_PUBLIC_NETWORK_IP}:3000`);
  allowedDevOrigins.push(process.env.NEXT_PUBLIC_NETWORK_IP);
}

const nextConfig: NextConfig = {
  // Allow network access for team testing
  allowedDevOrigins,

  // Explicitly bind to all interfaces
  // This ensures Next.js accepts connections from network IP
  ...(process.env.NODE_ENV === 'development' && {
    async headers() {
      return [
        {
          source: '/:path*',
          headers: [
            { key: 'Access-Control-Allow-Origin', value: '*' },
            { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE,OPTIONS' },
            { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
          ],
        },
      ];
    },
  }),

  experimental: {
    serverActions: {
      allowedOrigins,
    },
  },
};

export default nextConfig;
