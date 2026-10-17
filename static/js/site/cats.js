// The three cats on the footer line (facet's cast).
// This path mirrors [extra.site].facet in config.toml (modules cannot read config).
import { createCat } from "/vendor/facet/dist/cast/cast.js";

const slot = document.querySelector(".f-footer__cats");
if (slot)
  slot.append(
    createCat("dudu", { label: "" }),
    createCat("nangnang", { label: "" }),
    createCat("duna", { pose: "wave", label: "" }),
  );
