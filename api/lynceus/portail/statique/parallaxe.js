/* Accueil : progression du défilement et apparition des scènes.
 *
 * Amélioration progressive stricte — sans ce script, la page reste entièrement lisible :
 * le dégradé nuit→jour est porté par le CSS, et rien n'est masqué tant que la classe
 * « js-anime » n'a pas été posée ici. Le mouvement est abandonné si le système le refuse. */
(function () {
  "use strict";
  var racine = document.documentElement;
  var recit = document.querySelector(".recit");
  if (!recit) return;

  var mouvementRefuse = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Progression 0 → 1 sur la hauteur du document : pilote l'effacement des étoiles et la
  // montée de la lueur d'horizon (deux calc() en CSS, aucune écriture de style ici).
  var enAttente = false;
  function mesurer() {
    enAttente = false;
    var course = document.documentElement.scrollHeight - window.innerHeight;
    var p = course > 0 ? window.scrollY / course : 0;
    racine.style.setProperty("--progression", p.toFixed(4));
  }
  function auDefilement() {
    if (!enAttente) { enAttente = true; requestAnimationFrame(mesurer); }
  }
  window.addEventListener("scroll", auDefilement, { passive: true });
  window.addEventListener("resize", auDefilement, { passive: true });
  mesurer();

  // « js-anime » est posée par un script en ligne dans <head>, avant le premier rendu :
  // la poser ici produirait un clignotement (contenu peint, puis masqué). On ne fait que
  // la retirer si l'apparition progressive n'est finalement pas possible.
  if (mouvementRefuse || !("IntersectionObserver" in window)) {
    racine.classList.remove("js-anime");
    return;
  }
  var observateur = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (entree) {
      if (entree.isIntersecting) {
        entree.target.classList.add("vu");
        observateur.unobserve(entree.target);
      }
    });
  }, { rootMargin: "0px 0px -12% 0px", threshold: 0.15 });

  document.querySelectorAll(".revele").forEach(function (element) {
    observateur.observe(element);
  });
})();
