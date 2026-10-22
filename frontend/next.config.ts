import type { NextConfig } from "next";

const config: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/v1/apps/:path*", destination: "http://127.0.0.1:8000/api/v1/apps/:path*" },
      { source: "/api/v1/ai/:path*", destination: "http://127.0.0.1:8000/api/v1/ai/:path*" },
    ];
  },
  async headers() {
    return [{
      source: "/:path*",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "no-referrer" },
        { key: "Cache-Control", value: "no-store" },
      ],
    }];
  },
};

export default config;
