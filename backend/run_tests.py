#!/usr/bin/env python3
"""
Script pour exécuter tous les tests du backend Alteris.
Génère des rapports de couverture et des statistiques.
"""
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Exécute une commande shell et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✅ {description} - Terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - Échec")
        return False


def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print("🧪 SUITE DE TESTS BACKEND ALTERIS")
    print("="*60)
    
    # Vérifier qu'on est dans le bon répertoire
    backend_dir = Path(__file__).parent.resolve()
    print(f"\n📁 Répertoire de travail: {backend_dir}")
    
    tests_dir = backend_dir / "tests"
    if not tests_dir.exists():
        print(f"\n❌ Erreur: Le dossier 'tests' n'existe pas dans {backend_dir}")
        sys.exit(1)
    
    print(f"✅ Dossier tests trouvé: {tests_dir}")
    
    # Liste des tests à exécuter
    test_modules = [
        ("tests/test_auth_unit.py", "Tests unitaires Auth"),
        ("tests/test_auth_integration.py", "Tests intégration Auth"),
        ("tests/test_apprenti_unit.py", "Tests unitaires Apprenti"),
        ("tests/test_apprenti_integration.py", "Tests intégration Apprenti"),
        ("tests/test_admin.py", "Tests Admin"),
        ("tests/test_tuteur_maitre_professeur.py", "Tests Tuteur/Maître/Professeur"),
        ("tests/test_jury.py", "Tests Jury"),
        ("tests/test_coordonatrice.py", "Tests Coordonatrice"),
        ("tests/test_responsable_cursus.py", "Tests Responsable Cursus"),
        ("tests/test_entreprise.py", "Tests Entreprise"),
        ("tests/test_ecole.py", "Tests Ecole"),
        ("tests/test_responsableformation.py", "Tests Responsable Formation"),
    ]
    
    # Option 1: Exécuter tous les tests ensemble
    if "--all" in sys.argv or "--fast" in sys.argv:
        success = run_command(
            "pytest tests/ -v --tb=short",
            "Exécution de tous les tests"
        )
        
        if not success:
            print("\n❌ Certains tests ont échoué")
            sys.exit(1)
    
    # Option 2: Exécuter module par module (par défaut)
    else:
        results = []
        for module, description in test_modules:
            success = run_command(
                f"pytest {module} -v --tb=short",
                description
            )
            results.append((description, success))
        
        # Résumé final
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60 + "\n")
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for description, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {description}")
        
        print(f"\n{'='*60}")
        print(f"Modules passés: {passed}/{total}")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT PASSÉS !")
        else:
            print(f"⚠️  {total - passed} module(s) en échec")
        print("="*60 + "\n")
        
        if passed != total:
            sys.exit(1)
    
    # Option coverage
    if "--coverage" in sys.argv:
        print("\n" + "="*60)
        print("📈 Génération du rapport de couverture")
        print("="*60 + "\n")
        
        run_command(
            "pytest tests/ --cov=auth --cov=apprenti --cov=admin "
            "--cov=tuteur --cov=maitre --cov=professeur "
            "--cov=jury --cov=coordonatrice --cov=responsable_cursus "
            "--cov=entreprise --cov=ecole --cov=responsableformation "
            "--cov-report=html --cov-report=term",
            "Génération du rapport de couverture"
        )
        
        print("\n📄 Rapport HTML généré dans: htmlcov/index.html")
    
    print("\n✅ Tests terminés avec succès !\n")


if __name__ == "__main__":
    main()
