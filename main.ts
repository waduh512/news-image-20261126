// news-image-20261126: write the one-page world-news image to /output/entry.png.
//
// The image is entry.png in this repository (drawn with code by render.py:
// "THURSDAY 26 NOVEMBER 2026" — an atlas of the day's news: Trump hits
// 14 trading partners with new tariffs, Houthis claim a strike on Saudi
// Arabia's biggest refinery, Ukraine hits the Savasleyka air base and
// knocks out 5 planes, plus 31 more dated stories in 7 regions, every
// story pinned where it happened on a dark world map. This program copies
// it byte for byte, so two runs write identical bytes. No network, no
// randomness, Node 22 standard library only.
import { chmodSync, copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const src = join(root, "entry.png");
const outDir = "/output";
mkdirSync(outDir, { recursive: true });
const out = join(outDir, "entry.png");
copyFileSync(src, out);
chmodSync(out, 0o644);
console.log("wrote /output/entry.png");
