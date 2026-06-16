import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker runtime stage.
  output: "standalone",
  // Lint runs in CI, not during the production image build.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
