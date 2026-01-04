import type { NextConfig } from "next";

function _stripTrailingSlash(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

const backendUrl = _stripTrailingSlash(
  process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "http://localhost:8000"
);

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Proxy to FastAPI backend to avoid CORS and env mismatch issues.
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
