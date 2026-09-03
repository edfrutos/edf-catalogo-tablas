/*
 * Atlas Trigger (OPCIONAL) — sincronización de convenciones en `users`.
 *
 * Mantiene en cada documento de `edf_catalogotablas.users` las dos convenciones
 * de nombres de campo en sync, escriba quien escriba:
 *   - snake_case  (app Flask):  username, nombre, role, is_active, created_at, last_login, ...
 *   - PascalCase  (cliente .NET): Username, Name,  Role, IsActive,  CreatedAt,  LastLoginAt, ...
 *
 * Es puramente aditivo/espejo: copia el lado que cambió al lado que falta o
 * quedó desincronizado. Así ninguna de las dos apps necesita conocer la otra
 * convención y el backfill deja de ser necesario para altas nuevas.
 *
 * Cómo instalarlo:
 *   Atlas UI -> (proyecto) -> Triggers -> Add Trigger
 *     Type: Database
 *     Cluster / DB / Collection: <cluster0.alh9mwn> / edf_catalogotablas / users
 *     Operation types: Insert, Update, Replace
 *     Full Document: ON
 *     Function: pega esta función
 *
 * Nota: el trigger se auto-excluye de sus propias escrituras comprobando que
 * haya algo que copiar antes de hacer updateOne (si no hay diferencias, no
 * escribe y no se re-dispara).
 */

exports = async function (changeEvent) {
  const doc = changeEvent.fullDocument;
  if (!doc) return;

  // canónico snake_case  ->  PascalCase equivalente
  const PAIRS = [
    ["username", "Username"],
    ["nombre", "Name"],
    ["role", "Role"],
    ["is_active", "IsActive"],
    ["created_at", "CreatedAt"],
    ["last_login", "LastLoginAt"],
    ["phone", "Phone"],
    ["company", "Company"],
    ["address", "Address"],
    ["occupation", "Occupation"],
  ];

  const isEmpty = (v) => v === undefined || v === null || v === "";
  const set = {};

  for (const [snake, pascal] of PAIRS) {
    const s = doc[snake];
    const p = doc[pascal];
    if (!isEmpty(s) && isEmpty(p)) set[pascal] = s;
    else if (isEmpty(s) && !isEmpty(p)) set[snake] = p;
  }

  // role/Role siempre en minúsculas del lado Flask
  if (typeof doc.role === "string" && doc.role !== doc.role.toLowerCase()) {
    set.role = doc.role.toLowerCase();
  } else if (isEmpty(doc.role) && typeof doc.Role === "string") {
    set.role = doc.Role.toLowerCase();
  }

  if (Object.keys(set).length === 0) return; // nada que sincronizar -> no re-dispara

  const col = context.services
    .get("mongodb-atlas")
    .db("edf_catalogotablas")
    .collection("users");

  await col.updateOne({ _id: doc._id }, { $set: set });
};
