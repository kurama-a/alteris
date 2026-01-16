import React from "react";
import { ADMIN_API_URL, APPRENTI_API_URL, JURY_API_URL } from "../config";
import { useAuth } from "../auth/Permissions";
import { fetchApprenticeDocuments } from "../api/documents";
import { fetchJson } from "../config";

type ApprenticeOption = {
  id: string;
  fullName: string;
  email: string;
};

type AdminApprentisResponse = {
  apprentis: ApprenticeOption[];
};

type AdminPromotion = {
  id: string;
  semesters?: Array<{
    semester_id?: string;
    id?: string;
    start_date?: string | null;
    end_date?: string | null;
  }>;
};

type PromotionListResponse = {
  promotions: AdminPromotion[];
};

type EntretienRecord = {
  entretien_id: string;
  date: string;
  sujet: string;
  semester_id?: string;
};

type ApprentiInfosResponse = {
  data: {
    entretiens?: EntretienRecord[];
  };
};

type JuryRecord = {
  id: string;
  date: string;
  promotion_reference?: {
    promotion_id: string;
    semester_id: string;
    semester_name?: string;
  };
  members: {
    apprenti: { user_id: string };
    tuteur: { user_id: string };
    professeur: { user_id: string };
    intervenant: { user_id: string };
  };
};

export type NotificationType = "document" | "deadline" | "overdue" | "entretien" | "jury";

export type NotificationItem = {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  date: string;
  apprenticeId: string;
  apprenticeName: string;
};

const GLOBAL_NOTIFICATION_ROLES = new Set([
  "admin",
  "administrateur",
  "coordinatrice",
  "responsable_cursus",
]);

const UPCOMING_WINDOW_DAYS = 14;
const OVERDUE_WINDOW_DAYS = 30;
const DOC_WINDOW_DAYS = 30;

const parseDateOnly = (value?: string | null) => {
  if (!value) return null;
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const [_, year, month, day] = match;
  return new Date(Number(year), Number(month) - 1, Number(day), 0, 0, 0, 0);
};

const daysBetween = (a: Date, b: Date) => {
  const diff = b.getTime() - a.getTime();
  return Math.floor(diff / (1000 * 60 * 60 * 24));
};

const isDateWithin = (dateValue: Date, start?: Date | null, end?: Date | null) => {
  if (!start || !end) return true;
  return dateValue >= start && dateValue <= end;
};

export function useNotifications() {
  const { me, token } = useAuth();
  const [items, setItems] = React.useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const normalizedRoles = React.useMemo(() => {
    const set = new Set<string>();
    if (typeof me.role === "string" && me.role.trim()) {
      set.add(me.role.toLowerCase());
    }
    (me.roles ?? []).forEach((role) => {
      if (typeof role === "string" && role.trim()) {
        set.add(role.toLowerCase());
      }
    });
    return set;
  }, [me.role, me.roles]);

  const isApprentice = Array.from(normalizedRoles).some((role) => role.includes("apprenti"));
  const canBrowseAll = Array.from(normalizedRoles).some((role) =>
    GLOBAL_NOTIFICATION_ROLES.has(role)
  );

  const [apprentices, setApprentices] = React.useState<ApprenticeOption[]>([]);

  React.useEffect(() => {
    if (!token) {
      setApprentices([]);
      return;
    }

    const base: ApprenticeOption[] = [];
    if (isApprentice) {
      base.push({ id: me.id, fullName: me.fullName, email: me.email });
    }
    if (Array.isArray(me.apprentices)) {
      me.apprentices.forEach((apprentice) => {
        base.push({
          id: apprentice.id,
          fullName: apprentice.fullName,
          email: apprentice.email,
        });
      });
    }

    if (!canBrowseAll) {
      const map = new Map<string, ApprenticeOption>();
      base.forEach((apprentice) => map.set(apprentice.id, apprentice));
      setApprentices(Array.from(map.values()));
      return;
    }

    let cancelled = false;
    fetchJson<AdminApprentisResponse>(`${ADMIN_API_URL}/apprentis`, { token })
      .then((payload) => {
        if (cancelled) return;
        const global =
          payload.apprentis?.map((apprentice) => ({
            id: apprentice.id,
            fullName: apprentice.fullName || apprentice.email || "Apprenti",
            email: apprentice.email,
          })) ?? [];
        const map = new Map<string, ApprenticeOption>();
        base.forEach((apprentice) => map.set(apprentice.id, apprentice));
        global.forEach((apprentice) => map.set(apprentice.id, apprentice));
        setApprentices(Array.from(map.values()));
      })
      .catch(() => {
        if (cancelled) return;
        const map = new Map<string, ApprenticeOption>();
        base.forEach((apprentice) => map.set(apprentice.id, apprentice));
        setApprentices(Array.from(map.values()));
      });

    return () => {
      cancelled = true;
    };
  }, [canBrowseAll, isApprentice, me.apprentices, me.email, me.fullName, me.id, token]);

  React.useEffect(() => {
    if (!token || apprentices.length === 0) {
      setItems([]);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const now = new Date();
    const nowStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);

    const loadNotifications = async () => {
      let promotionMap = new Map<string, AdminPromotion>();
      try {
        const promotions = await fetchJson<PromotionListResponse>(`${ADMIN_API_URL}/promos`, {
          token,
        });
        promotionMap = new Map<string, AdminPromotion>();
        promotions.promotions?.forEach((promotion) => {
          promotionMap.set(promotion.id, promotion);
        });
      } catch {
        promotionMap = new Map<string, AdminPromotion>();
      }

      let juries: JuryRecord[] = [];
      try {
        juries = await fetchJson<JuryRecord[]>(`${JURY_API_URL}/juries`, { token });
      } catch {
        juries = [];
      }

      const apprenticeResults = await Promise.all(
        apprentices.map(async (apprentice) => {
          let payload;
          try {
            payload = await fetchApprenticeDocuments(apprentice.id, token);
          } catch {
            return [];
          }
          const promotionId = payload.promotion?.promotion_id;
          const promotion = promotionId ? promotionMap.get(promotionId) : undefined;

          const semesterWindowMap = new Map<
            string,
            { start?: Date | null; end?: Date | null }
          >();
          promotion?.semesters?.forEach((semester) => {
            const semesterKey = semester.semester_id ?? semester.id;
            if (!semesterKey) return;
            semesterWindowMap.set(semesterKey, {
              start: parseDateOnly(semester.start_date),
              end: parseDateOnly(semester.end_date),
            });
          });

          const nextItems: NotificationItem[] = [];
          (payload.semesters ?? []).forEach((semester) => {
            const window = semesterWindowMap.get(semester.semester_id);
            if (window && !isDateWithin(nowStart, window.start, window.end)) {
              return;
            }
            const deliverables = semester.deliverables ?? [];
            deliverables.forEach((deliverable) => {
              const dueDate = (deliverable as { due_date?: string | null }).due_date;
              if (!dueDate) return;
              const due = parseDateOnly(dueDate);
              if (!due) return;
              if (window && !isDateWithin(due, window.start, window.end)) {
                return;
              }
              const days = daysBetween(nowStart, due);
              if (days < 0 && Math.abs(days) > OVERDUE_WINDOW_DAYS) {
                return;
              }
              if (days > UPCOMING_WINDOW_DAYS) {
                return;
              }
              const isOverdue = days < 0;
              nextItems.push({
                id: `deadline-${apprentice.id}-${semester.semester_id}-${deliverable.id}`,
                type: isOverdue ? "overdue" : "deadline",
                title: isOverdue ? "Deadline depassee" : "Deadline a venir",
                message: `${deliverable.label} (${semester.name}) - ${dueDate}`,
                date: dueDate,
                apprenticeId: apprentice.id,
                apprenticeName: apprentice.fullName,
              });
            });

            (semester.documents ?? []).forEach((document) => {
              const uploadedAt = new Date(document.uploaded_at);
              if (Number.isNaN(uploadedAt.getTime())) return;
              const daysAgo = Math.abs(daysBetween(uploadedAt, nowStart));
              if (daysAgo > DOC_WINDOW_DAYS) return;
              nextItems.push({
                id: `doc-${document.id}`,
                type: "document",
                title: "Nouveau document depose",
                message: `${document.uploader_name} a ajoute ${document.file_name}`,
                date: document.uploaded_at,
                apprenticeId: apprentice.id,
                apprenticeName: apprentice.fullName,
              });
            });
          });

          let entretiens: EntretienRecord[] = [];
          try {
            const entretiensPayload = await fetchJson<ApprentiInfosResponse>(
              `${APPRENTI_API_URL}/infos-completes/${apprentice.id}`,
              { token }
            );
            entretiens = entretiensPayload.data?.entretiens ?? [];
          } catch {
            entretiens = [];
          }
          entretiens.forEach((entretien) => {
            const dateValue = new Date(entretien.date);
            if (Number.isNaN(dateValue.getTime())) return;
            const days = daysBetween(nowStart, dateValue);
            if (days < 0 && Math.abs(days) > OVERDUE_WINDOW_DAYS) {
              return;
            }
            if (days > UPCOMING_WINDOW_DAYS) {
              return;
            }
            if (entretien.semester_id) {
              const window = semesterWindowMap.get(entretien.semester_id);
              if (window && !isDateWithin(dateValue, window.start, window.end)) {
                return;
              }
            }
            nextItems.push({
              id: `entretien-${entretien.entretien_id}`,
              type: "entretien",
              title: "Entretien programme",
              message: `${entretien.sujet}`,
              date: entretien.date,
              apprenticeId: apprentice.id,
              apprenticeName: apprentice.fullName,
            });
          });

          return nextItems;
        })
      );

      const juryItems: NotificationItem[] = juries.flatMap((jury) => {
        const apprenticeId = jury.members?.apprenti?.user_id;
        if (!apprenticeId) return [];
        const apprentice = apprentices.find((item) => item.id === apprenticeId);
        if (!apprentice) return [];

        if (!canBrowseAll && !isApprentice) {
          const isMember =
            jury.members.tuteur.user_id === me.id ||
            jury.members.professeur.user_id === me.id ||
            jury.members.intervenant.user_id === me.id;
          const isFollowing = apprentices.some((entry) => entry.id === apprenticeId);
          if (!isMember && !isFollowing) return [];
        }

        const dateValue = new Date(jury.date);
        if (Number.isNaN(dateValue.getTime())) return [];
        const days = daysBetween(nowStart, dateValue);
        if (days < 0 && Math.abs(days) > OVERDUE_WINDOW_DAYS) return [];
        if (days > UPCOMING_WINDOW_DAYS) return [];

        const promotionId = jury.promotion_reference?.promotion_id;
        const semesterId = jury.promotion_reference?.semester_id;
        if (promotionId && semesterId) {
          const promotion = promotionMap.get(promotionId);
          const semester = promotion?.semesters?.find(
            (entry) => (entry.semester_id ?? entry.id) === semesterId
          );
          const window = semester
            ? { start: parseDateOnly(semester.start_date), end: parseDateOnly(semester.end_date) }
            : null;
          if (window && !isDateWithin(nowStart, window.start, window.end)) return [];
        }

        return [
          {
            id: `jury-${jury.id}`,
            type: "jury",
            title: "Jury programme",
            message: jury.promotion_reference?.semester_name
              ? `${jury.promotion_reference.semester_name}`
              : "Session de jury",
            date: jury.date,
            apprenticeId: apprentice.id,
            apprenticeName: apprentice.fullName,
          },
        ];
      });

      return [...apprenticeResults.flat(), ...juryItems];
    };

    loadNotifications()
      .then((flattened) => {
        if (cancelled) return;
        flattened.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        setItems(flattened);
      })
      .catch((error) => {
        if (cancelled) return;
        setItems([]);
        setError(
          error instanceof Error
            ? error.message
            : "Impossible de charger les notifications."
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [apprentices, token]);

  return {
    items,
    isLoading,
    error,
  };
}
