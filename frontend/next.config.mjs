/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://campusos-ifab.onrender.com/api/v1",
  },
};

export default nextConfig;
