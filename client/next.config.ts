import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/LDlinkRestWeb/:path*",
        destination: `http://${process.env.NEXT_PUBLIC_API_BASE_URL || "localhost:80"}/LDlinkRestWeb/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `http://${process.env.NEXT_PUBLIC_API_BASE_URL || "localhost:8080"}/LDlinkRest/:path*`,
      },
    ];
  },
};

export default nextConfig;
