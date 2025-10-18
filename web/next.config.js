/** @type {import('next').NextConfig} */

// Only set default for development, not production
const isProd = process.env.NODE_ENV === 'production'
if (!process.env.NEXT_PUBLIC_API_URL && !isProd) {
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
}

const nextConfig = {
  reactStrictMode: true,

  // Output standalone for Docker
  output: 'standalone',
}

module.exports = nextConfig
