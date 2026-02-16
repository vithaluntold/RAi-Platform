import type { NextConfig } from "next";

const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Proxy all /api/v1/* requests to the backend — eliminates CORS entirely
  rewrites: async () => [
    {
      source: '/api/v1/:path*',
      destination: `${backendUrl}/api/v1/:path*`,
    },
  ],
  headers: async () => [
    {
      source: '/:path*',
      headers: [
        { key: 'Cache-Control', value: 'no-store, must-revalidate' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
      ],
    },
  ],
};

export default nextConfig;
