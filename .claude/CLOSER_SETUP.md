# Verrou Closer sur ce depot

Ce depot a maintenant `.claude/settings.json` qui branche le hook
`PreToolUse` de Closer avant chaque edition de fichier ou commande bash.
Ca ne fait rien tant que deux etapes locales (une seule fois, sur cette
machine) n'ont pas ete faites :

## 1. Exposer la commande `closer-hook` sur cette machine

Depuis votre clone local de `closer-for-team-` :

```
cd chemin/vers/closer-for-team-/packages/closer-solo
npm link
```

Ca rend `closer` et `closer-hook` disponibles partout sur cette
machine (verifiable avec `which closer-hook`).

## 2. Declarer ce depot dans le registre

Toujours depuis n'importe ou (le registre est global, pas lie a un
depot) :

```
closer add lrs LRS pro "$(pwd)" --status actif
```

A lancer depuis la racine de ce depot LRS en local, pour que `$(pwd)`
capture le bon chemin. Si un autre projet pro est deja actif, `add`
refusera — voir `closer list` et `closer activate --force` si besoin.

## Verification

Une fois les deux etapes faites, une tentative d'edition dans un autre
depot pro gele/inconnu doit etre bloquee par le hook avec un message
explicite. `closer status` doit afficher LRS comme chantier actif.

Reference complete : `docs/closer-solo-spec.md` et le README du depot
`closer-for-team-`.
