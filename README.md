# Guilde Algo & IA

Les projets des membres de la guilde, rangés par thème puis par sujet.

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
4. Remplir le `README.md` du projet.
5. Ajouter sa ligne dans `.github/CODEOWNERS` : `/<theme>/<sujet>/<projet>/ @<github-login>`.
6. Ouvrir une PR et suivre la checklist du template.

## Contribuer

- **`main` est protégée** : tout passe par une PR, avec une approbation et la CI au vert.
- **Chaque projet appartient à son auteur** (`.github/CODEOWNERS`) : une PR qui touche le projet de quelqu'un d'autre attend son approbation.
- **La CI vérifie la structure** : nommage, README présent, ligne CODEOWNERS, aucun `.env` commité, aucun fichier de plus de 10 Mo. Pour la lancer en local : `.github/scripts/check-structure.sh`.

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
