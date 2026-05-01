/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone: required for Docker/Node.js production deployment (node .next/standalone/server.js)
  output: 'standalone',

  // Allow images from any source (for PWA)
  images: {
    unoptimized: true,
  },

  // Proxy API requests to FastAPI backend in development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
