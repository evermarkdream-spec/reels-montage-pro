import { Composition } from "remotion";
import { StudentPreview } from "./student-style";
import { ImportedCompositions } from "./generated/Registry";
import { LocalCompositions } from "./local/Local";
import "./index.css";

// Композиции шаблона. Импортированные ролики живут в src/generated/Registry.tsx
// (его пишет scripts/import-video.py), личные — в src/local/Local.tsx.
// Обе папки не попадают в git, поэтому этот файл правится только вручную.
export const RemotionRoot = () => (
  <>
    <Composition
      id="Style-Preview"
      component={StudentPreview}
      durationInFrames={200}
      fps={25}
      width={1080}
      height={1920}
    />
    <ImportedCompositions />
    <LocalCompositions />
  </>
);
