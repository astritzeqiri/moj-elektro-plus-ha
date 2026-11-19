// Reproducible build: bundles src/ into the integration package.
//   npm ci && npm run build
// `--check` verifies the committed bundle equals a fresh build (used in CI).

import { build } from "esbuild";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, "../custom_components/mojelektro_plus/frontend/mojelektro-panel.js");
const check = process.argv.includes("--check");

const result = await build({
  entryPoints: [resolve(here, "src/panel.js")],
  bundle: true,
  format: "esm",
  target: "es2021",
  minify: true,
  legalComments: "none",
  write: false,
  banner: { js: "/* Moj Elektro Plus panel. Source: frontend/src (MIT). Built with esbuild. */" },
});
const code = result.outputFiles[0].text;

if (check) {
  const current = readFileSync(out, "utf8");
  if (current !== code) {
    console.error("Bundle is out of date. Run `npm run build` in frontend/ and commit it.");
    process.exit(1);
  }
  console.log("Bundle is up to date.");
} else {
  writeFileSync(out, code);
  console.log(`Wrote ${out} (${code.length} bytes)`);
}
