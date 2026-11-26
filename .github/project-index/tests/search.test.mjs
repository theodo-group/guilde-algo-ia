import assert from "node:assert/strict";
import { test } from "node:test";

import { search } from "../site/search.js";

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
