import React from "react";
import { useAuth } from "../auth/Permissions";
import type { UserSummary } from "../auth/Permissions";
import { AUTH_API_URL, ADMIN_API_URL, ENTREPRISE_API_URL, fetchJson } from "../config";

type EditableUser = UserSummary & {
  firstName?: string;
  lastName?: string;
  phone?: string;
};

type UsersResponse = {
  users: UserSummary[];
};

type Enterprise = {
  id: string;
  raisonSociale: string;
  siret?: string;
  adresse?: string;
  email?: string;
};

type EnterpriseListResponse = {
  entreprises: Array<{
    _id: string;
    raisonSociale?: string;
    siret?: string;
    adresse?: string;
    email?: string;
  }>;
};

type RoleOption = {
  value: string;
  label: string;
};

type CreateUserDraft = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  anneeAcademique: string;
  password: string;
  role: string;
  tutorId: string;
  masterId: string;
  enterpriseId: string;
};

type EnterpriseFormState = {
  id: string;
  raisonSociale: string;
  siret: string;
  adresse: string;
  email: string;
};

function normalizeRoleLabel(label?: string): string {
  return (label ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

const ROLE_OPTIONS: RoleOption[] = [
  { value: "apprenti", label: "Apprentie" },
  { value: "tuteur_pedagogique", label: "Tuteur pédagogique" },
  { value: "maitre_apprentissage", label: "Maître d'apprentissage" },
  { value: "coordinatrice", label: "Coordinatrice d'apprentissage" },
  { value: "entreprise", label: "Entreprise partenaire" },
  { value: "responsable_cursus", label: "Responsable du cursus" },
  { value: "jury", label: "Professeur jury ESEO" },
  { value: "admin", label: "Administrateur" },
];

const ROLE_VALUE_TO_OPTION = ROLE_OPTIONS.reduce<Record<string, RoleOption>>((acc, option) => {
  acc[option.value] = option;
  return acc;
}, {});

const ROLE_LABEL_TO_VALUE = ROLE_OPTIONS.reduce<Record<string, string>>((acc, option) => {
  const normalized = normalizeRoleLabel(option.label);
  acc[normalized] = option.value;
  return acc;
}, {});

const DEFAULT_ROLE_VALUE = ROLE_OPTIONS[0]?.value ?? "apprenti";

const createUserTemplate = (): CreateUserDraft => ({
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  anneeAcademique: "",
  password: "",
  role: DEFAULT_ROLE_VALUE,
  tutorId: "",
  masterId: "",
  enterpriseId: "",
});

const emptyEnterpriseForm: EnterpriseFormState = {
  id: "",
  raisonSociale: "",
  siret: "",
  adresse: "",
  email: "",
};

function inferRoleFromSummary(user: UserSummary): string | undefined {
  if (user.role) {
    return user.role;
  }

  const directMatch = ROLE_LABEL_TO_VALUE[normalizeRoleLabel(user.roleLabel)];
  if (directMatch) {
    return directMatch;
  }

  if (Array.isArray(user.roles)) {
    for (const candidate of user.roles) {
      const match = ROLE_LABEL_TO_VALUE[normalizeRoleLabel(candidate)];
      if (match) {
        return match;
      }
    }
  }

  return undefined;
}

function splitFullName(fullName?: string): { firstName?: string; lastName?: string } {
  if (!fullName) {
    return {};
  }
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 0) {
    return {};
  }
  const firstName = parts.shift() ?? "";
  const lastName = parts.join(" ");
  return {
    firstName,
    lastName: lastName || undefined,
  };
}

function buildUpdatePayloadFromDraft(draft: EditableUser, fallbackRole: string) {
  const payload: Record<string, unknown> = {};
  const assign = (key: string, value: unknown) => {
    if (value !== undefined) {
      payload[key] = value;
    }
  };

  assign("first_name", draft.firstName);
  assign("last_name", draft.lastName);
  assign("fullName", `${draft.firstName ?? ""} ${draft.lastName ?? ""}`.trim() || draft.fullName);
  assign("email", draft.email);
  assign("phone", draft.phone);
  assign("role", draft.role ?? fallbackRole);
  assign("roles", draft.roles);
  assign("roleLabel", draft.roleLabel);
  assign("perms", draft.perms);

  return payload;
}

const modalBackdropStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: "rgba(0, 0, 0, 0.45)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const modalContainerStyle: React.CSSProperties = {
  backgroundColor: "#fff",
  borderRadius: 8,
  boxShadow: "0 20px 45px rgba(15, 23, 42, 0.25)",
  maxWidth: 520,
  width: "100%",
  padding: "24px 28px",
};

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div style={modalBackdropStyle} role="dialog" aria-modal="true">
      <div style={modalContainerStyle}>
        <header style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>{title}</h2>
          <button
            onClick={onClose}
            style={{ border: "none", background: "transparent", fontSize: 18, cursor: "pointer" }}
            aria-label="Fermer"
          >
            ×
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

export default function Admin() {
  const { token } = useAuth();
  const [users, setUsers] = React.useState<EditableUser[]>([]);
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);
  const [editUser, setEditUser] = React.useState<EditableUser | null>(null);
  const [editDraft, setEditDraft] = React.useState<EditableUser | null>(null);
  const [deleteIds, setDeleteIds] = React.useState<string[]>([]);
  const [isFetching, setIsFetching] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  const [actionError, setActionError] = React.useState<string | null>(null);
  const [isSavingEdit, setIsSavingEdit] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [createDraft, setCreateDraft] = React.useState<CreateUserDraft>(() => createUserTemplate());
  const [isCreatingUser, setIsCreatingUser] = React.useState(false);
  const [enterprises, setEnterprises] = React.useState<Enterprise[]>([]);
  const [isLoadingEnterprises, setIsLoadingEnterprises] = React.useState(false);
  const [enterpriseError, setEnterpriseError] = React.useState<string | null>(null);
  const [enterpriseSuccess, setEnterpriseSuccess] = React.useState<string | null>(null);
  const [enterpriseForm, setEnterpriseForm] = React.useState<EnterpriseFormState>(emptyEnterpriseForm);
  const [isSavingEnterprise, setIsSavingEnterprise] = React.useState(false);
  const [editTutorId, setEditTutorId] = React.useState("");
  const [editMasterId, setEditMasterId] = React.useState("");
  const [editEnterpriseId, setEditEnterpriseId] = React.useState("");

  const mapUserToEditable = React.useCallback(
    (user: UserSummary): EditableUser => {
      const inferredRole = inferRoleFromSummary(user);
      const nameParts = splitFullName(user.fullName);
      return {
        ...user,
        role: user.role ?? inferredRole,
        firstName: user.firstName ?? nameParts.firstName,
        lastName: user.lastName ?? nameParts.lastName,
        phone: user.phone ?? "",
      };
    },
    []
  );

  const loadEnterprises = React.useCallback(async () => {
    if (!token) {
      setEnterprises([]);
      setEnterpriseError(null);
      return;
    }
    setIsLoadingEnterprises(true);
    setEnterpriseError(null);
    try {
      const payload = await fetchJson<EnterpriseListResponse>(`${ENTREPRISE_API_URL}/`, { token });
      const mapped =
        payload.entreprises
          ?.map((enterprise) => ({
            id: enterprise._id ?? "",
            raisonSociale: enterprise.raisonSociale ?? "Entreprise sans nom",
            siret: enterprise.siret ?? "",
            adresse: enterprise.adresse ?? "",
            email: enterprise.email ?? "",
          }))
          .filter((enterprise): enterprise is Enterprise => Boolean(enterprise.id)) ?? [];
      setEnterprises(mapped);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossible de charger les entreprises.";
      setEnterpriseError(message);
      setEnterprises([]);
    } finally {
      setIsLoadingEnterprises(false);
    }
  }, [token]);

  const refreshUsers = React.useCallback(async () => {
    if (!token) {
      setUsers([]);
      setSelectedIds([]);
      setFetchError("Authentification requise pour charger les utilisateurs.");
      setIsFetching(false);
      return;
    }

    setIsFetching(true);
    setFetchError(null);
    try {
      const payload = await fetchJson<UsersResponse>(`${AUTH_API_URL}/users`, { token });
      const nextUsers = payload.users.map(mapUserToEditable);
      setUsers(nextUsers);
      setSelectedIds((current) =>
        current.filter((id) => nextUsers.some((candidate) => candidate.id === id))
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossible de recuperer les utilisateurs.";
      setFetchError(message);
      setUsers([]);
      setSelectedIds([]);
    } finally {
      setIsFetching(false);
    }
  }, [token, mapUserToEditable]);

  React.useEffect(() => {
    refreshUsers();
  }, [refreshUsers]);

  React.useEffect(() => {
    loadEnterprises();
  }, [loadEnterprises]);

  React.useEffect(() => {
    setCreateDraft((current) => {
      if (!current.enterpriseId) return current;
      return enterprises.some((enterprise) => enterprise.id === current.enterpriseId)
        ? current
        : { ...current, enterpriseId: "" };
    });
  }, [enterprises]);

  React.useEffect(() => {
    if (!editEnterpriseId) return;
    if (!enterprises.some((enterprise) => enterprise.id === editEnterpriseId)) {
      setEditEnterpriseId("");
    }
  }, [enterprises, editEnterpriseId]);

  const tutors = React.useMemo(() => users.filter((user) => user.role === "tuteur_pedagogique"), [users]);
  const masters = React.useMemo(() => users.filter((user) => user.role === "maitre_apprentissage"), [users]);

  const isAllSelected = users.length > 0 && selectedIds.length === users.length;
  const hasSelection = selectedIds.length > 0;

  const toggleSelect = React.useCallback(
    (id: string) => {
      setSelectedIds((current) =>
        current.includes(id) ? current.filter((candidate) => candidate !== id) : [...current, id]
      );
    },
    [setSelectedIds]
  );

  const toggleSelectAll = React.useCallback(() => {
    setSelectedIds((current) => (current.length === users.length ? [] : users.map((user) => user.id)));
  }, [users]);

  const beginEdit = React.useCallback((user: EditableUser) => {
    const names = splitFullName(user.fullName);
    const fallbackRole = inferRoleFromSummary(user) ?? DEFAULT_ROLE_VALUE;
    const resolvedRole = user.role ?? fallbackRole;
    const resolvedRoleLabel = ROLE_VALUE_TO_OPTION[resolvedRole]?.label ?? user.roleLabel;
    setActionError(null);
    setEditUser(user);
    setEditDraft({
      ...user,
      role: resolvedRole,
      roleLabel: resolvedRoleLabel,
      roles: resolvedRoleLabel ? [resolvedRoleLabel] : user.roles,
      perms: [...user.perms],
      firstName: user.firstName ?? names.firstName ?? "",
      lastName: user.lastName ?? names.lastName ?? "",
      phone: user.phone ?? "",
    });
    const existingTutorId =
      (user as EditableUser & { tuteur?: { tuteur_id?: string } }).tuteur?.tuteur_id ?? "";
    const existingMasterId =
      (user as EditableUser & { maitre?: { maitre_id?: string } }).maitre?.maitre_id ?? "";
    const existingEnterpriseId = user.company?.entreprise_id ?? "";
    setEditTutorId(existingTutorId);
    setEditMasterId(existingMasterId);
    setEditEnterpriseId(existingEnterpriseId);
  }, []);

  const closeEditModal = React.useCallback(() => {
    setEditUser(null);
    setEditDraft(null);
    setEditTutorId("");
    setEditMasterId("");
    setEditEnterpriseId("");
  }, []);

  const handleEnterpriseFormChange = React.useCallback(
    (key: keyof EnterpriseFormState, value: string) => {
      setEnterpriseForm((current) => ({ ...current, [key]: value }));
      setEnterpriseError(null);
      setEnterpriseSuccess(null);
    },
    []
  );

  const handleEditEnterprise = React.useCallback((enterprise: Enterprise) => {
    setEnterpriseForm({
      id: enterprise.id,
      raisonSociale: enterprise.raisonSociale ?? "",
      siret: enterprise.siret ?? "",
      adresse: enterprise.adresse ?? "",
      email: enterprise.email ?? "",
    });
    setEnterpriseError(null);
    setEnterpriseSuccess(null);
  }, []);

  const cancelEnterpriseEdit = React.useCallback(() => {
    setEnterpriseForm(emptyEnterpriseForm);
    setEnterpriseError(null);
    setEnterpriseSuccess(null);
  }, []);

  const handleEnterpriseSubmit = React.useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!token) {
        setEnterpriseError("Authentification requise pour g�rer les entreprises.");
        return;
      }
      const raison = enterpriseForm.raisonSociale.trim();
      const siret = enterpriseForm.siret.trim();
      const email = enterpriseForm.email.trim();
      if (!raison || !siret || !email) {
        setEnterpriseError("Renseignez la raison sociale, le SIRET et l'email.");
        return;
      }
      setIsSavingEnterprise(true);
      setEnterpriseError(null);
      setEnterpriseSuccess(null);
      const isEditingEnterprise = Boolean(enterpriseForm.id);
      const body: Record<string, string> = {
        raisonSociale: raison,
        siret,
        email,
      };
      if (enterpriseForm.adresse.trim()) {
        body.adresse = enterpriseForm.adresse.trim();
      }
      const endpoint = isEditingEnterprise
        ? `${ENTREPRISE_API_URL}/${enterpriseForm.id}`
        : `${ENTREPRISE_API_URL}/`;
      const method = isEditingEnterprise ? "PUT" : "POST";
      try {
        await fetchJson(endpoint, {
          method,
          token,
          body: JSON.stringify(body),
        });
        setEnterpriseSuccess(
          isEditingEnterprise ? "Entreprise mise � jour." : "Entreprise ajout�e."
        );
        setEnterpriseForm(emptyEnterpriseForm);
        await loadEnterprises();
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Impossible d'enregistrer l'entreprise.";
        setEnterpriseError(message);
      } finally {
        setIsSavingEnterprise(false);
      }
    },
    [token, enterpriseForm, loadEnterprises]
  );

  const handleEditChange = React.useCallback(
    (key: keyof EditableUser, value: string) => {
      setEditDraft((current) => {
        if (!current) return current;
        if (key === "perms") {
          return { ...current, perms: value.split(",").map((item) => item.trim()).filter(Boolean) };
        }
        if (key === "role") {
          const option = ROLE_VALUE_TO_OPTION[value];
          if (value !== "apprenti") {
            setEditTutorId("");
            setEditMasterId("");
            setEditEnterpriseId("");
          }
          return {
            ...current,
            role: value,
            roleLabel: option?.label ?? current.roleLabel,
            roles: option ? [option.label] : current.roles,
          };
        }
        return { ...current, [key]: value };
      });
    },
    []
  );

  const saveEdit = React.useCallback(async () => {
    if (!editDraft || !editUser) return;
    if (!token) {
      setActionError("Authentification requise pour modifier un utilisateur.");
      return;
    }

    const roleForRoute = editUser.role ?? editDraft.role;
    if (!roleForRoute) {
      setActionError("Rôle introuvable pour cet utilisateur.");
      return;
    }

    setIsSavingEdit(true);
    setActionError(null);
    try {
      const body = buildUpdatePayloadFromDraft(editDraft, roleForRoute);
      await fetchJson(`${ADMIN_API_URL}/user/${roleForRoute}/${editDraft.id}`, {
        method: "PUT",
        token,
        body: JSON.stringify(body),
      });
      if (editDraft.role === "apprenti" && editDraft.id) {
        const associationCalls: Promise<unknown>[] = [];
        if (editTutorId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-tuteur`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: editDraft.id,
                tuteur_id: editTutorId,
              }),
            })
          );
        }
        if (editMasterId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-maitre`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: editDraft.id,
                maitre_id: editMasterId,
              }),
            })
          );
        }
        if (editEnterpriseId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-entreprise`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: editDraft.id,
                entreprise_id: editEnterpriseId,
              }),
            })
          );
        }
        if (associationCalls.length) {
          await Promise.all(associationCalls);
        }
      }
      closeEditModal();
      await refreshUsers();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "La modification a échoué.";
      setActionError(message);
    } finally {
      setIsSavingEdit(false);
    }
  }, [editDraft, editUser, token, closeEditModal, refreshUsers, editTutorId, editMasterId, editEnterpriseId]);

  const requestDelete = React.useCallback((ids: string[]) => {
    setActionError(null);
    setDeleteIds(ids);
  }, []);

  const closeDeleteModal = React.useCallback(() => {
    setDeleteIds([]);
  }, []);

  const confirmDelete = React.useCallback(async () => {
    if (deleteIds.length === 0) return;
    if (!token) {
      setActionError("Authentification requise pour supprimer un utilisateur.");
      return;
    }

    setIsDeleting(true);
    setActionError(null);
    try {
      await Promise.all(
        deleteIds.map(async (id) => {
          const target = users.find((candidate) => candidate.id === id);
          if (!target?.role) {
            throw new Error("Rôle introuvable pour un utilisateur sélectionné.");
          }
          await fetchJson(`${ADMIN_API_URL}/user/${target.role}/${id}`, {
            method: "DELETE",
            token,
          });
        })
      );
      closeDeleteModal();
      await refreshUsers();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "La suppression a échoué.";
      setActionError(message);
    } finally {
      setIsDeleting(false);
    }
  }, [deleteIds, token, users, closeDeleteModal, refreshUsers]);

  const openCreateModal = React.useCallback(() => {
    setCreateDraft(createUserTemplate());
    setIsCreateModalOpen(true);
    setActionError(null);
  }, []);

  const closeCreateModal = React.useCallback(() => {
    setIsCreateModalOpen(false);
  }, []);

  const handleCreateChange = React.useCallback((key: keyof CreateUserDraft, value: string) => {
    setCreateDraft((current) => {
      if (key === "role" && value !== "apprenti") {
        return {
          ...current,
          role: value,
          tutorId: "",
          masterId: "",
          enterpriseId: "",
        };
      }
      return { ...current, [key]: value };
    });
  }, []);

  const submitCreate = React.useCallback(async () => {
    if (!token) {
      setActionError("Authentification requise pour créer un utilisateur.");
      return;
    }

    setIsCreatingUser(true);
    setActionError(null);
    try {
      const created = await fetchJson<{ user_id?: string }>(`${AUTH_API_URL}/register`, {
        method: "POST",
        token,
        body: JSON.stringify({
          first_name: createDraft.firstName,
          last_name: createDraft.lastName,
          email: createDraft.email,
          phone: createDraft.phone,
          annee_academique: createDraft.anneeAcademique,
          password: createDraft.password,
          role: createDraft.role,
        }),
      });
      const newUserId = created?.user_id;
      if (createDraft.role === "apprenti" && newUserId) {
        const associationCalls: Promise<unknown>[] = [];
        if (createDraft.tutorId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-tuteur`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: newUserId,
                tuteur_id: createDraft.tutorId,
              }),
            })
          );
        }
        if (createDraft.masterId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-maitre`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: newUserId,
                maitre_id: createDraft.masterId,
              }),
            })
          );
        }
        if (createDraft.enterpriseId) {
          associationCalls.push(
            fetchJson(`${ADMIN_API_URL}/associer-entreprise`, {
              method: "POST",
              token,
              body: JSON.stringify({
                apprenti_id: newUserId,
                entreprise_id: createDraft.enterpriseId,
              }),
            })
          );
        }
        if (associationCalls.length) {
          await Promise.all(associationCalls);
        }
      }
      closeCreateModal();
      await refreshUsers();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "La création a échoué.";
      setActionError(message);
    } finally {
      setIsCreatingUser(false);
    }
  }, [token, createDraft, closeCreateModal, refreshUsers]);

  const renderPerms = (perms: string[]) => perms.join(", ");

  return (
    <div style={{ padding: "32px 40px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, margin: 0 }}>Administration</h1>
        <button
          onClick={openCreateModal}
          style={{
            padding: "10px 18px",
            borderRadius: 6,
            border: "1px solid #16a34a",
            background: "#16a34a",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Ajouter un utilisateur
        </button>
      </div>

      {fetchError ? (
        <div
          style={{
            marginBottom: 16,
            padding: "12px 16px",
            borderRadius: 8,
            background: "#fee2e2",
            color: "#b91c1c",
          }}
        >
          {fetchError}
        </div>
      ) : null}

      {actionError ? (
        <div
          style={{
            marginBottom: 16,
            padding: "12px 16px",
            borderRadius: 8,
            background: "#fef3c7",
            color: "#b45309",
          }}
        >
          {actionError}
        </div>
      ) : null}

      {isFetching ? (
        <div style={{ marginBottom: 16, color: "#2563eb" }}>
          Chargement des utilisateurs...
        </div>
      ) : null}

      <section
        style={{
          marginBottom: 24,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 16,
        }}
      >
        <div
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 16,
            background: "#fff",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>Gestion des entreprises partenaires</h2>
          <p style={{ margin: 0, color: "#475569" }}>Ajoutez une entreprise pour l'associer aux apprentis.</p>
          <form onSubmit={handleEnterpriseSubmit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Raison sociale</span>
              <input
                type="text"
                value={enterpriseForm.raisonSociale}
                onChange={(event) => handleEnterpriseFormChange("raisonSociale", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>SIRET</span>
              <input
                type="text"
                value={enterpriseForm.siret}
                onChange={(event) => handleEnterpriseFormChange("siret", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Email de contact</span>
              <input
                type="email"
                value={enterpriseForm.email}
                onChange={(event) => handleEnterpriseFormChange("email", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Adresse</span>
              <input
                type="text"
                value={enterpriseForm.adresse}
                onChange={(event) => handleEnterpriseFormChange("adresse", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
              />
            </label>
            {enterpriseError && <p className="form-error">{enterpriseError}</p>}
            {enterpriseSuccess && (
              <p style={{ color: "#15803d", fontSize: 13, margin: 0 }}>{enterpriseSuccess}</p>
            )}
            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              {enterpriseForm.id && (
                <button
                  type="button"
                  onClick={cancelEnterpriseEdit}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 6,
                    border: "1px solid #cbd5f5",
                    background: "#fff",
                    cursor: "pointer",
                  }}
                >
                  Annuler
                </button>
              )}
              <button
                type="submit"
                disabled={isSavingEnterprise}
                style={{
                  padding: "8px 14px",
                  borderRadius: 6,
                  border: "1px solid #0ea5e9",
                  background: isSavingEnterprise ? "#bae6fd" : "#0ea5e9",
                  color: "#fff",
                  cursor: isSavingEnterprise ? "wait" : "pointer",
                }}
              >
                {isSavingEnterprise
                  ? "Enregistrement..."
                  : enterpriseForm.id
                  ? "Mettre a jour"
                  : "Ajouter l'entreprise"}
              </button>
            </div>
          </form>
        </div>
        <div
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 16,
            background: "#fff",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <h3 style={{ margin: 0, fontSize: 16 }}>Entreprises enregistrees</h3>
          {isLoadingEnterprises ? (
            <p>Chargement des entreprises...</p>
          ) : enterprises.length === 0 ? (
            <p style={{ margin: 0, color: "#475569" }}>
              {enterpriseError ?? "Aucune entreprise enregistree pour le moment."}
            </p>
          ) : (
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {enterprises.map((enterprise) => (
                <li
                  key={enterprise.id}
                  style={{
                    border: "1px solid #e2e8f0",
                    borderRadius: 10,
                    padding: 12,
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    alignItems: "center",
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <strong>{enterprise.raisonSociale}</strong>
                    <span style={{ color: "#475569", fontSize: 13 }}>
                      SIRET : {enterprise.siret || "Non renseigne"}
                    </span>
                    {enterprise.adresse && (
                      <span style={{ color: "#475569", fontSize: 13 }}>{enterprise.adresse}</span>
                    )}
                    {enterprise.email && (
                      <span style={{ color: "#475569", fontSize: 13 }}>{enterprise.email}</span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleEditEnterprise(enterprise)}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 6,
                      border: "1px solid #2563eb",
                      background: "#2563eb",
                      color: "#fff",
                      cursor: "pointer",
                    }}
                  >
                    Modifier
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section style={{ marginBottom: 16, display: "flex", gap: 12 }}>
        <button
          onClick={() => requestDelete(selectedIds)}
          disabled={selectedIds.length === 0}
          style={{
            padding: "10px 16px",
            borderRadius: 6,
            border: "1px solid #e11d48",
            background: selectedIds.length === 0 ? "#fde7ee" : "#f43f5e",
            color: selectedIds.length === 0 ? "#9f1239" : "#fff",
            cursor: selectedIds.length === 0 ? "not-allowed" : "pointer",
          }}
        >
          Supprimer la sélection
        </button>
      </section>

      <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid #e2e8f0" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ backgroundColor: "#f8fafc", textAlign: "left" }}>
            <tr>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={toggleSelectAll}
                  aria-label="Tout sélectionner"
                />
              </th>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>ID</th>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>Nom complet</th>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>Email</th>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>Rôle</th>
              <th style={{ padding: "12px 16px", borderBottom: "1px solid #e2e8f0" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "12px 16px" }}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(user.id)}
                    onChange={() => toggleSelect(user.id)}
                    aria-label={`Sélectionner ${user.fullName}`}
                  />
                </td>
                <td style={{ padding: "12px 16px", fontWeight: 500 }}>{user.id}</td>
                <td style={{ padding: "12px 16px" }}>{user.fullName}</td>
                <td style={{ padding: "12px 16px" }}>{user.email}</td>
                <td style={{ padding: "12px 16px" }}>{user.roleLabel}</td>
                <td style={{ padding: "12px 16px", display: "flex", gap: 8 }}>
                  <button
                    onClick={() => beginEdit(user)}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 6,
                      border: "1px solid #2563eb",
                      background: "#2563eb",
                      color: "#fff",
                      cursor: "pointer",
                    }}
                  >
                    Modifier
                  </button>
                  <button
                    onClick={() => requestDelete([user.id])}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 6,
                      border: "1px solid #dc2626",
                      background: "#fff",
                      color: "#dc2626",
                      cursor: "pointer",
                    }}
                  >
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={7} style={{ padding: "24px 16px", textAlign: "center", color: "#64748b" }}>
                  Aucun utilisateur à afficher.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isCreateModalOpen && (
        <Modal title="Ajouter un utilisateur" onClose={closeCreateModal}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              submitCreate();
            }}
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            <div style={{ display: "flex", gap: 12 }}>
              <label style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Prénom</span>
                <input
                  type="text"
                  value={createDraft.firstName}
                  onChange={(event) => handleCreateChange("firstName", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
              <label style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Nom</span>
                <input
                  type="text"
                  value={createDraft.lastName}
                  onChange={(event) => handleCreateChange("lastName", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
            </div>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Email</span>
              <input
                type="email"
                value={createDraft.email}
                onChange={(event) => handleCreateChange("email", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Téléphone</span>
              <input
                type="tel"
                value={createDraft.phone}
                onChange={(event) => handleCreateChange("phone", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Année académique</span>
              <input
                type="text"
                value={createDraft.anneeAcademique}
                onChange={(event) => handleCreateChange("anneeAcademique", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Mot de passe</span>
              <input
                type="password"
                value={createDraft.password}
                onChange={(event) => handleCreateChange("password", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Rôle</span>
              <select
                value={createDraft.role}
                onChange={(event) => handleCreateChange("role", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
              >
                {ROLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {createDraft.role === "apprenti" && (
              <>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Tuteur pédagogique</span>
                  <select
                    value={createDraft.tutorId}
                    onChange={(event) => handleCreateChange("tutorId", event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucun tuteur</option>
                    {tutors.map((tutor) => (
                      <option key={tutor.id} value={tutor.id}>
                        {tutor.fullName} — {tutor.email}
                      </option>
                    ))}
                  </select>
                  {tutors.length === 0 && (
                    <small style={{ color: "#b45309" }}>Aucun tuteur disponible pour le moment.</small>
                  )}
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Maître d'apprentissage</span>
                  <select
                    value={createDraft.masterId}
                    onChange={(event) => handleCreateChange("masterId", event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucun maître</option>
                    {masters.map((master) => (
                      <option key={master.id} value={master.id}>
                        {master.fullName} — {master.email}
                      </option>
                    ))}
                  </select>
                  {masters.length === 0 && (
                    <small style={{ color: "#b45309" }}>Aucun maître disponible pour le moment.</small>
                  )}
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Entreprise partenaire</span>
                  <select
                    value={createDraft.enterpriseId}
                    onChange={(event) => handleCreateChange("enterpriseId", event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucune entreprise</option>
                    {enterprises.map((enterprise) => (
                      <option key={enterprise.id} value={enterprise.id}>
                        {enterprise.raisonSociale}
                        {enterprise.email ? ` - ${enterprise.email}` : ""}
                      </option>
                    ))}
                  </select>
                  {enterprises.length === 0 && (
                    <small style={{ color: "#b45309" }}>
                      Ajoutez une entreprise pour pouvoir l'associer.
                    </small>
                  )}
                </label>
              </>
            )}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
              <button
                type="button"
                onClick={closeCreateModal}
                style={{
                  padding: "10px 16px",
                  borderRadius: 6,
                  border: "1px solid #cbd5f5",
                  background: "#fff",
                  cursor: "pointer",
                }}
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={isCreatingUser}
                style={{
                  padding: "10px 16px",
                  borderRadius: 6,
                  border: "1px solid #16a34a",
                  background: isCreatingUser ? "#86efac" : "#16a34a",
                  color: "#fff",
                  cursor: isCreatingUser ? "wait" : "pointer",
                }}
              >
                {isCreatingUser ? "Création..." : "Créer"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {editUser && editDraft && (
        <Modal title={`Modifier ${editUser.fullName}`} onClose={closeEditModal}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              saveEdit();
            }}
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            <div style={{ display: "flex", gap: 12 }}>
              <label style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Prénom</span>
                <input
                  type="text"
                  value={editDraft.firstName ?? ""}
                  onChange={(event) => handleEditChange("firstName", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
              <label style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Nom</span>
                <input
                  type="text"
                  value={editDraft.lastName ?? ""}
                  onChange={(event) => handleEditChange("lastName", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
            </div>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Email</span>
              <input
                type="email"
                value={editDraft.email}
                onChange={(event) => handleEditChange("email", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Téléphone</span>
              <input
                type="tel"
                value={editDraft.phone ?? ""}
                onChange={(event) => handleEditChange("phone", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span>Rôle</span>
              <select
                value={editDraft.role ?? ""}
                onChange={(event) => handleEditChange("role", event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
              >
                {ROLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {editDraft.role === "apprenti" && (
              <>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Tuteur pédagogique</span>
                  <select
                    value={editTutorId}
                    onChange={(event) => setEditTutorId(event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucun tuteur</option>
                    {tutors.map((tutor) => (
                      <option key={tutor.id} value={tutor.id}>
                        {tutor.fullName} — {tutor.email}
                      </option>
                    ))}
                  </select>
                  {tutors.length === 0 && (
                    <small style={{ color: "#b45309" }}>Aucun tuteur disponible pour le moment.</small>
                  )}
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Maître d'apprentissage</span>
                  <select
                    value={editMasterId}
                    onChange={(event) => setEditMasterId(event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucun maître</option>
                    {masters.map((master) => (
                      <option key={master.id} value={master.id}>
                        {master.fullName} — {master.email}
                      </option>
                    ))}
                  </select>
                  {masters.length === 0 && (
                    <small style={{ color: "#b45309" }}>Aucun maître disponible pour le moment.</small>
                  )}
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span>Entreprise partenaire</span>
                  <select
                    value={editEnterpriseId}
                    onChange={(event) => setEditEnterpriseId(event.target.value)}
                    style={{ padding: "10px 12px", borderRadius: 6, border: "1px solid #cbd5f5" }}
                  >
                    <option value="">Aucune entreprise</option>
                    {enterprises.map((enterprise) => (
                      <option key={enterprise.id} value={enterprise.id}>
                        {enterprise.raisonSociale}
                        {enterprise.email ? ` - ${enterprise.email}` : ""}
                      </option>
                    ))}
                  </select>
                  {enterprises.length === 0 && (
                    <small style={{ color: "#b45309" }}>
                      Ajoutez une entreprise pour pouvoir l'associer.
                    </small>
                  )}
                </label>
              </>
            )}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
              <button
                type="button"
                onClick={closeEditModal}
                style={{
                  padding: "10px 16px",
                  borderRadius: 6,
                  border: "1px solid #cbd5f5",
                  background: "#fff",
                  cursor: "pointer",
                }}
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={isSavingEdit}
                style={{
                  padding: "10px 16px",
                  borderRadius: 6,
                  border: "1px solid #2563eb",
                  background: isSavingEdit ? "#93c5fd" : "#2563eb",
                  color: "#fff",
                  cursor: isSavingEdit ? "wait" : "pointer",
                }}
              >
                {isSavingEdit ? "Enregistrement..." : "Enregistrer"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {deleteIds.length > 0 && (
        <Modal
          title={
            deleteIds.length === 1
              ? "Confirmer la suppression"
              : `Confirmer la suppression de ${deleteIds.length} utilisateurs`
          }
          onClose={closeDeleteModal}
        >
          <p style={{ marginBottom: 24, lineHeight: 1.5 }}>
            Êtes-vous sûr de vouloir supprimer{" "}
            {deleteIds.length === 1 ? "cet utilisateur" : "ces utilisateurs sélectionnés"} ? Cette action est
            irréversible.
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
            <button
              type="button"
              onClick={closeDeleteModal}
              style={{
                padding: "10px 16px",
                borderRadius: 6,
                border: "1px solid #cbd5f5",
                background: "#fff",
                cursor: "pointer",
              }}
            >
              Annuler
            </button>
            <button
              type="button"
              onClick={confirmDelete}
              disabled={isDeleting}
              style={{
                padding: "10px 16px",
                borderRadius: 6,
                border: "1px solid #dc2626",
                background: isDeleting ? "#fca5a5" : "#dc2626",
                color: "#fff",
                cursor: isDeleting ? "wait" : "pointer",
              }}
            >
              {isDeleting ? "Suppression..." : "Supprimer"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

