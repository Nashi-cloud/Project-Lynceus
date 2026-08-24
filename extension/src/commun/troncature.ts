/** Raccourcissement des pages trop longues pour l'instance.
 *
 * Refuser tout net un article long est le pire comportement : l'utilisateur n'y peut rien.
 * Analyser son début reste utile — à condition de le signaler, car la carte produite est
 * mise en cache et resservie à d'autres lecteurs. */

export interface Raccourcissement {
  texte: string;
  tronque: boolean;
}

/** Proportion minimale du texte conservée : on ne remonte pas chercher une frontière de
 * paragraphe au prix d'une part excessive du contenu analysable. */
const PROPORTION_MINIMALE = 0.8;

export function raccourcir(markdown: string, maximum: number): Raccourcissement {
  if (markdown.length <= maximum) return { texte: markdown, tronque: false };

  const coupe = markdown.slice(0, maximum);
  const finParagraphe = coupe.lastIndexOf("\n\n");
  // Couper au milieu d'une phrase donnerait au modèle un texte bancal à analyser : on
  // préfère la dernière frontière de paragraphe, si elle n'est pas trop loin en arrière.
  const texte = finParagraphe > maximum * PROPORTION_MINIMALE ? coupe.slice(0, finParagraphe) : coupe;
  return { texte, tronque: true };
}
