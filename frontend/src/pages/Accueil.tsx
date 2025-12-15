import React from "react";
import { useAuth, useMe } from "../auth/Permissions";
import { ADMIN_API_URL, fetchJson } from "../config";
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

type PromotionRecord = {
  id: string;
  label?: string;
  annee_academique?: string;
  semesters?: PromotionSemester[];
};

type PromotionsResponse = {
  promotions: PromotionRecord[];
};

type CalendarDeliverable = {
  id: string;
  title: string;
  date: Date;
  dateKey: string;
  semesterName: string;
  promotionLabel: string;
  semesterKey: string;
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

export default function Accueil() {
  const me = useMe();
  const { token } = useAuth();
  const [deliverables, setDeliverables] = React.useState<CalendarDeliverable[]>([]);
  const [semesterRanges, setSemesterRanges] = React.useState<CalendarSemesterRange[]>([]);
  const [calendarError, setCalendarError] = React.useState<string | null>(null);
  const [isLoadingCalendar, setIsLoadingCalendar] = React.useState(false);
  const [currentMonth, setCurrentMonth] = React.useState(() => new Date());

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

  React.useEffect(() => {
    if (!token) {
      setDeliverables([]);
      setSemesterRanges([]);
      return;
    }
    let cancelled = false;
    setIsLoadingCalendar(true);
    setCalendarError(null);
    fetchJson<PromotionsResponse>(`${ADMIN_API_URL}/promos`, { token })
      .then((payload) => {
        if (cancelled) return;
        const allPromotions = payload.promotions ?? [];
        const preferredPromo = me.anneeAcademique?.trim();
        const shouldRestrictToPromo = isApprentice && preferredPromo?.length;
        let scopedPromotions = allPromotions;
        if (shouldRestrictToPromo) {
          scopedPromotions = allPromotions.filter(
            (promotion) =>
              promotion.annee_academique &&
              promotion.annee_academique.toLowerCase() === preferredPromo!.toLowerCase()
          );
        }
        const sourcePromotions =
          shouldRestrictToPromo && scopedPromotions.length > 0 ? scopedPromotions : allPromotions;
        const normalized: CalendarDeliverable[] = [];
        const ranges: CalendarSemesterRange[] = [];
        let paletteIndex = 0;
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        sourcePromotions.forEach((promotion) => {
          const promotionLabel = promotion.label || promotion.annee_academique || "Promotion";
          (promotion.semesters ?? []).forEach((semester, semesterIndex) => {
            const semesterName = semester.name || "Semestre";
            const semesterKey = buildSemesterKey(promotion.id, semester, semesterIndex);
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
                    label: `${semesterName} • ${promotionLabel}`,
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
                  `${promotion.id}-${semester.semester_id ?? semester.name}-${deliverable.title ?? dateKey}`,
                title: deliverable.title?.trim() || "Livrable",
                date: parsed,
                dateKey,
                semesterName,
                promotionLabel,
                semesterKey,
              });
            });
          });
        });

        normalized.sort((a, b) => a.date.getTime() - b.date.getTime());
        setDeliverables(normalized);
        setSemesterRanges(ranges);

        const nextUpcoming = normalized.find((item) => item.date >= today) ?? normalized[0];
        if (nextUpcoming) {
          setCurrentMonth(
            (current) =>
              new Date(nextUpcoming.date.getFullYear(), nextUpcoming.date.getMonth(), current.getDate())
          );
        }
      })
      .catch((error) => {
        if (cancelled) return;
        const message =
          error instanceof Error
            ? error.message
            : "Impossible de charger les echeances des promotions.";
        setCalendarError(message);
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
  }, [token, me.anneeAcademique, isApprentice]);

  const eventsByDate = React.useMemo(() => {
    const map: Record<string, CalendarDeliverable[]> = {};
    deliverables.forEach((deliverable) => {
      if (!map[deliverable.dateKey]) {
        map[deliverable.dateKey] = [];
      }
      map[deliverable.dateKey].push(deliverable);
    });
    return map;
  }, [deliverables]);

  const semesterColorMap = React.useMemo(() => {
    const assignments: Record<string, string> = {};
    semesterRanges.forEach((range) => {
      assignments[range.id] = range.color;
    });
    return assignments;
  }, [semesterRanges]);

  const calendarDays = React.useMemo(() => buildCalendarDays(currentMonth), [currentMonth]);

  const upcomingDeliverables = React.useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return deliverables.filter((deliverable) => deliverable.date >= today).slice(0, 4);
  }, [deliverables]);

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
            <p className="calendar-subtitle">Calendrier des livrables</p>
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
        </div>
        {calendarError ? <p className="calendar-status calendar-error">{calendarError}</p> : null}
        {isLoadingCalendar ? (
          <p className="calendar-status">Chargement des echeances...</p>
        ) : deliverables.length === 0 ? (
          <p className="calendar-status">Aucune echeance n&apos;a encore ete definie pour votre promotion.</p>
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
                      {events.map((event) => (
                        <span
                          key={event.id}
                          className="calendar-tag"
                          title={`${event.title} - ${event.semesterName}`}
                          style={
                            semesterColorMap[event.semesterKey]
                              ? {
                                  backgroundColor: semesterColorMap[event.semesterKey],
                                  borderColor: semesterColorMap[event.semesterKey],
                                }
                              : undefined
                          }
                        >
                          <span
                            className="calendar-tag-dot"
                            style={
                              semesterColorMap[event.semesterKey]
                                ? { backgroundColor: semesterColorMap[event.semesterKey] }
                                : undefined
                            }
                          />
                          <span className="calendar-tag-content">
                            <strong>{event.title}</strong>
                            <small>{event.semesterName}</small>
                          </span>
                        </span>
                      ))}
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
            {upcomingDeliverables.length > 0 ? (
              <div className="calendar-upcoming">
                <h3>Prochaines echeances</h3>
                <ul>
                  {upcomingDeliverables.map((event) => (
                    <li key={`upcoming-${event.id}`}>
                      <span className="calendar-upcoming-date">
                        {event.date.toLocaleDateString("fr-FR", {
                          weekday: "short",
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                      <div>
                        <p>{event.title}</p>
                        <small>
                          {event.semesterName} - {event.promotionLabel}
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
