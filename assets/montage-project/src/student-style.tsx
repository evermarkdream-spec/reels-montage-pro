import React from "react";
import {
  AbsoluteFill,
  Interactive,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FileText, Film, Check } from "lucide-react";
import { latestRef as r } from "./scenes/tokens";
import "./student-fonts";

export const SceneCanvas = ({ children }: { children: React.ReactNode }) => (
  <div
    style={{
      position: "relative",
      width: 888,
      height: 800,
      fontFamily: r.font,
      color: r.ink,
    }}
  >
    {children}
  </div>
);

export const Paper = ({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      background: r.white,
      border: `1px solid ${r.line}`,
      borderRadius: r.radius,
      boxShadow: r.shadow,
      padding: 32,
      boxSizing: "border-box",
      ...style,
    }}
  >
    {children}
  </div>
);

export const appear = (seconds: number, start: number, duration = 0.4) => {
  const p = interpolate(seconds, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return {
    opacity: p,
    transform: `translateY(${24 * (1 - p)}px) scale(${0.92 + 0.08 * p})`,
  };
};

const DepthTitle = ({
  children,
  color,
  size,
}: {
  children: React.ReactNode;
  color: string;
  size: number;
}) => (
  <div
    style={{
      position: "relative",
      fontFamily: r.titleFont,
      fontWeight: 900,
      fontSize: size,
      lineHeight: 1.08,
      letterSpacing: -3,
      wordSpacing: 8,
      overflowWrap: "anywhere",
      transformStyle: "preserve-3d",
    }}
  >
    {Array.from({ length: 12 }, (_, i) => {
      const z = 12 - i;
      return (
        <div
          key={i}
          aria-hidden
          style={{
            position: "absolute",
            inset: 0,
            color: z > 6 ? "#58378f" : "#8052bc",
            transform: `translate3d(${z * 0.32}px,${z * 0.55}px,${-z}px)`,
          }}
        >
          {children}
        </div>
      );
    })}
    <div
      style={{
        position: "relative",
        color,
        transform: "translateZ(1px)",
        textShadow: `0 -1px 0 ${r.white}`,
      }}
    >
      {children}
    </div>
  </div>
);

export const ReelHook = ({
  text,
  accent = "",
  kicker = "",
  durationSeconds = 4.12,
}: {
  text: string;
  accent?: string;
  kicker?: string;
  durationSeconds?: number;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame >= durationSeconds * fps) return null;
  const t = frame / fps;
  return (
    <Interactive.Div
      name="Хук • объёмный редактируемый заголовок"
      from={0}
      durationInFrames={Math.round(durationSeconds * fps)}
      style={{
        position: "absolute",
        zIndex: 4,
        top: 235,
        left: 96,
        width: 888,
        textAlign: "center",
        perspective: 1300,
        perspectiveOrigin: "540px 380px",
        filter: "drop-shadow(0 18px 20px rgba(0,0,0,.38))",
        ...appear(t, 0, 0.65),
      }}
    >
      {kicker ? (
        <div
          style={{
            fontFamily: r.font,
            fontSize: 27,
            letterSpacing: 3,
            fontWeight: 700,
            color: r.white,
            marginBottom: 14,
          }}
        >
          {kicker}
        </div>
      ) : null}
      <DepthTitle color={r.white} size={82}>
        {text}
      </DepthTitle>
      {accent ? (
        <div style={{ marginTop: 4 }}>
          <DepthTitle color={r.lime} size={112}>
            {accent}
          </DepthTitle>
        </div>
      ) : null}
    </Interactive.Div>
  );
};

// Demonstrates the visual language without using the author's face, voice or results.
export const StudentPreview = () => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const selected = t > 3;
  return (
    <AbsoluteFill
      style={{
        background: r.background,
        fontFamily: r.font,
        color: r.ink,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 300,
          width: 900,
          textAlign: "center",
          fontFamily: r.titleFont,
          fontWeight: 900,
          fontSize: 74,
        }}
      >
        ВАША МЫСЛЬ
        <br />
        <span style={{ background: r.lime }}>СТАНОВИТСЯ СЦЕНОЙ</span>
      </div>
      <Paper
        style={{
          width: 760,
          height: 440,
          position: "relative",
          ...appear(t, 0.3),
        }}
      >
        <FileText
          size={110}
          style={{
            color: r.purple,
            position: "absolute",
            left: 60,
            top: 70,
            ...appear(t, 0.8),
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 210,
            top: 90,
            fontSize: 44,
            fontWeight: 700,
          }}
        >
          Исходное видео
        </div>
        <div
          style={{
            position: "absolute",
            top: 235,
            left: 60,
            width: 620,
            height: 22,
            borderRadius: 12,
            background: r.lilac,
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${interpolate(t, [1.3, 3], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}%`,
              background: r.purple,
              borderRadius: 12,
            }}
          />
        </div>
        {selected ? (
          <div
            style={{
              position: "absolute",
              left: 70,
              top: 300,
              display: "flex",
              alignItems: "center",
              gap: 20,
              fontSize: 38,
              fontWeight: 700,
              ...appear(t, 3),
            }}
          >
            <Film size={56} />
            <span>Монтаж и субтитры</span>
            <Check color={r.purple} size={48} />
          </div>
        ) : null}
      </Paper>
      <div
        style={{
          position: "absolute",
          top: 1420,
          fontSize: 64,
          fontWeight: 700,
        }}
      >
        ПРЕДМЕТ → ДЕЙСТВИЕ → РЕЗУЛЬТАТ
      </div>
    </AbsoluteFill>
  );
};
