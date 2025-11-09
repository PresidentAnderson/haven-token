/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },
  webpack: (config) => {
    config.resolve.fallback = {
      fs: false,
      net: false,
      tls: false,
      encoding: false
    };
    config.externals.push('pino-pretty', 'lokijs', 'encoding');
    return config;
  },
  env: {
    NEXT_PUBLIC_APP_NAME: 'HAVEN Token',
    NEXT_PUBLIC_APP_DESCRIPTION: 'Blockchain Loyalty for PVT Hospitality',
  },
}

module.exports = nextConfig
