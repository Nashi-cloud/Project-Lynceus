from lynceus.moteur import prompt


def test_taxonomie_complete():
    taxonomie = prompt.charger_taxonomie()
    assert len(taxonomie) == 31
    for attendu in ("appel_a_la_peur", "verite_cachee", "cherry_picking", "deshumanisation",
                    "conflit_interet_commercial", "je_pose_des_questions"):
        assert attendu in taxonomie
    entree = taxonomie["appel_a_la_peur"]
    assert entree["nom"] and entree["gravite"] == "haute" and entree["definition"]


def test_prompt_systeme_injecte():
    version = prompt.resoudre_version("latest")
    systeme = prompt.prompt_systeme(version)
    assert "{{" not in systeme  # tous les gabarits remplacés
    assert "verite_cachee" in systeme  # taxonomie injectée
    assert '"categorie"' in systeme  # schéma injecté
    assert "Gabarit" not in systeme  # la section documentation n'est pas envoyée au modèle


def test_schema_sortie_llm_sans_champs_serveur():
    schema = prompt.schema_sortie_llm()
    for champ in ("meta", "url", "titre", "domaine", "version_schema"):
        assert champ not in schema["properties"]
    assert schema["properties"]["note"]["required"] == ["confiance"]
    assert "meta" not in schema["required"]


def test_resolution_versions():
    versions = prompt.versions_disponibles()
    assert "0.1.0" in versions
    assert prompt.resoudre_version("latest") == versions[-1]
