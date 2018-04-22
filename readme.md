
# Food ontology

This ontology is designed to handle culinary needs. Biological, chemical and nutritional components are also considered to improve usability and reliability.


## Overview

Items are mostly everything, from raw ingredients to compound dishes. This is not limited to edible concepts (e.g. brands and processing indications). Together, a directed acyclic graph is built, as commonly done in ontologies. For simplicity sake's, a custom format with weak annotation is used, which is closer to thesauri formalism than RDF-based ontologies.

In particular, the following relationships exist between items:
 * _product-of_ links attach a food to its producer, usually used to highlight the origin of milk, eggs and honey. Not to be confused with the remaining relationships, used to represents direct extraction or transformation (i.e. a steak is a beef derivate, not a beef product).
 * _derivative-of_ is the most generic relationship, which simply indicate the presence of an item, regardless of its transformation or extraction scheme. In particular, future versions are likely to introduce new specializations of this concept.
 * _part-of_ is a kind of derivate relationship, which indicates the usage of only some parts (e.g. seeds are part of fruits).
 * _made-of_ is the opposite derivate relationship, used for compositions with minimal transformations (e.g. egg dishes are made of eggs). In practice, non-straightforward transformations use __derivate-of__ links (e.g. wine is derivated from grape).
 * _kind-of_ dependencies are traditional __is-a__ relations, providing inheritance (more on transitivity below), which is the strongest derivation process. Multiple inheritance is allowed (e.g. tomatoes are both vegetables and fruits).

Implicit information is provided using inheritance and transitivity:
 * __kind-of__ relationships transfer all dependencies (e.g. chicken soup has chicken parts).
 * The other __derivate-of__ links transfer everything, except inheritance (e.g. lemon juice is not a fruit, but it is a fruit juice).
 * __product-of__ dependencies do not transfer anything (e.g. honey is not an insect).

Additional attributes can be specified, including names and references to other corpora. Currently, the following references are in-use (non-exhaustive, except is specified):
 * [Wikipedia](https://en.wikipedia.org/wiki/Main_Page), and therefore [DBPedia](http://wiki.dbpedia.org/)
 * [FNDDS](https://data.nal.usda.gov/dataset/food-and-nutrient-database-dietary-studies-fndds) and [SR](https://data.nal.usda.gov/dataset/composition-foods-raw-processed-prepared-usda-national-nutrient-database-standard-reference-release-28-0), both from USDA
 * [Swiss](http://www.naehrwertdaten.ch) food composition database

Other relationships and attributes can be used to refine taxonomies:
 * _substitute-of_ reports semantical equivalences (e.g. aspartame is a sugar substitute), which does not include practical substitutes (e.g. almond powder is not officially a substitute of flour).
 * _modifier_ markers are used to specify important aspects of the item (e.g. dried, cooked, canned...)


## License

The content of the project itself is licensed under the [Creative Commons Attribution Share Alike 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/), and the underlying source code used to process and format that content is licensed under [The Unlicense](https://unlicense.org/UNLICENSE).

Note that this does not apply to referenced corpora, which are often in public domain. Please consult the official websites for more information.
