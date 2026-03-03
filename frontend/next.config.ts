import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  trailingSlash: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" },
      { source: "/accounts/:path*", destination: "http://127.0.0.1:8000/accounts/:path*" },
      // Django admin (legacy) — use /django-admin/ to avoid conflict with Next.js /admin/
      { source: "/django-admin/:path*", destination: "http://127.0.0.1:8000/admin/:path*" },
      // Legacy Django views for form submissions
      { source: "/exam/session/:path*", destination: "http://127.0.0.1:8000/exam/session/:path*" },
      { source: "/exam/dokkai/:slug/submit/:path*", destination: "http://127.0.0.1:8000/exam/dokkai/:slug/submit/:path*" },
      { source: "/vocab/api/:path*", destination: "http://127.0.0.1:8000/vocab/api/:path*" },
      { source: "/grammar/api/:path*", destination: "http://127.0.0.1:8000/grammar/api/:path*" },
      // Django media files (audio, images)
      { source: "/media/:path*", destination: "http://127.0.0.1:8000/media/:path*" },
    ];
  },
};

export default nextConfig;
