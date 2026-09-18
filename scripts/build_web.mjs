import { build } from "esbuild";
import { resolve } from "node:path";

const root = process.cwd();

await build({
  absWorkingDir: root,
  entryPoints: [resolve(root, "frontend", "app.js")],
  outfile: resolve(root, "dist", "app.js"),
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
});
