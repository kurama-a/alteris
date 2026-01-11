"""
Module de sanitisation et validation des entrées utilisateur.
Protection contre les injections et données malveillantes.
"""
import re
import html
import unicodedata
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import logging

logger = logging.getLogger("sanitization")


# =====================
# Patterns dangereux
# =====================

# Patterns d'injection NoSQL MongoDB
NOSQL_INJECTION_PATTERNS = [
    r'\$where',
    r'\$regex',
    r'\$ne',
    r'\$gt',
    r'\$lt',
    r'\$gte',
    r'\$lte',
    r'\$in',
    r'\$nin',
    r'\$or',
    r'\$and',
    r'\$not',
    r'\$exists',
    r'\$type',
    r'\$expr',
    r'\$jsonSchema',
    r'\$mod',
    r'\$text',
    r'\$geoWithin',
]

# Patterns XSS
XSS_PATTERNS = [
    r'<script[^>]*>',
    r'</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'data:text/html',
    r'vbscript:',
    r'expression\s*\(',
]

# Patterns d'injection de commandes
COMMAND_INJECTION_PATTERNS = [
    r';\s*rm\s+',
    r';\s*cat\s+',
    r';\s*wget\s+',
    r';\s*curl\s+',
    r'\|\s*sh',
    r'\|\s*bash',
    r'`[^`]+`',
    r'\$\([^)]+\)',
]

# Patterns de path traversal
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.',
    r'%2e%2e',
    r'%252e%252e',
    r'\.%2e',
    r'%2e\.',
]


# =====================
# Fonctions de sanitisation
# =====================

def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitise une chaîne de caractères.
    - Échappe les caractères HTML
    - Normalise les caractères Unicode
    - Supprime les caractères de contrôle
    - Trim les espaces
    """
    if not isinstance(value, str):
        return str(value)
    
    # Normaliser Unicode (NFKC)
    value = unicodedata.normalize('NFKC', value)
    
    # Supprimer les caractères de contrôle (sauf newlines et tabs)
    value = ''.join(
        char for char in value
        if unicodedata.category(char) != 'Cc' or char in '\n\r\t'
    )
    
    # Trim
    value = value.strip()
    
    # Limiter la longueur
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_html(value: str) -> str:
    """
    Sanitise une chaîne en échappant le HTML.
    Utiliser pour les données qui seront affichées dans du HTML.
    """
    if not isinstance(value, str):
        return str(value)
    
    return html.escape(value, quote=True)


def sanitize_for_mongodb(value: Any) -> Any:
    """
    Sanitise une valeur pour l'utilisation dans MongoDB.
    Prévient les injections NoSQL.
    """
    if isinstance(value, str):
        # Vérifier les patterns d'injection
        for pattern in NOSQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Tentative d'injection NoSQL détectée: {pattern}")
                # Échapper le $ pour neutraliser l'opérateur
                value = value.replace('$', '＄')  # Remplace par fullwidth dollar sign
        return value
    
    elif isinstance(value, dict):
        # Vérifier les clés commençant par $
        sanitized = {}
        for key, val in value.items():
            if key.startswith('$'):
                logger.warning(f"Clé MongoDB suspecte détectée: {key}")
                continue  # Ignorer les clés commençant par $
            sanitized[key] = sanitize_for_mongodb(val)
        return sanitized
    
    elif isinstance(value, list):
        return [sanitize_for_mongodb(item) for item in value]
    
    return value


def sanitize_email(email: str) -> str:
    """Sanitise et normalise une adresse email."""
    if not isinstance(email, str):
        return ""
    
    email = email.strip().lower()
    
    # Supprimer les caractères non autorisés
    email = re.sub(r'[^\w.@+-]', '', email)
    
    return email


def sanitize_filename(filename: str) -> str:
    """
    Sanitise un nom de fichier.
    Supprime les caractères dangereux et prévient le path traversal.
    """
    if not isinstance(filename, str):
        return "unnamed"
    
    # Supprimer les path traversal
    filename = filename.replace('..', '')
    filename = filename.replace('/', '')
    filename = filename.replace('\\', '')
    
    # Supprimer les caractères dangereux
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    
    # Limiter la longueur
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename or "unnamed"


def sanitize_phone(phone: str) -> str:
    """Sanitise un numéro de téléphone (garde uniquement les chiffres et +)."""
    if not isinstance(phone, str):
        return ""
    
    # Garder uniquement les chiffres, + et espaces
    phone = re.sub(r'[^\d+\s-]', '', phone)
    
    return phone.strip()


def sanitize_dict(
    data: Dict[str, Any],
    allowed_fields: Optional[List[str]] = None,
    max_string_length: int = 10000
) -> Dict[str, Any]:
    """
    Sanitise un dictionnaire complet.
    
    Args:
        data: Dictionnaire à sanitiser
        allowed_fields: Liste des champs autorisés (None = tous)
        max_string_length: Longueur max des chaînes
    """
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    
    for key, value in data.items():
        # Filtrer les champs si whitelist fournie
        if allowed_fields and key not in allowed_fields:
            continue
        
        # Sanitiser la clé
        key = sanitize_string(str(key), max_length=100)
        
        # Sanitiser la valeur selon son type
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value, max_length=max_string_length)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_string_length=max_string_length)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(v, max_string_length) if isinstance(v, str)
                else sanitize_dict(v, max_string_length=max_string_length) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


# =====================
# Détection de contenu malveillant
# =====================

def detect_xss(value: str) -> bool:
    """Détecte les tentatives XSS."""
    if not isinstance(value, str):
        return False
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False


def detect_nosql_injection(value: Any) -> bool:
    """Détecte les tentatives d'injection NoSQL."""
    if isinstance(value, str):
        for pattern in NOSQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
    
    elif isinstance(value, dict):
        for key in value.keys():
            if key.startswith('$'):
                return True
        for val in value.values():
            if detect_nosql_injection(val):
                return True
    
    elif isinstance(value, list):
        for item in value:
            if detect_nosql_injection(item):
                return True
    
    return False


def detect_command_injection(value: str) -> bool:
    """Détecte les tentatives d'injection de commandes."""
    if not isinstance(value, str):
        return False
    
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False


def detect_path_traversal(value: str) -> bool:
    """Détecte les tentatives de path traversal."""
    if not isinstance(value, str):
        return False
    
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False


def is_safe_input(value: Any) -> tuple[bool, Optional[str]]:
    """
    Vérifie si une entrée est sûre.
    Retourne (is_safe, threat_type).
    """
    if isinstance(value, str):
        if detect_xss(value):
            return False, "xss"
        if detect_nosql_injection(value):
            return False, "nosql_injection"
        if detect_command_injection(value):
            return False, "command_injection"
        if detect_path_traversal(value):
            return False, "path_traversal"
    
    elif isinstance(value, dict):
        if detect_nosql_injection(value):
            return False, "nosql_injection"
        for val in value.values():
            is_safe, threat = is_safe_input(val)
            if not is_safe:
                return False, threat
    
    elif isinstance(value, list):
        for item in value:
            is_safe, threat = is_safe_input(item)
            if not is_safe:
                return False, threat
    
    return True, None


# =====================
# Décorateur de validation
# =====================

def validate_input(*field_names: str, max_length: int = 10000):
    """
    Décorateur pour valider automatiquement les entrées.
    
    Usage:
        @validate_input("email", "name")
        async def create_user(email: str, name: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for field_name in field_names:
                if field_name in kwargs:
                    value = kwargs[field_name]
                    
                    is_safe, threat = is_safe_input(value)
                    if not is_safe:
                        logger.warning(f"Entrée malveillante détectée dans {field_name}: {threat}")
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Données d'entrée invalides"
                        )
                    
                    # Sanitiser
                    if isinstance(value, str):
                        kwargs[field_name] = sanitize_string(value, max_length)
                    elif isinstance(value, dict):
                        kwargs[field_name] = sanitize_dict(value, max_string_length=max_length)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =====================
# Validation de types spécifiques
# =====================

def validate_object_id(value: str) -> bool:
    """Valide un ObjectId MongoDB."""
    if not isinstance(value, str):
        return False
    
    # ObjectId = 24 caractères hexadécimaux
    return bool(re.match(r'^[a-fA-F0-9]{24}$', value))


def validate_uuid(value: str) -> bool:
    """Valide un UUID."""
    if not isinstance(value, str):
        return False
    
    uuid_pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
    return bool(re.match(uuid_pattern, value))


def validate_date_string(value: str, format: str = "%Y-%m-%d") -> bool:
    """Valide une date au format string."""
    if not isinstance(value, str):
        return False
    
    from datetime import datetime
    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
        return False


def validate_url(value: str, allowed_schemes: List[str] = None) -> bool:
    """Valide une URL."""
    if not isinstance(value, str):
        return False
    
    allowed_schemes = allowed_schemes or ['http', 'https']
    
    url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, value, re.IGNORECASE):
        return False
    
    # Vérifier le scheme
    scheme = value.split('://')[0].lower()
    return scheme in allowed_schemes
