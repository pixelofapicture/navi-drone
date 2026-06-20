// Navi Drone visual identity: a dim cockpit-HUD feel - deep navy field,
// a single scanner-teal accent for "recognized", warm coral for "unknown/alert".
export const colors = {
  bg: "#0A0F1C",
  surface: "#121A2B",
  surfaceRaised: "#182238",
  border: "#22304A",
  textPrimary: "#E9EEF9",
  textSecondary: "#7C8AA8",
  accent: "#22E5C9",      // recognized / online / signature color
  accentDim: "#0F4A44",
  alert: "#FF6B57",       // unknown face / offline
  alertDim: "#4A211C",
};

export const type = {
  label: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.5,
    color: colors.textSecondary,
    textTransform: "uppercase",
  },
  h1: {
    fontSize: 26,
    fontWeight: "800",
    color: colors.textPrimary,
    letterSpacing: 0.3,
  },
  h2: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.textPrimary,
  },
  mono: {
    fontFamily: "monospace",
    color: colors.textPrimary,
  },
  body: {
    fontSize: 14,
    color: colors.textPrimary,
  },
  caption: {
    fontSize: 12,
    color: colors.textSecondary,
  },
};
