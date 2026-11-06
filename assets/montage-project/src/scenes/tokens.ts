// Единственный источник цвета, размера и формы для сцен.
//
// Правило простое: в сцене нет ни одного числа и ни одного цвета «на глаз».
// Всё берётся отсюда. Так кадры одного ролика выглядят одной работой, а не
// набором случайных прямоугольников, и правка вкуса делается в одном файле.
//
// Цветовая политика — три уровня, больше нет:
//   1. Подложка и поверхности — нейтральные, почти без насыщенности.
//   2. Текст — три ступени контраста: главное, пояснение, служебное.
//   3. Акцент — ОДИН на ролик, и только на том объекте, о котором идёт речь
//      прямо сейчас. Как только акцентных пятен два, кадр перестаёт вести взгляд.
// Красный и зелёный — не украшение: только «нельзя» и «получилось».

export const dark = {
  ground: "#0b0c0e",
  surface: "rgba(255,255,255,.055)",
  surfaceSolid: "#15171b",
  line: "rgba(255,255,255,.09)",
  lineStrong: "rgba(255,255,255,.16)",
  grid: "rgba(180,200,227,.07)",
  text: "#f2f4f7",
  textSoft: "rgba(242,244,247,.56)",
  textMuted: "rgba(242,244,247,.32)",
} as const;

export const light = {
  ground: "#f4f5f7",
  surface: "rgba(16,22,32,.04)",
  surfaceSolid: "#ffffff",
  line: "rgba(16,22,32,.1)",
  lineStrong: "rgba(16,22,32,.18)",
  grid: "rgba(68,101,139,.1)",
  text: "#10151d",
  textSoft: "rgba(16,21,29,.6)",
  textMuted: "rgba(16,21,29,.38)",
} as const;

/** Акцент один на ролик. Остальные — только по смыслу, не для красоты. */
export const accent = "#2d8cff";
export const positive = "#35c66b";
export const negative = "#ff4d6d";

/** User-selected competitor-01 adaptation; opt-in, old compositions unchanged. */
export const reference01 = {
  accent: "#ff6b32",
  ground: "#0d0b08",
  panel: "#292725",
  cream: "#f7f5ee",
  ink: "#141311",
  line: "rgba(255,255,255,.24)",
  glow: "rgba(212,70,23,.24)",
  softGlow: "rgba(238,174,104,.13)",
  font: "Montserrat",
  panelFill:
    "linear-gradient(165deg,rgba(255,255,255,.16),rgba(255,255,255,.045))",
  shadow: "0 20px 60px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.18)",
  textShadow: "0 3px 8px rgba(0,0,0,.65)",
} as const;

export const palette = (isLight = false) => (isLight ? light : dark);

/** Explicit full restyle, latest three references, 2026-11-03. Opt-in only. */
export const latestRef = {
  paper: "#fffef8",
  ink: "#16151b",
  white: "#ffffff",
  muted: "#777480",
  lime: "#beff59",
  purple: "#8854da",
  lilac: "#eee5ff",
  pink: "#f8e1ed",
  line: "#ddd9e4",
  shadow: "0 18px 38px rgba(42,20,65,.17)",
  captionShadow: "0 3px 5px rgba(0,0,0,.7)",
  splitCaptionShadow: "0 2px 2px rgba(0,0,0,.85), 0 4px 8px rgba(0,0,0,.4)",
  splitCaptionStroke: "1.5px #16151b",
  background:
    "radial-gradient(ellipse at 85% 32%,#eee5ff 0,transparent 65%),radial-gradient(ellipse at 70% 100%,#f8e1ed 0,transparent 65%),#fffef8",
  titleFont: "Unbounded",
  font: "Onest",
  titleSize: 48,
  bodySize: 32,
  labelSize: 25,
  radius: 28,
} as const;

/** November graphics revision: distinct paper objects on the existing warm stage. */
export const avatarNov = {
  paper: "#f7f5ee",
  ink: "#25221e",
  paperLine: "rgba(37,34,30,.14)",
  paperMuted: "rgba(37,34,30,.42)",
  selected: "rgba(255,107,50,.18)",
  warmGrid: "rgba(247,245,238,.045)",
  paperShadow: "0 20px 42px rgba(0,0,0,.40)",
  width: 888,
  height: 800,
  smallType: 24,
  bodyType: 30,
  titleType: 40,
  largeType: 56,
  cardRadius: 22,
} as const;

/** Шаг сетки: отступы и размеры берутся отсюда, промежуточных значений нет. */
export const step = [4, 8, 12, 16, 24, 32, 48, 64, 96, 128] as const;

export const radius = { small: 14, card: 24, panel: 32, round: 999 } as const;

/** Толщина обводки иконок на сетке 24 px — одна на весь проект. */
export const stroke = 1.75;

export const type = {
  caption: { fontSize: 26, fontWeight: 500, letterSpacing: "0.01em" },
  label: { fontSize: 34, fontWeight: 500, letterSpacing: "-0.005em" },
  title: { fontSize: 46, fontWeight: 600, letterSpacing: "-0.015em" },
  headline: { fontSize: 64, fontWeight: 600, letterSpacing: "-0.02em" },
} as const;

/** Две ступени глубины: поверхность и то, что над ней. Третьей нет. */
export const shadow = {
  flat: "inset 0 1px 0 rgba(255,255,255,.07)",
  raised: "inset 0 1px 0 rgba(255,255,255,.09), 0 24px 60px rgba(0,0,0,.5)",
} as const;

export const card = (isLight = false, raised = false) => {
  const c = palette(isLight);
  return {
    background: c.surface,
    border: `1px solid ${c.line}`,
    borderRadius: radius.card,
    boxShadow: raised ? shadow.raised : shadow.flat,
  } as const;
};
