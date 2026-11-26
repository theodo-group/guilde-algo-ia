# Guilde Algo & IA

Les projets des membres de la guilde, rangés par thème puis par sujet.

- **Index des projets, avec recherche** : https://theodo-group.github.io/guilde-algo-ia/
- **Page Notion de la guilde** : [Guilde Algo IA](https://app.notion.com/p/m33/Guilde-Algo-IA-1f1744af43ed4491948aa59646624eba)

## Structure

```
<theme>/
  <sujet>/
    <projet>/          # un projet = un dossier autonome
      README.md
      .env.example
      .gitignore
      src/
      data/
```

Exemple :

```
algo/
  knn/
    knn-iris-jdupont/
  dijkstra-astar/
ia/
  sdk-anthropic/
  adk/
```

## Ajouter un projet

1. Créer une branche depuis `main` (pas de fork : tout `theodo-group` a accès en écriture).
2. Choisir le thème et le sujet. Créer le dossier du sujet s'il n'existe pas.
3. Copier le template :
   ```bash
   cp -r _template <theme>/<sujet>/<projet>
   ```
4. Remplir le `README.md` du projet, avec son bloc de métadonnées pour apparaître dans l'index (optionnel).
5. Ajouter sa ligne dans `.github/CODEOWNERS` : `/<theme>/<sujet>/<projet>/ @<github-login>`.
6. Ouvrir une PR et suivre la checklist du template.

## Contribuer

- **`main` est protégée** : tout passe par une PR, avec une approbation et la CI au vert.
- **Chaque projet appartient à son auteur** (`.github/CODEOWNERS`) : une PR qui touche le projet de quelqu'un d'autre attend son approbation.
- **La CI vérifie la structure** : nommage, README présent, ligne CODEOWNERS, aucun `.env` commité, aucun fichier de plus de 10 Mo. Elle valide aussi le bloc de métadonnées quand il est présent. Pour la lancer en local :
  ```bash
  .github/scripts/check-structure.sh
  uv run --directory .github/project-index python -m project_index check
  ```

## Tags

Chaque projet a un tag `projet/<theme>/<sujet>/<projet>`, posé par la CI à chaque merge sur `main` sur le dernier commit de `main` qui touche son dossier. Ce tag appartient à la CI : s'il est déplacé à la main, il est remis en place au merge suivant. Il sert à retrouver le projet rapidement :

```bash
git fetch --tags --force
git checkout projet/ia/mlx/mlx-vs-pytorch-wadnet
```

Pour marquer un état précis (une session, une version), ajoute un tag fixe avec `@<label>` : `projet/<theme>/<sujet>/<projet>@<label>`, par exemple `projet/ia/mlx/mlx-vs-pytorch-wadnet@session-2026-03-11`. Git ne peut pas avoir à la fois `a/b` et `a/b/c`, d'où le `@`.

```bash
git tag projet/ia/mlx/mlx-vs-pytorch-wadnet@session-2026-03-11 <commit>
git push origin projet/ia/mlx/mlx-vs-pytorch-wadnet@session-2026-03-11
```

## Métadonnées

Optionnel. Un bloc YAML en tête du `README.md` d'un projet le décrit de façon standard et l'ajoute à l'[index](https://theodo-group.github.io/guilde-algo-ia/). La CI le valide quand il est présent. Sans ce bloc, le projet reste dans le repo mais n'apparaît pas dans l'index.

```yaml
---
titre: KNN sur Iris                         # requis
auteurs: [jdupont]                          # requis, logins GitHub
description: Ce que le projet montre.       # requis, une phrase
date: 2026-01-15                            # optionnel, date de la session
session: https://app.notion.com/p/...       # optionnel, lien vers la présentation
stack: [python, scikit-learn]               # optionnel
---
```

Le thème, le sujet et le projet sont déduits du chemin du dossier. L'index est reconstruit à chaque merge sur `main`. Les valeurs entre chevrons du template (`<...>`) sont refusées : remplis-les ou supprime le bloc.

## Développer sur ce repo

Pour le code du repo (`.github/`) ou d'un projet qui le souhaite, une bonne pratique est disponible : le skill Claude Code [`ub-mode`](.claude/skills/ub-mode/SKILL.md) et ses [règles d'architecture](.claude/skills/ub-mode/architecture.md). Ce n'est pas une règle : aucune CI ne les vérifie. Un projet qui les suit le dit dans son README.

## Conventions

- **Noms de dossiers** : minuscules, kebab-case, sans accent (`dijkstra-astar`, `sdk-anthropic`).
- **Nom du projet** : `<description-courte>-<auteur>` pour éviter les collisions (`knn-iris-jdupont`).
- **Un projet est autonome** : ses dépendances, sa config et son `.gitignore` vivent dans son dossier. Rien n'est partagé entre projets.
- **Secrets** : uniquement dans `.env` (ignoré par git). Lister les variables nécessaires dans `.env.example`, sans valeur.
- **Données** : dans `data/`, non versionnées. Le README du projet explique comment les obtenir.

## Licence

Par défaut, tout le repo est sous [licence MIT](LICENSE). Si tu ne veux pas de la MIT pour ton projet, ajoute ton propre fichier `LICENSE` à la racine de ton dossier projet : il remplace la licence générale pour ce dossier.
