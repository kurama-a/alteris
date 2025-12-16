import React from "react";
import { useAuth, useMe } from "../auth/Permissions";
import { ADMIN_API_URL, APPRENTI_API_URL, JURY_API_URL, fetchJson } from "../config";
import "../styles/accueil.css";

type PromotionDeliverable = {
  deliverable_id?: string;
  title?: string;
  due_date?: string;
  description?: string;
};

type PromotionSemester = {
  semester_id?: string;
  name?: string;
  start_date?: string;
  end_date?: string;
  deliverables?: PromotionDeliverable[];
};

type PromotionApprenticeRef = {
  _id?: string;
  id?: string;
  apprenti_id?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
};

type PromotionRecord = {
  id: string;
  label?: string;
  annee_academique?: string;
  semesters?: PromotionSemester[];
  apprentis?: PromotionApprenticeRef[];
};

type PromotionsResponse = {
  promotions: PromotionRecord[];
};

type ApprenticeOption = {
  id: string;
  label: string;
  email?: string;
};

type CalendarEventCategory = "deliverable" | "meeting" | "jury";

type CalendarEvent = {
  id: string;
  title: string;
  date: Date;
  dateKey: string;
  promotionLabel: string;
  semesterName?: string;
  semesterKey?: string;
  category: CalendarEventCategory;
  details?: string;
};

type CalendarDay = {
  date: Date;
  dateKey: string;
  isCurrentMonth: boolean;
  isToday: boolean;
};

type CalendarSemesterRange = {
  id: string;
  label: string;
  start: Date;
  end: Date;
  color: string;
};

const WEEK_DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
const SEMESTER_COLOR_PALETTE = [
  "#fde6b3",
  "#c7e9fb",
  "#ffd6e8",
  "#d8f2c4",
  "#fbe7ff",
  "#ffe5d4",
  "#d9ddff",
  "#c9f0e1",
  "#f7d8c7",
  "#e8d9ff",
];

const EVENT_CATEGORY_LABELS: Record<CalendarEventCategory, string> = {
  deliverable: "Livrable",
  meeting: "Entretien",
  jury: "Jury",
};

function formatDateKey(date: Date): string {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy.toISOString().split("T")[0] ?? "";
}

function buildCalendarDays(referenceDate: Date): CalendarDay[] {
  const year = referenceDate.getFullYear();
  const month = referenceDate.getMonth();
  const firstDayOfMonth = new Date(year, month, 1);
  const mondayBasedOffset = (firstDayOfMonth.getDay() + 6) % 7;
  const firstVisibleDate = new Date(year, month, 1 - mondayBasedOffset);
  const todayKey = formatDateKey(new Date());
  const days: CalendarDay[] = [];
  for (let index = 0; index < 42; index += 1) {
    const date = new Date(firstVisibleDate);
    date.setDate(firstVisibleDate.getDate() + index);
    const dateKey = formatDateKey(date);
    days.push({
      date,
      dateKey,
      isCurrentMonth: date.getMonth() === month,
      isToday: dateKey === todayKey,
    });
  }
  return days;
}

function buildSemesterKey(promotionId: string, semester: PromotionSemester, fallbackIndex: number): string {
  const base = semester.semester_id ?? semester.name ?? `semester-${fallbackIndex}`;
  return `${promotionId}-${base}`;
}

function getPromotionDisplayLabel(promotion: PromotionRecord): string {
  return promotion.label || promotion.annee_academique || "Promotion";
}

type ApprenticeInfosResponse = {
  data?: {
    entretiens?: Array<{
      entretien_id: string;
      apprenti_id?: string;
      apprenti_nom?: string;
      date?: string;
      sujet?: string;
    }>;
  };
};

type JuryMemberSummary = {
  user_id?: string;
  role?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
};

type JuryCalendarRecord = {
  id: string;
  date: string;
  status: string;
  members: {
    tuteur?: JuryMemberSummary;
    professeur?: JuryMemberSummary;
    apprenti?: JuryMemberSummary;
    intervenant?: JuryMemberSummary;
  };
  promotion_reference?: {
    promotion_id?: string;
    annee_academique?: string;
    label?: string;
    semester_name?: string;
    deliverable_title?: string;
  };
};

export default function Accueil() {
  const me = useMe();
  const { token } = useAuth();
  const [deliverables, setDeliverables] = React.useState<CalendarEvent[]>([]);
  const [meetingEvents, setMeetingEvents] = React.useState<CalendarEvent[]>([]);
  const [juryEvents, setJuryEvents] = React.useState<CalendarEvent[]>([]);
  const [semesterRanges, setSemesterRanges] = React.useState<CalendarSemesterRange[]>([]);
  const [calendarError, setCalendarError] = React.useState<string | null>(null);
  const [isLoadingCalendar, setIsLoadingCalendar] = React.useState(false);
  const [currentMonth, setCurrentMonth] = React.useState(() => new Date());
  const [promotions, setPromotions] = React.useState<PromotionRecord[]>([]);
  const [selectedPromotionId, setSelectedPromotionId] = React.useState<string | null>(null);
  const [selectedApprenticeId, setSelectedApprenticeId] = React.useState<string | null>(null);

  const displayName = React.useMemo(() => {
    if (me.firstName || me.lastName) {
      return `${me.firstName ?? ""} ${me.lastName ?? ""}`.trim();
    }
    return me.fullName;
  }, [me.firstName, me.lastName, me.fullName]);

  const normalizedRoles = React.useMemo(() => {
    const roles = new Set<string>();
    if (me.role) roles.add(me.role.toLowerCase());
    (me.roles ?? []).forEach((role) => {
      if (role) roles.add(role.toLowerCase());
    });
    return roles;
  }, [me.role, me.roles]);

  const isApprentice = normalizedRoles.has("apprenti");
  const supervisedApprenticeIds = React.useMemo(() => {
    const set = new Set<string>();
    (me.apprentices ?? []).forEach((apprentice) => {
      if (apprentice.id) {
        set.add(apprentice.id);
      }
    });
    return set;
  }, [me.apprentices]);
  const isTutorRole = React.useMemo(
    () =>
      Array.from(normalizedRoles).some(
        (role) => role.includes("tuteur") || role.includes("maitre")
      ),
    [normalizedRoles]
  );
const hasGlobalPromotionSelector = React.useMemo(() => {
  if (normalizedRoles.has("admin") || normalizedRoles.has("administrateur")) {
    return true;
  }
  return Array.from(normalizedRoles).some(
    (role) => role.includes("responsable") || role.includes("coordin")
  );
}, [normalizedRoles]);
const requiresPromotionSelector = isTutorRole || hasGlobalPromotionSelector;
const needsApprenticeSelector = isTutorRole || hasGlobalPromotionSelector;

  const accessiblePromotions = React.useMemo(() => {
    if (!promotions.length) {
      return [];
    }
    if (isApprentice) {
      const preferredPromo = me.anneeAcademique?.trim();
      if (preferredPromo) {
        const scopedPromotions = promotions.filter(
          (promotion) =>
            promotion.annee_academique &&
            promotion.annee_academique.toLowerCase() === preferredPromo.toLowerCase()
        );
        if (scopedPromotions.length) {
          return scopedPromotions;
        }
      }
    }
    if (isTutorRole) {
      const filtered = promotions.filter((promotion) =>
        (promotion.apprentis ?? []).some((apprentice) => {
          const identifier =
            apprentice._id ?? apprentice.id ?? apprentice.apprenti_id ?? apprentice.email;
          return identifier ? supervisedApprenticeIds.has(String(identifier)) : false;
        })
      );
      return filtered.length ? filtered : promotions;
    }
    if (hasGlobalPromotionSelector) {
      return promotions;
    }
    return promotions;
  }, [
    promotions,
    isApprentice,
    me.anneeAcademique,
    isTutorRole,
    supervisedApprenticeIds,
    hasGlobalPromotionSelector,
  ]);

  const activePromotion = React.useMemo(() => {
    if (!accessiblePromotions.length) {
      return null;
    }
    if (requiresPromotionSelector) {
      if (!selectedPromotionId) {
        return null;
      }
      return (
        accessiblePromotions.find((promotion) => promotion.id === selectedPromotionId) ?? null
      );
    }
    return accessiblePromotions[0] ?? null;
  }, [accessiblePromotions, requiresPromotionSelector, selectedPromotionId]);

  const apprenticeOptions = React.useMemo<ApprenticeOption[]>(() => {
    if (!activePromotion?.apprentis?.length) {
      if (isApprentice && me.id) {
        return [
          {
            id: me.id,
            label: me.fullName || me.email || "Mon profil",
            email: me.email,
          },
        ];
      }
      return [];
    }
    const seen = new Set<string>();
    const options: ApprenticeOption[] = [];
    activePromotion.apprentis.forEach((apprentice) => {
      const identifier =
        apprentice._id ?? apprentice.id ?? apprentice.apprenti_id ?? apprentice.email;
      if (!identifier || seen.has(identifier)) {
        return;
      }
      seen.add(identifier);
      const label =
        `${apprentice.first_name ?? ""} ${apprentice.last_name ?? ""}`.trim() ||
        apprentice.email ||
        "Apprenti";
      options.push({ id: String(identifier), label, email: apprentice.email });
    });
    if (isApprentice && me.id && !seen.has(me.id)) {
      options.push({
        id: me.id,
        label: me.fullName || me.email || "Mon profil",
        email: me.email,
      });
    }
    return options;
  }, [activePromotion, isApprentice, me.email, me.fullName, me.id]);

  const filteredApprenticeOptions = React.useMemo(() => {
    if (!apprenticeOptions.length) {
      return [];
    }
    if (isTutorRole) {
      return apprenticeOptions.filter((option) => supervisedApprenticeIds.has(option.id));
    }
    if (hasGlobalPromotionSelector) {
      return apprenticeOptions;
    }
    if (isApprentice && me.id) {
      return apprenticeOptions.filter((option) => option.id === me.id);
    }
    return apprenticeOptions;
  }, [
    apprenticeOptions,
    hasGlobalPromotionSelector,
    isApprentice,
    isTutorRole,
    me.id,
    supervisedApprenticeIds,
  ]);

  React.useEffect(() => {
    if (!token) {
      setPromotions([]);
      setDeliverables([]);
      setSemesterRanges([]);
      setIsLoadingCalendar(false);
      return;
    }
    let cancelled = false;
    setIsLoadingCalendar(true);
    setCalendarError(null);
    fetchJson<PromotionsResponse>(`${ADMIN_API_URL}/promos`, { token })
      .then((payload) => {
        if (cancelled) return;
        setPromotions(payload.promotions ?? []);
      })
      .catch((error) => {
        if (cancelled) return;
        const message =
          error instanceof Error
            ? error.message
            : "Impossible de charger les echeances des promotions.";
        setCalendarError(message);
        setPromotions([]);
        setDeliverables([]);
        setSemesterRanges([]);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingCalendar(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);


  React.useEffect(() => {
    if (!requiresPromotionSelector) {
      if (selectedPromotionId !== null) {
        setSelectedPromotionId(null);
      }
      return;
    }
    if (!accessiblePromotions.length) {
      if (selectedPromotionId !== null) {
        setSelectedPromotionId(null);
      }
      return;
    }
    if (
      !selectedPromotionId ||
      !accessiblePromotions.some((promotion) => promotion.id === selectedPromotionId)
    ) {
      const nextId = accessiblePromotions[0]?.id ?? null;
      setSelectedPromotionId(nextId ?? null);
    }
  }, [requiresPromotionSelector, accessiblePromotions, selectedPromotionId]);

  React.useEffect(() => {
    if (!needsApprenticeSelector) {
      if (isApprentice && me.id) {
        setSelectedApprenticeId(me.id);
      } else {
        setSelectedApprenticeId(null);
      }
      return;
    }
    if (!filteredApprenticeOptions.length) {
      setSelectedApprenticeId(null);
      return;
    }
    if (
      !selectedApprenticeId ||
      !filteredApprenticeOptions.some((option) => option.id === selectedApprenticeId)
    ) {
      setSelectedApprenticeId(filteredApprenticeOptions[0]?.id ?? null);
    }
  }, [
    needsApprenticeSelector,
    filteredApprenticeOptions,
    selectedApprenticeId,
    isApprentice,
    me.id,
  ]);

  const promotionSelectorOptions = React.useMemo(
    () =>
      accessiblePromotions.map((promotion) => ({
        id: promotion.id,
        label: getPromotionDisplayLabel(promotion),
      })),
    [accessiblePromotions]
  );

  const activePromotionApprenticeIds = React.useMemo(() => {
    const ids = new Set<string>();
    if (activePromotion?.apprentis) {
      activePromotion.apprentis.forEach((apprentice) => {
        const identifier =
          apprentice._id ?? apprentice.id ?? apprentice.apprenti_id ?? apprentice.email;
        if (identifier) {
          ids.add(String(identifier));
        }
      });
    }
    if (isApprentice && me.id) {
      ids.add(me.id);
    }
    return Array.from(ids);
  }, [activePromotion, isApprentice, me.id]);

  const focusedApprenticeIds = React.useMemo(() => {
    if (needsApprenticeSelector) {
      return selectedApprenticeId ? [selectedApprenticeId] : [];
    }
    if (isApprentice && me.id) {
      return [me.id];
    }
    if (activePromotionApprenticeIds.length) {
      return activePromotionApprenticeIds;
    }
    return [];
  }, [
    needsApprenticeSelector,
    selectedApprenticeId,
    isApprentice,
    me.id,
    activePromotionApprenticeIds,
  ]);

  const apprenticeIdsKey = React.useMemo(
    () => [...focusedApprenticeIds].sort().join("|"),
    [focusedApprenticeIds]
  );

  React.useEffect(() => {
    if (!activePromotion) {
      setDeliverables([]);
      setSemesterRanges([]);
      return;
    }
    const normalized: CalendarEvent[] = [];
    const ranges: CalendarSemesterRange[] = [];
    let paletteIndex = 0;
    const promotionLabel = getPromotionDisplayLabel(activePromotion);
    (activePromotion.semesters ?? []).forEach((semester, semesterIndex) => {
      const semesterName = semester.name || "Semestre";
      const semesterKey = buildSemesterKey(activePromotion.id, semester, semesterIndex);
      const startValue = semester.start_date?.trim();
      const endValue = semester.end_date?.trim();
      if (startValue && endValue) {
        const startDate = new Date(startValue);
        const endDate = new Date(endValue);
        if (!Number.isNaN(startDate.getTime()) && !Number.isNaN(endDate.getTime())) {
          startDate.setHours(0, 0, 0, 0);
          endDate.setHours(0, 0, 0, 0);
          if (endDate >= startDate) {
            ranges.push({
              id: semesterKey,
              label: `${semesterName} - ${promotionLabel}`,
              start: startDate,
              end: endDate,
              color: SEMESTER_COLOR_PALETTE[paletteIndex % SEMESTER_COLOR_PALETTE.length],
            });
            paletteIndex += 1;
          }
        }
      }
      (semester.deliverables ?? []).forEach((deliverable) => {
        const dueDateValue = deliverable.due_date?.trim();
        if (!dueDateValue) {
          return;
        }
        const parsed = new Date(dueDateValue);
        if (Number.isNaN(parsed.getTime())) {
          return;
        }
        const dateKey = formatDateKey(parsed);
        normalized.push({
          id:
            deliverable.deliverable_id ??
            `${activePromotion.id}-${semester.semester_id ?? semester.name}-${deliverable.title ?? dateKey}`,
          title: deliverable.title?.trim() || "Livrable",
          date: parsed,
          dateKey,
          semesterName,
          promotionLabel,
          semesterKey,
          category: "deliverable",
          details: semesterName,
        });
      });
    });

    normalized.sort((a, b) => a.date.getTime() - b.date.getTime());
    setDeliverables(normalized);
    setSemesterRanges(ranges);
  }, [activePromotion]);

  React.useEffect(() => {
    if (!token) {
      setMeetingEvents([]);
      return;
    }
    if (!focusedApprenticeIds.length) {
      setMeetingEvents([]);
      return;
    }
    let cancelled = false;
    const promotionLabel =
      activePromotion?.label ||
      activePromotion?.annee_academique ||
      me.anneeAcademique ||
      "Promotion";
    Promise.all(
      focusedApprenticeIds.map((apprenticeId) =>
        fetchJson<ApprenticeInfosResponse>(
          `${APPRENTI_API_URL}/infos-completes/${apprenticeId}`,
          { token }
        )
          .then((payload) => payload.data?.entretiens ?? [])
          .catch(() => [])
      )
    )
      .then((results) => {
        if (cancelled) return;
        const events: CalendarEvent[] = [];
        results.forEach((entretiens) => {
          entretiens.forEach((entretien) => {
            const dateValue = entretien.date ?? "";
            const parsed = new Date(dateValue);
            if (Number.isNaN(parsed.getTime())) {
              return;
            }
            const dateKey = formatDateKey(parsed);
            const title = entretien.sujet?.trim()
              ? `Entretien - ${entretien.sujet.trim()}`
              : "Entretien de suivi";
            events.push({
              id: `meeting-${entretien.entretien_id ?? dateKey}`,
              title,
              date: parsed,
              dateKey,
              promotionLabel,
              category: "meeting",
              details: entretien.apprenti_nom || "Entretien planifié",
            });
          });
        });
        events.sort((a, b) => a.date.getTime() - b.date.getTime());
        setMeetingEvents(events);
      })
      .catch(() => {
        if (!cancelled) {
          setMeetingEvents([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [activePromotion, focusedApprenticeIds, apprenticeIdsKey, token, me.anneeAcademique]);

  React.useEffect(() => {
    if (!token) {
      setJuryEvents([]);
      return;
    }
    let cancelled = false;
    fetchJson<JuryCalendarRecord[]>(`${JURY_API_URL}/juries`, { token })
      .then((payload) => {
        if (cancelled) return;
        const juries = Array.isArray(payload) ? payload : [];
        const normalized: CalendarEvent[] = [];
        juries.forEach((jury) => {
          const dateValue = jury.date;
          const parsed = new Date(dateValue);
          if (Number.isNaN(parsed.getTime())) {
            return;
          }
          const promotionMatches = () => {
            if (!activePromotion) {
              return !hasGlobalPromotionSelector && !isTutorRole;
            }
            if (jury.promotion_reference?.promotion_id && activePromotion.id) {
              return jury.promotion_reference.promotion_id === activePromotion.id;
            }
            if (
              jury.promotion_reference?.annee_academique &&
              activePromotion.annee_academique
            ) {
              return (
                jury.promotion_reference.annee_academique.toLowerCase() ===
                activePromotion.annee_academique.toLowerCase()
              );
            }
            return false;
          };
          const apprenticeId = jury.members?.apprenti?.user_id;
          const isApprenticeMatch = apprenticeId === me.id;
          const isSupervisedApprentice =
            apprenticeId && supervisedApprenticeIds.has(apprenticeId);
          const isMember =
            jury.members?.tuteur?.user_id === me.id ||
            jury.members?.professeur?.user_id === me.id ||
            jury.members?.intervenant?.user_id === me.id;

          let include = false;
          if (needsApprenticeSelector) {
            include =
              Boolean(selectedApprenticeId) && apprenticeId === selectedApprenticeId && promotionMatches();
          } else if (isApprentice) {
            include = isApprenticeMatch;
          } else if (isTutorRole) {
            include = (isSupervisedApprentice || isMember) && promotionMatches();
          } else if (hasGlobalPromotionSelector) {
            include = promotionMatches();
          } else {
            include = isMember || isApprenticeMatch;
          }

          if (!include) {
            return;
          }

          const dateKey = formatDateKey(parsed);
          const promotionLabel =
            jury.promotion_reference?.label ||
            jury.promotion_reference?.annee_academique ||
            activePromotion?.label ||
            activePromotion?.annee_academique ||
            "Promotion";
          const apprenticeName = [
            jury.members?.apprenti?.first_name ?? "",
            jury.members?.apprenti?.last_name ?? "",
          ]
            .join(" ")
            .trim() || jury.members?.apprenti?.email || "Apprenti";
          const semesterName = jury.promotion_reference?.semester_name || "Jury";
          const statusLabel = jury.status === "termine" ? "Terminé" : "Planifié";
          const title =
            jury.promotion_reference?.deliverable_title ||
            `Jury ${semesterName} (${statusLabel})`;

          normalized.push({
            id: `jury-${jury.id}`,
            title,
            date: parsed,
            dateKey,
            promotionLabel,
            category: "jury",
            details: apprenticeName,
            semesterName,
          });
        });
        normalized.sort((a, b) => a.date.getTime() - b.date.getTime());
        setJuryEvents(normalized);
      })
      .catch(() => {
        if (!cancelled) {
          setJuryEvents([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [
    activePromotion,
    hasGlobalPromotionSelector,
    isApprentice,
    isTutorRole,
    me.id,
    supervisedApprenticeIds,
    needsApprenticeSelector,
    selectedApprenticeId,
    token,
  ]);

  const calendarEvents = React.useMemo(() => {
    const merged = [...deliverables, ...meetingEvents, ...juryEvents];
    return merged.sort((a, b) => a.date.getTime() - b.date.getTime());
  }, [deliverables, meetingEvents, juryEvents]);

  const lastAutoFocusRef = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (!calendarEvents.length) {
      return;
    }
    const nextEvent =
      calendarEvents.find((event) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return event.date >= today;
      }) ?? calendarEvents[0];
    const promotionKey = activePromotion?.id || (isApprentice ? me.id : "default");
    if (lastAutoFocusRef.current === `${promotionKey}-${calendarEvents.length}`) {
      return;
    }
    lastAutoFocusRef.current = `${promotionKey}-${calendarEvents.length}`;
    setCurrentMonth(
      (current) => new Date(nextEvent.date.getFullYear(), nextEvent.date.getMonth(), current.getDate())
    );
  }, [calendarEvents, activePromotion, isApprentice, me.id]);

  const eventsByDate = React.useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {};
    calendarEvents.forEach((event) => {
      if (!map[event.dateKey]) {
        map[event.dateKey] = [];
      }
      map[event.dateKey].push(event);
    });
    return map;
  }, [calendarEvents]);

  const semesterColorMap = React.useMemo(() => {
    const assignments: Record<string, string> = {};
    semesterRanges.forEach((range) => {
      assignments[range.id] = range.color;
    });
    return assignments;
  }, [semesterRanges]);

  const getEventStyles = React.useCallback(
    (event: CalendarEvent) => {
      if (event.category === "deliverable" && event.semesterKey) {
        const color = semesterColorMap[event.semesterKey];
        if (color) {
          return {
            tag: { backgroundColor: color, borderColor: color },
            dot: { backgroundColor: color },
          };
        }
      }
      if (event.category === "meeting") {
        return {
          tag: { backgroundColor: "#e0f2fe", borderColor: "#bae6fd", color: "#075985" },
          dot: { backgroundColor: "#0ea5e9" },
        };
      }
      if (event.category === "jury") {
        return {
          tag: { backgroundColor: "#fef3c7", borderColor: "#fcd34d", color: "#92400e" },
          dot: { backgroundColor: "#f59e0b" },
        };
      }
      return { tag: undefined, dot: undefined };
    },
    [semesterColorMap]
  );

  const calendarDays = React.useMemo(() => buildCalendarDays(currentMonth), [currentMonth]);

  const upcomingEvents = React.useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return calendarEvents.filter((event) => event.date >= today).slice(0, 4);
  }, [calendarEvents]);

  const monthLabel = React.useMemo(() => {
    return new Intl.DateTimeFormat("fr-FR", {
      month: "long",
      year: "numeric",
    }).format(currentMonth);
  }, [currentMonth]);

  const goToPreviousMonth = React.useCallback(() => {
    setCurrentMonth((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1));
  }, []);

  const goToNextMonth = React.useCallback(() => {
    setCurrentMonth((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1));
  }, []);

  const emptyCalendarMessage = React.useMemo(() => {
    if (!accessiblePromotions.length) {
      if (isTutorRole) {
        return "Aucune promotion n'est associée à vos apprentis pour le moment.";
      }
      if (hasGlobalPromotionSelector) {
        return "Aucune promotion n'a encore été configurée.";
      }
      if (isApprentice) {
        return "Votre promotion n'a pas encore de semestres planifiés.";
      }
      return "Aucune promotion disponible.";
    }
    if (requiresPromotionSelector && !activePromotion) {
      return "Sélectionnez une promotion pour afficher ses échéances.";
    }
    if (needsApprenticeSelector && !selectedApprenticeId) {
      return "Sélectionnez un apprenti pour afficher son calendrier.";
    }
    return "Aucune échéance n'a encore été définie pour cette promotion.";
  }, [
    accessiblePromotions.length,
    isTutorRole,
    hasGlobalPromotionSelector,
    isApprentice,
    requiresPromotionSelector,
    activePromotion,
    needsApprenticeSelector,
    selectedApprenticeId,
  ]);

  return (
    <main className="accueil">
      <section className="accueil-hero">
        <img
          className="accueil-hero-image"
          src="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?auto=format&fit=crop&w=1600&q=80"
          alt="Vue d'ensemble d'un campus"
        />
        <div className="accueil-hero-content">
          <p className="accueil-salut">Bonjour</p>
          <h1 className="accueil-title">{displayName || me.fullName}</h1>
          <p className="accueil-text">
            Bienvenue sur la plateforme Alteris. Retrouvez vos informations, vos documents et le suivi de votre parcours directement depuis cet espace.
          </p>
        </div>
      </section>
      <section className="accueil-calendar">
        <div className="calendar-header">
          <div>
            <p className="calendar-subtitle">Calendrier des échéances</p>
            <h2 className="calendar-title">{monthLabel}</h2>
          </div>
          <div className="calendar-nav">
            <button type="button" onClick={goToPreviousMonth} aria-label="Mois precedent">
              {"<"}
            </button>
            <span>{monthLabel}</span>
            <button type="button" onClick={goToNextMonth} aria-label="Mois suivant">
              {">"}
            </button>
          </div>
          {requiresPromotionSelector ? (
            <div className="calendar-filter">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  fontSize: 14,
                  gap: 4,
                  fontWeight: 500,
                }}
              >
                Promotion affichée
                <select
                  value={selectedPromotionId ?? ""}
                  onChange={(event) => setSelectedPromotionId(event.target.value || null)}
                  disabled={!promotionSelectorOptions.length}
                  style={{
                    borderRadius: 8,
                    border: "1px solid #cbd5f5",
                    padding: "8px 12px",
                    fontSize: 14,
                    fontWeight: 600,
                    background: "#fff",
                  }}
                >
                  {promotionSelectorOptions.length === 0 ? (
                    <option value="">Aucune promotion disponible</option>
                  ) : (
                    promotionSelectorOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))
                  )}
                </select>
              </label>
            </div>
          ) : null}
          {needsApprenticeSelector ? (
            <div className="calendar-filter">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  fontSize: 14,
                  gap: 4,
                  fontWeight: 500,
                }}
              >
                Apprenti suivi
                <select
                  value={selectedApprenticeId ?? ""}
                  onChange={(event) => setSelectedApprenticeId(event.target.value || null)}
                  disabled={!filteredApprenticeOptions.length}
                  style={{
                    borderRadius: 8,
                    border: "1px solid #cbd5f5",
                    padding: "8px 12px",
                    fontSize: 14,
                    fontWeight: 600,
                    background: "#fff",
                  }}
                >
                  {filteredApprenticeOptions.length === 0 ? (
                    <option value="">Aucun apprenti disponible</option>
                  ) : (
                    filteredApprenticeOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                        {option.email ? ` (${option.email})` : ""}
                      </option>
                    ))
                  )}
                </select>
              </label>
            </div>
          ) : null}
        </div>
        {activePromotion ? (
          <div
            style={{
              border: "1px solid rgba(37, 99, 235, 0.2)",
              background: "rgba(37, 99, 235, 0.08)",
              padding: "12px 16px",
              borderRadius: 12,
              marginBottom: 16,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <div>
              <p style={{ margin: 0, color: "#1d4ed8", fontWeight: 600 }}>Promotion en cours d'affichage</p>
              <strong style={{ fontSize: 16 }}>
                {getPromotionDisplayLabel(activePromotion)}{" "}
                {activePromotion.annee_academique ? `(${activePromotion.annee_academique})` : ""}
              </strong>
            </div>
            <span
              style={{
                padding: "4px 12px",
                borderRadius: 999,
                background: "#fff",
                border: "1px solid #93c5fd",
                color: "#1d4ed8",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {activePromotion.semesters?.length ?? 0} semestre(s)
            </span>
          </div>
        ) : null}
        {calendarError ? <p className="calendar-status calendar-error">{calendarError}</p> : null}
        {isLoadingCalendar ? (
          <p className="calendar-status">Chargement des echeances...</p>
        ) : calendarEvents.length === 0 ? (
          <p className="calendar-status">{emptyCalendarMessage}</p>
        ) : (
          <>
            <div className="calendar-weekdays">
              {WEEK_DAYS.map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>
            <div className="calendar-grid">
              {calendarDays.map((day) => {
                const events = eventsByDate[day.dateKey] ?? [];
                const coveringRanges = semesterRanges.filter(
                  (range) => day.date >= range.start && day.date <= range.end
                );
                const classes = [
                  "calendar-cell",
                  day.isCurrentMonth ? "" : "is-muted",
                  day.isToday ? "is-today" : "",
                  coveringRanges.length > 0 ? "has-semester" : "",
                ]
                  .filter(Boolean)
                  .join(" ");
                const uniqueColors = coveringRanges.map((range) => range.color);
                let cellStyle: React.CSSProperties | undefined;
                if (uniqueColors.length === 1) {
                  cellStyle = { backgroundColor: uniqueColors[0] };
                } else if (uniqueColors.length > 1) {
                  const gradientStops = uniqueColors
                    .map((color, index) => {
                      const start = (index / uniqueColors.length) * 100;
                      const end = ((index + 1) / uniqueColors.length) * 100;
                      return `${color} ${start}% ${end}%`;
                    })
                    .join(", ");
                  cellStyle = {
                    backgroundImage: `linear-gradient(135deg, ${gradientStops})`,
                    backgroundColor: uniqueColors[0],
                  };
                }
                return (
                  <div key={`${day.dateKey}-${day.date.getTime()}`} className={classes} style={cellStyle}>
                    <span className="calendar-day-number">{day.date.getDate()}</span>
                    <div className="calendar-tags">
                      {events.map((event) => {
                        const eventStyles = getEventStyles(event);
                        const subtitle = event.details || event.semesterName || event.promotionLabel;
                        return (
                          <span
                            key={event.id}
                            className={`calendar-tag calendar-tag-${event.category}`}
                            title={`${event.title} - ${subtitle}`}
                            style={eventStyles.tag}
                          >
                            <span className="calendar-tag-dot" style={eventStyles.dot} />
                            <span className="calendar-tag-content">
                              <strong>{event.title}</strong>
                              {subtitle ? <small>{subtitle}</small> : null}
                            </span>
                          </span>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
            {semesterRanges.length > 0 ? (
              <div className="calendar-legend">
                <h3>Legende des semestres</h3>
                <ul>
                  {semesterRanges.map((range) => (
                    <li key={`legend-${range.id}`}>
                      <span className="legend-color" style={{ backgroundColor: range.color }} />
                      <span>{range.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {upcomingEvents.length > 0 ? (
              <div className="calendar-upcoming">
                <h3>Prochaines echeances</h3>
                <ul>
                  {upcomingEvents.map((event) => (
                    <li key={`upcoming-${event.id}`}>
                      <span className="calendar-upcoming-date">
                        {event.date.toLocaleDateString("fr-FR", {
                          weekday: "short",
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                      <div>
                        <p style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                          <span>{event.title}</span>
                          <span
                            style={{
                              fontSize: 12,
                              borderRadius: 999,
                              padding: "2px 8px",
                              background: "#eef2ff",
                              color: "#4338ca",
                              border: "1px solid #c7d2fe",
                              fontWeight: 600,
                            }}
                          >
                            {EVENT_CATEGORY_LABELS[event.category]}
                          </span>
                        </p>
                        <small>
                          {(event.details || event.semesterName || event.promotionLabel) ??
                            event.promotionLabel}
                        </small>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}
