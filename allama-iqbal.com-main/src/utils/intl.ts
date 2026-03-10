export const urIntl = new Intl.Locale("ur-PK", {
  language: "ur",
  script: "Aran",
  region: "PK",
  collation: "compat",
  numberingSystem: "arabext",
});

export const urNumberFormat = Intl.NumberFormat(urIntl);
