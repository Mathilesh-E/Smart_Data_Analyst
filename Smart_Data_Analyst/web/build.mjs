import { createWriteStream } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const browserify = require("browserify");
const babelify = require("babelify");
const root = dirname(fileURLToPath(import.meta.url));
const output = resolve(root, "dist");
const assets = resolve(output, "assets");
await mkdir(assets, { recursive: true });

await new Promise((resolveBuild, rejectBuild) => {
  const bundler = browserify(resolve(root, "src/main.jsx"), { basedir: root });
  bundler.transform(babelify, {
    global: true,
    presets: ["@babel/preset-env", "@babel/preset-react"],
  });
  bundler.bundle()
    .on("error", rejectBuild)
    .pipe(createWriteStream(resolve(assets, "app.js")))
    .on("finish", resolveBuild)
    .on("error", rejectBuild);
});

await writeFile(resolve(assets, "styles.css"), await readFile(resolve(root, "src/styles.css")));
await writeFile(resolve(output, "index.html"), await readFile(resolve(root, "index.html")));
console.log("Production frontend written to web/dist");
