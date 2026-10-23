#!/usr/bin/env node
// Parses every classic/module inline <script> in built HTML and fails if any
// is not valid JavaScript (e.g. TypeScript left in an is:inline/define:vars block).
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import vm from "node:vm";

const root = process.argv[2] ?? "dist";

function* htmlFiles(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* htmlFiles(p);
    else if (name.endsWith(".html")) yield p;
  }
}

const SCRIPT_RE = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
const JS_TYPES = new Set(["", "text/javascript", "module", "application/javascript"]);

let checked = 0;
const failures = [];

for (const file of htmlFiles(root)) {
  const html = readFileSync(file, "utf8");
  for (const m of html.matchAll(SCRIPT_RE)) {
    const attrs = m[1];
    const body = m[2];
    if (/\bsrc\s*=/.test(attrs) || !body.trim()) continue;
    const type = (attrs.match(/\btype\s*=\s*["']?([^"'\s>]+)/i)?.[1] ?? "").toLowerCase();
    if (!JS_TYPES.has(type)) continue;
    checked++;
    try {
      if (type === "module") new vm.SourceTextModule(body);
      else new vm.Script(body);
    } catch (err) {
      const line = html.slice(0, m.index).split("\n").length;
      failures.push(`${relative(root, file)}:${line}  ${err.message}`);
    }
  }
}

for (const f of failures) console.error(f);
console.log(`${checked} inline scripts checked, ${failures.length} with syntax errors`);
process.exit(failures.length ? 1 : 0);
