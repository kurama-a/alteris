# Tests Backend - Projet Alteris

Ce document décrit la suite de tests complète pour le backend du projet Alteris (plateforme de gestion d'apprentissage).

## 📋 Vue d'ensemble

La suite de tests couvre l'ensemble des modules du backend :
- ✅ **Auth** : Authentification, autorisation, JWT, gestion utilisateurs
- ✅ **Apprenti** : Gestion des apprentis, entretiens, documents, compétences
- ✅ **Admin** : Administration, gestion promotions, associations
- ✅ **Tuteur** : Gestion des tuteurs pédagogiques
- ✅ **Maître** : Gestion des maîtres d'apprentissage
- ✅ **Professeur** : Gestion des professeurs
- ✅ **Jury** : Gestion des jurys de soutenance
- ✅ **Coordonatrice** : Gestion des coordinatrices
- ✅ **Responsable Cursus** : Gestion des responsables de cursus
- ✅ **Entreprise** : Gestion des entreprises partenaires
- ✅ **Ecole** : Gestion des écoles partenaires
- ✅ **Responsable Formation** : Gestion des responsables de formation
- ✅ **Security** : Rate limiting, headers sécurité, validation requêtes
- ✅ **Cache** : Système de cache LRU avec TTL
- ✅ **Performance** : Pagination, streaming, monitoring mémoire
- ✅ **Security Advanced** : Brute force, audit, sanitization, JWT avancé

## 🏗️ Structure des tests

```
backend/
├── tests/
│   ├── __init__.py                          # Package init
│   ├── conftest.py                          # Fixtures partagées (mock DB, données test, tokens JWT)
│   ├── test_auth_unit.py                    # Tests unitaires auth (~400 lignes)
│   ├── test_auth_integration.py             # Tests intégration auth (~350 lignes)
│   ├── test_apprenti_unit.py                # Tests unitaires apprenti (~350 lignes)
│   ├── test_apprenti_integration.py         # Tests intégration apprenti (~350 lignes)
│   ├── test_admin.py                        # Tests admin (unit + integration, ~400 lignes)
│   ├── test_tuteur_maitre_professeur.py     # Tests tuteur/maître/professeur (~300 lignes)
│   ├── test_jury.py                         # Tests jury (~450 lignes)
│   ├── test_coordonatrice.py                # Tests coordonatrice (~400 lignes)
│   ├── test_responsable_cursus.py           # Tests responsable cursus (~450 lignes)
│   ├── test_entreprise.py                   # Tests entreprise (~450 lignes)
│   ├── test_ecole.py                        # Tests ecole (~350 lignes)
│   ├── test_responsableformation.py         # Tests responsable formation (~400 lignes)
│   ├── test_security.py                     # Tests sécurité de base (~200 lignes)
│   ├── test_security_advanced.py            # Tests sécurité avancée (~400 lignes)
│   ├── test_cache.py                        # Tests système de cache (~300 lignes)
│   ├── test_performance.py                  # Tests optimisation performance (~350 lignes)
│   └── README.md                            # Documentation des tests
├── pytest.ini                               # Configuration pytest
└── run_tests.py                             # Script pour exécuter tous les tests
```

## 🚀 Installation

### Prérequis
```bash
# Python 3.8+
python --version

# Dépendances de test
pip install pytest pytest-asyncio httpx
```

### Installation des dépendances
```bash
cd backend
pip install -r requirements.txt
```

## 🧪 Exécution des tests

### Tous les tests
```bash
# Depuis le dossier backend/
pytest

# Avec plus de verbosité
pytest -v

# Avec coverage
pytest --cov=auth --cov=apprenti --cov=admin --cov-report=html
```

### Tests par module
```bash
# Module auth
pytest tests/test_auth_unit.py tests/test_auth_integration.py

# Module apprenti
pytest tests/test_apprenti_unit.py tests/test_apprenti_integration.py

# Module admin
pytest tests/test_admin.py

# Module jury
pytest tests/test_jury.py

# Module coordonatrice
pytest tests/test_coordonatrice.py

# Module responsable_cursus
pytest tests/test_responsable_cursus.py

# Module entreprise
pytest tests/test_entreprise.py

# Module ecole
pytest tests/test_ecole.py

# Module responsable formation
pytest tests/test_responsableformation.py

# Tous les modules tuteur/maître/professeur
pytest tests/test_tuteur_maitre_professeur.py
```

### Tests par type
```bash
# Seulement les tests unitaires
pytest -k "unit"

# Seulement les tests d'intégration
pytest -k "integration or Route"

# Tests spécifiques
pytest tests/test_auth_unit.py::TestPasswordHashing
pytest tests/test_apprenti_integration.py::TestHealthRoute
```

### Tests par marker
```bash
# Tests d'un module spécifique (si markers ajoutés)
pytest -m auth
pytest -m apprenti
pytest -m admin
```

## 📊 Couverture des tests

### Par module

#### Auth (`test_auth_unit.py` + `test_auth_integration.py`)
- ✅ Hashing de mots de passe (bcrypt)
- ✅ Tokens JWT (création, validation, expiration)
- ✅ Normalisation de données
- ✅ Génération de mots de passe
- ✅ Enregistrement utilisateur
- ✅ Connexion utilisateur
- ✅ Récupération utilisateur actuel
- ✅ Mise à jour profil utilisateur
- ✅ Génération d'email par rôle
- ✅ Récupération de mot de passe
- ✅ Enregistrement d'entité
- ✅ Routes API : `/register`, `/login`, `/me`, `/users`, `/generate-email`, `/recover-password`, `/register-entity`
- ✅ Validation des payloads
- ✅ Fonctionnalités de sécurité

#### Apprenti (`test_apprenti_unit.py` + `test_apprenti_integration.py`)
- ✅ Construction de profil complet
- ✅ Récupération infos entreprise, école, tuteurs
- ✅ Gestion des entretiens (CRUD)
- ✅ Notation des entretiens
- ✅ Gestion des documents du journal
- ✅ Upload de documents
- ✅ Commentaires sur documents
- ✅ Gestion des compétences
- ✅ Routes API : `/health`, `/infos-completes`, `/entretien`, `/documents`, `/competences`
- ✅ Validation des payloads
- ✅ Workflow complet entretien

#### Admin (`test_admin.py`)
- ✅ Récupération apprentis par année académique
- ✅ Listage de tous les apprentis
- ✅ Suppression utilisateur
- ✅ Modification utilisateur
- ✅ Listage des promotions
- ✅ Création/mise à jour promotion
- ✅ Listage responsables cursus
- ✅ Association tuteur
- ✅ Association maître
- ✅ Association entreprise
- ✅ Routes API : `/apprentis`, `/promos`, `/associer-tuteur`, `/associer-maitre`, `/associer-entreprise`
- ✅ Validation des payloads

#### Tuteur/Maître/Professeur (`test_tuteur_maitre_professeur.py`)
- ✅ Health checks
- ✅ Profils utilisateur
- ✅ Récupération infos complètes
- ✅ Routes API : `/health`, `/profile`, `/infos-completes`
- ✅ Modèles de données
- ✅ Gestion erreurs DB

#### Jury (`test_jury.py`)
- ✅ Health check
- ✅ Profil jury
- ✅ Modèles JuryStatus, MemberDetails, JuryCreateRequest
- ✅ Listage des jurys
- ✅ Récupération d'un jury
- ✅ Création de jury
- ✅ Mise à jour de jury
- ✅ Suppression de jury
- ✅ Promotions timeline
- ✅ Fonctions utilitaires (parse_object_id, serialize_jury)
- ✅ Routes API : `/health`, `/profile`, `/juries`, `/promotions-timeline`
- ✅ Validation des payloads

#### Coordonatrice (`test_coordonatrice.py`)
- ✅ Health check
- ✅ Profil coordonatrice
- ✅ Modèles User, UserUpdate
- ✅ Création coordonatrice
- ✅ Mise à jour coordonatrice
- ✅ Suppression coordonatrice
- ✅ Sérialisation documents
- ✅ Routes API : `/health`, `/profile`, `/`, `/{id}`
- ✅ Validation des payloads

#### Responsable Cursus (`test_responsable_cursus.py`)
- ✅ Health check
- ✅ Modèles User, UserUpdate
- ✅ Récupération infos complètes
- ✅ Création responsable cursus
- ✅ Mise à jour responsable cursus
- ✅ Suppression responsable cursus
- ✅ Sérialisation documents
- ✅ Routes API : `/health`, `/infos-completes/{id}`, `/`, `/{id}`
- ✅ Validation des payloads

#### Entreprise (`test_entreprise.py`)
- ✅ Health check
- ✅ Modèles Entity, EntityUpdate
- ✅ Listage des entreprises
- ✅ Récupération infos complètes
- ✅ Création entreprise
- ✅ Mise à jour entreprise
- ✅ Suppression entreprise
- ✅ Sérialisation documents
- ✅ Routes API : `/health`, `/`, `/infos-completes/{id}`, `/{id}`
- ✅ Validation des payloads

---

## 🔐 Modules de Sécurité

### Architecture de sécurité

Le backend Alteris implémente une architecture de sécurité multi-couches :

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Rate Limiting (InMemoryRateLimiter)                    │
│  - 100 requêtes/minute par IP                                    │
│  - Protection contre DoS                                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Security Headers (SecurityHeadersMiddleware)           │
│  - X-Content-Type-Options: nosniff                              │
│  - X-Frame-Options: DENY                                        │
│  - X-XSS-Protection: 1; mode=block                              │
│  - Strict-Transport-Security (HSTS)                             │
│  - Content-Security-Policy                                       │
│  - Cache-Control: no-store                                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Request ID (RequestIDMiddleware)                       │
│  - Génération UUID unique par requête                            │
│  - Traçabilité des logs                                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Input Validation (RequestValidationMiddleware)         │
│  - Limite taille body (1MB)                                      │
│  - Validation Content-Type                                       │
│  - Détection requêtes malformées                                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: Input Sanitization (sanitization.py)                   │
│  - Détection XSS (scripts, événements JS)                        │
│  - Détection NoSQL Injection ($gt, $regex, etc.)                │
│  - Détection Path Traversal (../, etc.)                         │
│  - Nettoyage HTML (balises dangereuses)                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 6: Brute Force Protection (brute_force.py)                │
│  - Lockout progressif (5→15min, 10→1h, 15→24h)                  │
│  - Protection par IP                                             │
│  - Protection par compte                                         │
│  - Détection attaques distribuées                               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 7: JWT Authentication (jwt_manager.py)                    │
│  - Access tokens (courte durée: 60 min)                          │
│  - Refresh tokens (longue durée: 7 jours)                        │
│  - Rotation automatique des tokens                               │
│  - Révocation individuelle/globale                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 8: Audit Logging (audit.py)                               │
│  - Journalisation des actions sensibles                          │
│  - Types: LOGIN, DATA_ACCESS, DATA_MODIFY, PERMISSION_CHANGE     │
│  - Stockage MongoDB avec détails complets                        │
│  - Décorateur @audit_action pour auto-logging                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LOGIC                           │
└─────────────────────────────────────────────────────────────────┘
```

---

### Security Base (`test_security.py`)

Tests du module `common/security.py` :

- ✅ **Rate Limiting**
  - `InMemoryRateLimiter` : Limite le nombre de requêtes par IP
  - Test limite 100 requêtes/60 secondes
  - Test reset automatique après expiration
  - Test obtention état actuel du rate limit
  
- ✅ **Security Headers**
  - `SecurityHeadersMiddleware` : Ajoute les headers de sécurité
  - Headers testés : X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
  - Strict-Transport-Security (HSTS)
  - Content-Security-Policy
  
- ✅ **Request Validation**
  - `RequestValidationMiddleware` : Valide les requêtes entrantes
  - Limite de taille body (1MB par défaut)
  - Validation Content-Type
  
- ✅ **Request ID**
  - `RequestIDMiddleware` : Génère un UUID unique par requête
  - Header X-Request-ID dans les réponses

```python
# Exemple de tests
class TestInMemoryRateLimiter:
    async def test_allows_requests_within_limit(self):
        limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
        for _ in range(10):
            allowed, _ = await limiter.is_allowed("127.0.0.1")
            assert allowed

    async def test_blocks_requests_over_limit(self):
        limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            await limiter.is_allowed("127.0.0.1")
        allowed, _ = await limiter.is_allowed("127.0.0.1")
        assert not allowed
```

---

### Security Advanced (`test_security_advanced.py`)

Tests des modules de sécurité avancée :

#### Brute Force Protection (`common/brute_force.py`)
- ✅ **Enregistrement tentatives échouées**
- ✅ **Lockout progressif**
  - 5 tentatives → 15 minutes de lockout
  - 10 tentatives → 1 heure de lockout
  - 15+ tentatives → 24 heures de lockout
- ✅ **Reset après succès**
- ✅ **Lockout par IP**
- ✅ **Détection attaques distribuées** (plusieurs IPs sur même compte)

```python
# Exemple de tests
class TestBruteForceProtection:
    async def test_lockout_after_max_attempts(self):
        protection = BruteForceProtection(max_attempts=3)
        for _ in range(3):
            await protection.record_failed_attempt("user@test.com", "127.0.0.1")
        is_locked, remaining = await protection.is_locked("user@test.com")
        assert is_locked
        assert remaining > 0
```

#### Input Sanitization (`common/sanitization.py`)
- ✅ **Nettoyage chaînes** : Suppression caractères de contrôle, trim
- ✅ **Nettoyage HTML** : Suppression balises script, style, iframe, etc.
- ✅ **Sanitization MongoDB** : Protection contre injection NoSQL
- ✅ **Détection XSS**
  - Balises `<script>`
  - Attributs événements (`onclick`, `onerror`, etc.)
  - Protocoles dangereux (`javascript:`, `data:`)
- ✅ **Détection NoSQL Injection**
  - Opérateurs MongoDB (`$gt`, `$ne`, `$regex`, `$where`)
  - Expressions de requête malveillantes
- ✅ **Détection Path Traversal** (`../`, `..\\`)
- ✅ **Décorateur `@validate_input`** pour validation automatique

```python
# Exemple de tests
class TestSanitization:
    def test_detect_xss_script_tag(self):
        assert detect_xss("<script>alert('xss')</script>") is True

    def test_detect_nosql_injection(self):
        assert detect_nosql_injection('{"$gt": ""}') is True

    def test_sanitize_html_removes_script(self):
        result = sanitize_html("<p>Hello</p><script>bad</script>")
        assert "<script>" not in result
```

#### JWT Manager (`common/jwt_manager.py`)
- ✅ **Création paire de tokens** (access + refresh)
- ✅ **Validation access token**
- ✅ **Refresh token rotation**
- ✅ **Révocation token individuel**
- ✅ **Révocation globale** (tous les tokens d'un utilisateur)
- ✅ **Gestion expiration**

```python
# Exemple de tests
class TestJWTManager:
    async def test_create_token_pair(self):
        manager = TokenManager(secret_key="test-secret")
        tokens = await manager.create_token_pair(user_id="123", role="admin")
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_refresh_token_rotation(self):
        manager = TokenManager(secret_key="test-secret")
        tokens = await manager.create_token_pair(user_id="123", role="user")
        new_tokens = await manager.refresh_access_token(tokens.refresh_token)
        assert new_tokens.access_token != tokens.access_token
```

#### Audit Service (`common/audit.py`)
- ✅ **Logging événements**
  - `LOGIN_SUCCESS`, `LOGIN_FAILURE`
  - `DATA_ACCESS`, `DATA_MODIFY`, `DATA_DELETE`
  - `PERMISSION_CHANGE`, `SECURITY_ALERT`
- ✅ **Stockage MongoDB avec métadonnées**
- ✅ **Décorateur `@audit_action`**
- ✅ **Récupération logs par utilisateur/période**

```python
# Exemple de tests
class TestAuditService:
    async def test_log_event(self):
        service = AuditService()
        await service.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id="123",
            details={"ip": "127.0.0.1"}
        )
        # Vérifie que l'événement est loggé

    async def test_get_user_audit_log(self):
        service = AuditService()
        logs = await service.get_user_audit_log(user_id="123", limit=10)
        assert isinstance(logs, list)
```

---

### Cache (`test_cache.py`)

Tests du module `common/cache.py` :

- ✅ **LRUCache**
  - Mise en cache avec TTL
  - Éviction LRU (Least Recently Used)
  - Expiration automatique
  - Nettoyage périodique
  
- ✅ **Décorateurs**
  - `@cached` : Cache résultat de fonction async
  - `@cache_response` : Cache réponse complète
  
- ✅ **QueryCache**
  - Cache spécialisé pour requêtes MongoDB
  - Invalidation par collection/pattern

```python
# Exemple de tests
class TestLRUCache:
    async def test_cache_set_and_get(self):
        cache = LRUCache(max_size=100)
        await cache.set("key", "value", ttl=300)
        result = await cache.get("key")
        assert result == "value"

    async def test_cache_expiration(self):
        cache = LRUCache(max_size=100)
        await cache.set("key", "value", ttl=1)
        await asyncio.sleep(1.5)
        result = await cache.get("key")
        assert result is None

    async def test_lru_eviction(self):
        cache = LRUCache(max_size=3)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        await cache.get("a")  # "a" devient le plus récent
        await cache.set("d", 4)  # "b" est évincé
        assert await cache.get("b") is None
```

---

### Performance (`test_performance.py`)

Tests du module `common/performance.py` :

- ✅ **Pagination**
  - `PaginatedResult` : Résultat paginé standardisé
  - `paginate_cursor` : Pagination offset-based
  - `cursor_pagination` : Pagination cursor-based (performante)
  
- ✅ **Streaming**
  - `stream_documents` : Générateur async pour grandes collections
  - Batch size configurable
  
- ✅ **QueryOptimizer**
  - Optimisation automatique des requêtes MongoDB
  - Suggestion d'index
  - Détection requêtes lentes
  
- ✅ **PerformanceMetrics**
  - Monitoring mémoire
  - Temps de réponse
  - Compteurs requêtes
  
- ✅ **Memory Monitoring**
  - Détection dépassement seuil
  - Garbage collection forcé si nécessaire

```python
# Exemple de tests
class TestPagination:
    async def test_paginated_result(self):
        result = PaginatedResult(
            items=[1, 2, 3],
            total=100,
            page=1,
            page_size=3
        )
        assert result.total_pages == 34
        assert result.has_next is True
        assert result.has_prev is False

class TestPerformanceMetrics:
    def test_memory_monitoring(self):
        metrics = PerformanceMetrics()
        memory_mb = metrics.get_memory_usage()
        assert memory_mb > 0
```

---

## 🛠️ Architecture des tests

### Fixtures partagées (`conftest.py`)
```python
# Mock MongoDB
- mock_db: Mock de la base de données
- mock_collection: Mock d'une collection MongoDB
- async_cursor_factory: Générateur de curseurs async

# Données de test
- sample_apprenti_data
- sample_tuteur_data
- sample_maitre_data
- sample_professeur_data
- sample_entreprise_data
- sample_promotion_data
- sample_entretien_data
- sample_document_data
- sample_coordonatrice_data
- sample_responsable_cursus_data

# Tokens JWT
- valid_token: Token valide
- expired_token: Token expiré

# IDs ObjectId
- sample_object_ids: Dict d'IDs pour les tests
```

### Pattern de test
```python
# Tests unitaires
@pytest.mark.asyncio
async def test_function_name():
    # Arrange: Configuration mocks et données
    # Act: Appel de la fonction
    # Assert: Vérification résultats

# Tests intégration
def test_route_name(client, fixtures):
    # Arrange: Configuration mocks
    # Act: Appel API via TestClient
    # Assert: Vérification status code et réponse
```

## 📈 Statistiques

- **Fichiers de test** : 17
- **Lignes de code de test** : ~7000+
- **Fixtures partagées** : 25+
- **Classes de test** : 150+
- **Fonctions de test** : 369+
- **Modules couverts** : 16/16 (100%)

### Répartition des tests

| Module | Tests | Description |
|--------|-------|-------------|
| Auth | ~70 | Authentification, JWT, utilisateurs |
| Apprenti | ~50 | Gestion apprentis, entretiens, documents |
| Admin | ~25 | Administration, promotions |
| Tuteur/Maître/Professeur | ~20 | Encadrants pédagogiques |
| Jury | ~20 | Jurys de soutenance |
| Coordonatrice | ~15 | Gestion coordination |
| Responsable Cursus | ~20 | Gestion cursus |
| Entreprise | ~25 | Entreprises partenaires |
| Ecole | ~15 | Écoles partenaires |
| Responsable Formation | ~15 | Gestion formation |
| **Security** | ~15 | Rate limiting, headers, validation |
| **Cache** | ~20 | LRU cache, TTL, décorateurs |
| **Performance** | ~24 | Pagination, streaming, monitoring |
| **Security Advanced** | ~29 | Brute force, audit, sanitization, JWT |

## 🔍 Cas de test importants

### Sécurité
- Validation JWT (création, expiration, révocation)
- Hashing de mots de passe (bcrypt)
- Rate limiting par IP
- Headers de sécurité (XSS, CSRF, Clickjacking)
- Protection brute force avec lockout progressif
- Détection XSS et NoSQL injection
- Sanitization des entrées
- Audit logging des actions sensibles

### Validation
- Payloads invalides
- Champs manquants
- Formats incorrects
- Emails invalides
- Injection NoSQL dans les requêtes
- Path traversal dans les chemins

### Gestion d'erreurs
- Ressources non trouvées (404)
- Base de données non initialisée (500)
- Mises à jour avec payload vide (400)
- IDs ObjectId invalides

### Workflows métier
- Création -> Lecture -> Mise à jour -> Suppression (CRUD)
- Cycle de vie entretien
- Association apprenti-tuteur-maître
- Gestion promotions

## 🐛 Debugging

### Afficher plus de détails
```bash
# Traceback complet
pytest --tb=long

# Afficher print statements
pytest -s

# Arrêter au premier échec
pytest -x

# Mode verbose maximum
pytest -vv
```

### Tester un cas spécifique
```bash
# Classe spécifique
pytest tests/test_auth_unit.py::TestPasswordHashing -v

# Fonction spécifique
pytest tests/test_auth_unit.py::TestPasswordHashing::test_hash_password -v

# Pattern de nom
pytest -k "password" -v
```

## 📝 Notes importantes

### ⚠️ Pas de modifications du code de production
Les tests sont conçus pour **NE PAS MODIFIER** les fonctionnalités existantes du site. Ils utilisent :
- Mocks pour les appels DB
- TestClient pour les routes API
- Fixtures isolées
- Pas d'effets de bord

### Base de données
Les tests n'interagissent pas avec une vraie base de données :
- Tous les appels MongoDB sont mockés
- Utilisation d'`AsyncMock` pour les opérations async
- Fixtures pour les données de test

### Async
Les fonctions async sont testées avec :
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result
```

## 🤝 Contribution

Pour ajouter de nouveaux tests :

1. **Ajouter les fixtures** dans `conftest.py` si nécessaire
2. **Créer le fichier de test** : `test_<module>.py`
3. **Suivre la structure** : 
   - Tests unitaires des fonctions
   - Tests d'intégration des routes
   - Tests de validation
4. **Utiliser les mocks** : Patcher `common.db.db`
5. **Tester les cas limites** : Erreurs, valeurs nulles, etc.

## 📚 Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## ✅ Checklist de qualité

- [x] Tests unitaires pour toutes les fonctions
- [x] Tests d'intégration pour toutes les routes
- [x] Tests de validation des payloads
- [x] Tests des cas d'erreur
- [x] Tests des cas limites
- [x] Couverture de tous les modules
- [x] Documentation complète
- [x] Configuration pytest
- [x] Fixtures réutilisables
- [x] Mocks appropriés
- [x] Tests de sécurité (rate limiting, headers)
- [x] Tests de cache (LRU, TTL, éviction)
- [x] Tests de performance (pagination, streaming)
- [x] Tests brute force protection
- [x] Tests sanitization (XSS, NoSQL injection)
- [x] Tests JWT avancé (refresh, révocation)
- [x] Tests audit logging

---

## 🔧 Modules Common - Structure

```
backend/common/
├── __init__.py              # Exports principaux
├── config.py                # Configuration centralisée
├── db.py                    # Connexion MongoDB
├── app_factory.py           # Factory FastAPI avec middlewares
│
├── security.py              # Rate limiting, headers sécurité
│   ├── InMemoryRateLimiter
│   ├── SecurityHeadersMiddleware
│   ├── RateLimitMiddleware
│   ├── RequestValidationMiddleware
│   └── RequestIDMiddleware
│
├── cache.py                 # Système de cache
│   ├── LRUCache
│   ├── CacheEntry
│   ├── @cached decorator
│   └── QueryCache
│
├── performance.py           # Optimisation
│   ├── PaginatedResult
│   ├── paginate_cursor()
│   ├── cursor_pagination()
│   ├── stream_documents()
│   ├── QueryOptimizer
│   └── PerformanceMetrics
│
├── brute_force.py           # Protection attaques
│   ├── BruteForceProtection
│   ├── AccountLockout
│   └── IPLockout
│
├── sanitization.py          # Validation entrées
│   ├── sanitize_string()
│   ├── sanitize_html()
│   ├── sanitize_for_mongodb()
│   ├── detect_xss()
│   ├── detect_nosql_injection()
│   ├── detect_path_traversal()
│   └── @validate_input decorator
│
├── jwt_manager.py           # Gestion JWT avancée
│   ├── TokenManager
│   ├── TokenPair
│   ├── TokenData
│   └── Token revocation
│
└── audit.py                 # Journalisation
    ├── AuditService
    ├── AuditEventType
    └── @audit_action decorator
```

---

**Créé pour le projet Alteris - ESGI**  
*Plateforme de gestion d'apprentissage*
