import { palette, reference01, avatarNov, latestRef } from "./tokens";

// Подложка сцены: ровный фон, слабая сетка и подсветка центра.
//
// Сетка здесь не для красоты. Она задаёт кадру масштаб: по ней глаз видит,
// что объект большой или маленький, далеко или близко. На голом однородном
// фоне этой опоры нет, и любая графика выглядит наклейкой. Подсветка центра
// добавляет глубину и уводит взгляд к середине, где идёт действие.
//
// Требование записано в motion-direction.json → background.grid / centerGlow.

export const Backdrop = ({
  light = false,
  cell = 72,
  warm = false,
  warmGrid = false,
  latest = false,
}: {
  light?: boolean;
  cell?: number;
  warm?: boolean;
  warmGrid?: boolean;
  latest?: boolean;
}) => {
  const c = palette(light);
  if (latest)
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: latestRef.background,
        }}
      />
    );
  if (warm)
    return (
      <>
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: reference01.ground,
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `radial-gradient(ellipse at 26% 34%,${reference01.glow},transparent 38%),radial-gradient(ellipse at 70% 52%,${reference01.softGlow},transparent 35%),radial-gradient(ellipse at 48% 112%,${reference01.glow},transparent 53%)`,
          }}
        />
        {warmGrid ? (
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `linear-gradient(${avatarNov.warmGrid} 1px,transparent 1px),linear-gradient(90deg,${avatarNov.warmGrid} 1px,transparent 1px)`,
              backgroundSize: `${cell}px ${cell}px`,
            }}
          />
        ) : null}
      </>
    );
  return (
    <>
      <div style={{ position: "absolute", inset: 0, background: c.ground }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `linear-gradient(${c.grid} 1px,transparent 1px),linear-gradient(90deg,${c.grid} 1px,transparent 1px)`,
          backgroundSize: `${cell}px ${cell}px`,
          // Сетка гаснет к краям: у кадра остаётся воздух, а не обои в клетку.
          maskImage:
            "radial-gradient(ellipse at 50% 46%,black 22%,transparent 82%)",
          WebkitMaskImage:
            "radial-gradient(ellipse at 50% 46%,black 22%,transparent 82%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: light
            ? "radial-gradient(ellipse at 50% 42%,rgba(255,255,255,.9),transparent 62%)"
            : "radial-gradient(ellipse at 50% 42%,rgba(120,160,215,.09),transparent 62%)",
        }}
      />
    </>
  );
};
