---
date: 2026-05-27
slug: codes-communautaires
description: Groupe de discussion de la 4ème rencontre plénière, Strasbourg 2026
---

# Codes communautaires

Comment un code de recherche devient-il un outil partagé, maintenu et cité par toute une communauté ? Synthèse d'un groupe de discussion de la [4ème rencontre plénière](../../workshops/workshop-2026.md).

<!-- more -->

## Les obstacles

- Peu de soutien pérenne aux développeurs.
- Un financement qui va aux nouveaux développements plutôt qu'à la maintenance.
- Une gouvernance et des responsabilités à clarifier.
- Une communauté de développeurs à construire et à faire vivre.
- Documentation, tests et support aux utilisateurs à assurer dans la durée.

> Quels mécanismes aideraient le mieux des codes de recherche à devenir des codes communautaires ?

## Souveraineté et infrastructures

Où héberger, archiver et préserver les codes ?

| Initiative | Rôle |
|------------|------|
| [GitLab du CNRS (Koda)](https://src.koda.cnrs.fr/) | forge nationale pour les laboratoires |
| [Data Terra](https://www.data-terra.org) | pourrait évoluer vers une forge logicielle dotée d'API |
| [Software Heritage](https://www.softwareheritage.org/) | archive du code source à long terme, lancée par Inria |
| [EPOS France](https://www.epos-france.fr/) | infrastructure de recherche Terre solide, rôle à préciser |
| GitHub, GitLab | plateformes très utilisées, hors du contrôle des institutions |

> Les codes communautaires doivent-ils s'appuyer sur des infrastructures nationales pour garantir leur pérennité et leur souveraineté ?

## Rendre les codes citables

Un code doit devenir une production scientifique à part entière. Un nouveau recensement des codes de la communauté pourrait partir de l'inventaire réalisé en 2023.

**Identifiants pérennes.** Un DOI doit désigner **une version précise**, pas une branche de développement. [Zenodo](https://zenodo.org/) attribue un DOI à chaque version, directement depuis GitHub. [Software Heritage](https://www.softwareheritage.org/) archive en plus tout l'historique du dépôt et ses auteurs, avec ses propres identifiants ([SWHID](https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html)). En France, [HAL accepte aussi le dépôt de code](https://doc.hal.science/deposer/deposer-le-code-source/).

> Chaque version officielle doit-elle recevoir un DOI et être préservée dans Software Heritage ?

**Articles logiciels.** Le [Journal of Open Source Software](https://joss.theoj.org/) (JOSS) offre une relecture légère et transparente, et une référence citable avec DOI. Quand c'est possible, mieux vaut toutefois publier dans les revues de la communauté, comme les [revues diamant](diamond-open-access.md) des géosciences.

> Les articles logiciels doivent-ils devenir un livrable standard des codes communautaires ?
