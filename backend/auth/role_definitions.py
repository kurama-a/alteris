"""
Role metadata shared by the Auth service.

Each entry describes how a given role should be exposed to the frontend
regarding labels and permissions.
"""

from __future__ import annotations

from typing import Dict, List, TypedDict


class RoleDefinition(TypedDict, total=False):
    roles: List[str]
    role_label: str
    perms: List[str]


ROLE_DEFINITIONS: Dict[str, RoleDefinition] = {
    "apprenti": {
        "roles": ["Apprentis"],
        "role_label": "Apprenti",
        "perms": [
            "journal:read:own",
            "journal:create:own",
            "doc:read",
            "doc:create",
            "meeting:schedule:own",
            "jury:read",
        ],
    },
    "apprentie": {
        "roles": ["Apprentis"],
        "role_label": "Apprenti",
        "perms": [
            "journal:read:own",
            "journal:create:own",
            "doc:read",
            "doc:create",
            "meeting:schedule:own",
            "jury:read",
        ],
    },
    "alternant": {
        "roles": ["Apprentis"],
        "role_label": "Apprenti",
        "perms": [
            "journal:read:own",
            "journal:create:own",
            "doc:read",
            "doc:create",
            "meeting:schedule:own",
            "jury:read",
        ],
    },
    "tuteur_pedagogique": {
        "roles": ["Tuteur pédagogique"],
        "role_label": "Tuteur pédagogique",
        "perms": [
            "journal:read:all",
            "doc:read",
            "meeting:participate",
            "jury:read",
        ],
    },
    "maitre_apprentissage": {
        "roles": ["Maître d'apprentissage"],
        "role_label": "Maître d'apprentissage",
        "perms": [
            "journal:read:assigned",
            "doc:read",
            "meeting:schedule:team",
        ],
    },
    "coordinatrice": {
        "roles": ["Coordinatrice d'apprentissage"],
        "role_label": "Coordinatrice d'apprentissage",
        "perms": [
            "journal:read:all",
            "doc:read",
            "promotion:manage",
            "meeting:participate",
            "user:manage",
            "jury:read",
        ],
    },
    "entreprise": {
        "roles": ["Entreprise partenaire"],
        "role_label": "Entreprise partenaire",
        "perms": [
            "journal:read:assigned",
            "doc:read",
            "doc:create",
        ],
    },
    "responsable_cursus": {
        "roles": ["Responsable du cursus"],
        "role_label": "Responsable du cursus",
        "perms": [
            "promotion:manage",
            "journal:read:all",
            "doc:read",
            "jury:read",
            "user:manage",
            "meeting:participate",
        ],
    },
    "jury": {
        "roles": ["Professeur ESEO"],
        "role_label": "Professeur jury ESEO",
        "perms": [
            "jury:read",
            "journal:read:all",
        ],
    },
    "professeur": {
        "roles": ["Professeur ESEO"],
        "role_label": "Professeur jury ESEO",
        "perms": [
            "jury:read",
        ],
    },
    "intervenant": {
        "roles": ["Intervenant"],
        "role_label": "Intervenant professionnel",
        "perms": [
            "jury:read",
        ],
    },
    "administrateur": {
        "roles": ["Administrateur de la plateforme"],
        "role_label": "Administrateur",
        "perms": [
            "user:manage",
            "doc:read",
            "promotion:manage",
            "journal:read:all",
            "jury:read",
        ],
    },
}


def get_role_definition(role: str) -> RoleDefinition:
    """
    Retrieve the metadata associated with a role.
    Falls back to a generic representation if the role is unknown.
    """
    normalized = role.lower()
    if normalized not in ROLE_DEFINITIONS:
        label = normalized.replace("_", " ").title()
        return RoleDefinition(
            roles=[label],
            role_label=label,
            perms=[],
        )
    return ROLE_DEFINITIONS[normalized]
