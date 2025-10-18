/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Output standalone for Docker
  output: 'standalone',

/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production'
if (!process.env.NEXT_PUBLIC_API_URL && !isProd) {
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
}

const nextConfig = {
  reactStrictMode: true,

  // Output standalone for Docker
  output: 'standalone',

  // Explicitly expose only whitelisted public envs
  experimental: {
    runtimeEnv: {
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    },
  },
}

export default nextConfig
}

module.exports = nextConfig
