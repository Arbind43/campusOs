/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://campus-os-zi43-56zulhl2w-mundaarbind73-4443s-projects.vercel.app/api/v1",
  },
};

export default nextConfig;
