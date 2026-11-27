import assert from "node:assert/strict";
import { cpSync, existsSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

// site/search.js imports ./vendor/fzf/fzf.es.js, which the build copies from node_modules
// (`npm ci`): lay out the same two files in a temporary folder and import search.js from there.
const root = fileURLToPath(new URL("..", import.meta.url));
const fzf = join(root, "node_modules", "fzf", "dist", "fzf.es.js");
if (!existsSync(fzf)) {
  throw new Error(`${fzf} is missing: run \`npm ci\` in .github/project-index; if it is installed, the fzf package layout changed`);
}
const site = mkdtempSync(join(tmpdir(), "project-index-"));
after(() => rmSync(site, { recursive: true, force: true }));
mkdirSync(join(site, "vendor", "fzf"), { recursive: true });
cpSync(join(root, "site", "search.js"), join(site, "search.js"));
cpSync(fzf, join(site, "vendor", "fzf", "fzf.es.js"));
const { search } = await import(pathToFileURL(join(site, "search.js")).href);

const dijkstra = {
  theme: "algo", sujet: "graphes", projet: "dijkstra-astar", titre: "Dijkstra et A*",
  auteurs: ["alice"], description: "Plus court chemin dans un réseau.",
};
const mlx = {
  theme: "ia", sujet: "mlx", projet: "mlx-vs-pytorch", titre: "MLX vs PyTorch",
  auteurs: ["Vlor999"], description: "Comparaison des pipelines d'entraînement.", stack: ["python", "mlx"],
};
const titles = query => search([dijkstra, mlx], query).map(p => p.titre);

test("a word matches with missing letters", () => {
  assert.deepEqual(titles("djkstr"), ["Dijkstra et A*"]);
  assert.deepEqual(titles("pytrch"), ["MLX vs PyTorch"]);
});

test("a project without stack is found", () => {
  assert.deepEqual(titles("alice"), ["Dijkstra et A*"]);
});

test("accents and case are ignored", () => {
  assert.deepEqual(titles("RESEAU"), ["Dijkstra et A*"]);
  assert.deepEqual(titles("entrainement"), ["MLX vs PyTorch"]);
});

test("every word must match", () => {
  assert.deepEqual(titles("vlor python"), ["MLX vs PyTorch"]);
  assert.deepEqual(titles("vlor alice"), []);
});
