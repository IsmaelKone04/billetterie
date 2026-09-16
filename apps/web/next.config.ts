import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Nécessaire pour l'image Docker de production (docker/web.Dockerfile) :
  // produit un serveur autonome sans dépendre de node_modules complet.
  output: "standalone",
};

export default nextConfig;
