import "../styles/promotions.css";

type Promotion = {
  id: string;
  label: string;
  year: string;
  apprentices: number;
  coordinators: string[];
  nextMilestone: string;
};

type Alert = {
  id: string;
  message: string;
  level: "info" | "warning";
};

const PROMOTIONS: Promotion[] = [
  {
    id: "PROM-2025-A",
    label: "Ing Tech - Promo 2025",
    year: "2025",
    apprentices: 32,
    coordinators: ["Nathalie Garcia", "Hugo Lemaire"],
    nextMilestone: "Jury intermédiaire - 12 mars 2025",
  },
  {
    id: "PROM-2026-B",
    label: "Cyberdefense - Promo 2026",
    year: "2026",
    apprentices: 27,
    coordinators: ["Sofia Mendes"],
    nextMilestone: "Comité entreprise - 3 avril 2025",
  },
  {
    id: "PROM-2024-C",
    label: "Dev Fullstack - Promo 2024",
    year: "2024",
    apprentices: 29,
    coordinators: ["Marc Delaunay"],
    nextMilestone: "Soutenance finale - 24 janvier 2025",
  },
];

const ALERTS: Alert[] = [
  {
    id: "alert-1",
    level: "warning",
    message:
      "3 rapports de mission en retard dans la promo Ing Tech 2025. Relancer les maîtres d'apprentissage.",
  },
  {
    id: "alert-2",
    level: "info",
    message:
      "Jury final de la promo Dev Fullstack 2024 programmé le 24 janvier. Vérifier les convocations.",
  },
];

export default function Promotions() {
  return (
    <div className="promotions-page">
      <header className="promotions-header">
        <div>
          <h1>Gestion des promotions</h1>
          <p>
            Surveillez chaque promotion, anticipez les échéances et gardez le
            contact avec les tuteurs pour accompagner tous les apprentis.
          </p>
        </div>
        <button type="button" className="cta-button">
          Créer une promotion
        </button>
      </header>

      <section className="alerts">
        {ALERTS.map((alert) => (
          <article key={alert.id} className={`alert-card ${alert.level}`}>
            <span className="alert-badge">
              {alert.level === "warning" ? "Attention" : "Information"}
            </span>
            <p>{alert.message}</p>
          </article>
        ))}
      </section>

      <section className="promotion-list">
        {PROMOTIONS.map((promotion) => (
          <article key={promotion.id} className="promotion-card">
            <header className="promotion-card-header">
              <div>
                <h2>{promotion.label}</h2>
                <span className="promotion-year">{promotion.year}</span>
              </div>
              <button type="button" className="secondary-button">
                Voir le détail
              </button>
            </header>

            <dl className="promotion-grid">
              <div>
                <dt>Apprentis</dt>
                <dd>{promotion.apprentices}</dd>
              </div>
              <div>
                <dt>Coordinateurs</dt>
                <dd>{promotion.coordinators.join(", ")}</dd>
              </div>
              <div>
                <dt>Prochaine étape</dt>
                <dd>{promotion.nextMilestone}</dd>
              </div>
            </dl>

            <footer className="promotion-footer">
              <button type="button" className="link-button">
                Consulter les suivis
              </button>
              <button type="button" className="link-button">
                Exporter les rapports
              </button>
            </footer>
          </article>
        ))}
      </section>
    </div>
  );
}
