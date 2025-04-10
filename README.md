# DevProject

---

# Prérequis

## Communication machine to machine

```
> Programme client qui envoie les entrées utilisateur au serveur
> Programme Serveur éxécuté ailleurs (sur une machine / VM différente) qui reçoit l'entrée client et envoie une réponse adéquate (nouvelle page de jeu ou rester sur la même en cas d'échec)
> Programme Client qui reçoit la réponse du serveur et affiche celle-ci à l'utilisateur
```

## Base de données

```
Table User :
-> id
-> nom
-> niveau actuel

Table Classement :
-> id
-> userID
-> place

Table Niveau :
-> id
-> nom
-> lettres acceptées
-> timer
-> difficulté

Table Entité
-> id
-> nom
-> mot pour vaincre
-> timer avant attaque
-> mortalité
```

## Algorithme avancé

```
Génération aléatoire de niveau si le niveau rentré n'existe pas (ex : niveau 'renard' n'existe pas)
Gérance de sous-niveau si le niveau rentré est un synonyme d'un niveau existant (ex : décéder et mourir)

> Génération d'une nouvelle donnée dans la table Niveau
> Arrière plan généré pour cacher les lettres acceptées (possible de les trouver évidemment)
```

## Intéraction utilisateur

```
> Champ texte
> Bouton connexion
> Bouton inscription
```

## CRUD

```
Possibilité de gérer en temps qu'administrateur les User pour en créer de nouveaux, en changer les données ou en supprimer
Possibilité de gérer également le classement des joueurs 
```

---

# Features

## Gestion de back-up 1

```
Back up sur un server autre afin de conserver et garantir les données toutes les semaines à 3:00 AM (Paris)
```

## réinitialisation des niveaux 1

```
Réinitialisation de la table niveau (suppression de toutes les données) excepté celles où chaque joueur se trouve (voir niveau dans la table joueur)
```

## Gestion multijoueur  2

```
Joueurs connéctés sur un serveur 'lobby' local pouvant jouer ensemble
```

## Gestion du lobby     1

```
Le host peut sortir des joueurs non désirables
Le host peut définir les règles de la course (nombre de manches)
```

## Mode course multijoueur  1

```
Les joueurs dans un même lobby peuvent tenter d'être le premier à finir une manche
Plusieurs manches possibles selon les règles, classement global au temps total
```

## Gestion de la langue de l'utilisateur    2

```
L'utilisateur rentrera sa langue de jeu et le serveur s'adaptera, traduisant les mots en mots de la langue de l'utilisateur
(fin -> end -> final -> ende -> ...)
```

## Système d'achievements   1

```
Les joueurs peuvent gagner des badges et des éléments de personnalisation en fonction de leurs performances ou niveaux débloqués
```

## Système de personnalisation  2

```
Les joueurs peuvent personnaliser leur profil ou style de boutons et champ de texte selon les personnalisations débloqués
```