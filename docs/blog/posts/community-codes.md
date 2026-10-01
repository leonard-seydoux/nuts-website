---
type: Discussion
date: 2026-05-27
slug: codes-communautaires
description: Groupe de discussion des Journées NuTS 2026, à Strasbourg
---

# Codes communautaires

Comment un code de recherche devient-il un outil partagé, maintenu et cité par toute une communauté ? Ce billet résume les échanges d'un groupe de discussion des [Journées NuTS 2026](../../workshops/workshop-2026.md).

<!-- more -->

## Les obstacles

Le premier obstacle est humain : les développeurs reçoivent peu de soutien dans la durée, et les financements vont plus volontiers aux nouveaux développements qu'à la maintenance. Un code communautaire demande pourtant un travail continu. Il faut documenter, tester et accompagner les utilisateurs, mais aussi construire une communauté de développeurs et la faire vivre. La gouvernance et le partage des responsabilités restent souvent à clarifier.

La question qui a guidé la discussion était donc de savoir quels mécanismes aideraient le mieux un code de recherche à devenir un code communautaire.

## Souveraineté et infrastructures

Héberger, archiver et préserver les codes suppose de choisir des infrastructures. Le CNRS propose une forge nationale pour les laboratoires, le [GitLab Koda](https://src.koda.cnrs.fr/). [Data Terra](https://www.data-terra.org) pourrait de son côté évoluer vers une forge logicielle dotée d'API, et le rôle de l'infrastructure de recherche [EPOS France](https://www.epos-france.fr/) reste à préciser. Pour l'archivage à long terme, [Software Heritage](https://www.softwareheritage.org/), lancé par Inria, conserve le code source. GitHub et GitLab restent enfin très utilisés, mais échappent au contrôle des institutions.

Le groupe s'est demandé si les codes communautaires devaient s'appuyer sur ces infrastructures nationales pour garantir leur pérennité et leur souveraineté.

## Rendre les codes citables

Un code doit devenir une production scientifique à part entière. Pour mieux connaître ceux de la communauté, un nouveau recensement pourrait partir de l'inventaire réalisé en 2023.

Être citable passe d'abord par un identifiant pérenne. Un DOI doit désigner une version précise du code, et non une branche de développement. [Zenodo](https://zenodo.org/) attribue un DOI à chaque version, directement depuis GitHub. [Software Heritage](https://www.softwareheritage.org/) archive en plus tout l'historique du dépôt et ses auteurs, avec ses propres identifiants ([SWHID](https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html)). En France, [HAL accepte aussi le dépôt de code](https://doc.hal.science/deposer/deposer-le-code-source/). Une piste serait que chaque version officielle reçoive un DOI et soit préservée dans Software Heritage.

Les articles logiciels sont l'autre levier. Le [Journal of Open Source Software](https://joss.theoj.org/) (JOSS) offre une relecture légère et transparente, et une référence citable avec un DOI. Quand c'est possible, mieux vaut toutefois publier dans les revues de la communauté, comme les [revues diamant](diamond-open-access.md) des géosciences. Reste à savoir si ces articles doivent devenir un livrable standard des codes communautaires.
