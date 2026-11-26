import { Fzf, extendedMatch } from "./vendor/fzf/fzf.es.js";

/** The text a project is searched on: title, path, authors, stack and description. */
export const searchText = project =>
  [project.titre, project.theme, project.sujet, project.projet, ...project.auteurs, ...(project.stack ?? []), project.description].join(" ");

/** Return the projects that match the query, best first: fzf matching, accents ignored, every word must match. */
export function search(projects, query) {
  const finder = new Fzf(projects, { selector: searchText, casing: "case-insensitive", normalize: true, match: extendedMatch });
  return finder.find(query).map(entry => entry.item);
}
