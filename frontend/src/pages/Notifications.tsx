import React from "react";
import { useNotifications } from "../notifications/useNotifications";
import "../styles/notifications.css";

const formatDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

export default function Notifications() {
  const { items, isLoading, error } = useNotifications();

  return (
    <section className="notifications-page">
      <header className="notifications-header">
        <div>
          <h1>Notifications</h1>
          <p>Suivez les depots de documents et les deadlines a venir.</p>
        </div>
        <span className="notifications-count">{items.length} alertes</span>
      </header>

      {error && <p className="notifications-error">{error}</p>}
      {isLoading ? (
        <p className="notifications-loading">Chargement des notifications...</p>
      ) : items.length === 0 ? (
        <div className="notifications-empty">
          <h2>Aucune notification</h2>
          <p>Vous serez informe ici des nouveaux depots et des echeances importantes.</p>
        </div>
      ) : (
        <div className="notifications-list">
          {items.map((item) => (
            <article key={item.id} className={`notification-card ${item.type}`}>
              <div className="notification-meta">
                <span className="notification-type">
                  {item.type === "document"
                    ? "Document"
                    : item.type === "jury"
                    ? "Jury"
                    : item.type === "entretien"
                    ? "Entretien"
                    : item.type === "overdue"
                    ? "En retard"
                    : "Deadline"}
                </span>
                <span className="notification-date">{formatDate(item.date)}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.message}</p>
              <span className="notification-apprentice">{item.apprenticeName}</span>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
