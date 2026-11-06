import { cancelRender, continueRender, delayRender, staticFile } from "remotion";

if (typeof document !== "undefined") {
  const handle = delayRender("Loading Onest and Unbounded");
  Promise.all(
    [["Onest", "onest"], ["Unbounded", "unbounded"]].map(async ([name, file]) => {
      const face = new FontFace(name, `url(${staticFile(`fonts/${file}.ttf`)})`, { weight: "100 900" });
      document.fonts.add(await face.load());
    }),
  ).then(() => continueRender(handle)).catch(cancelRender);
}
