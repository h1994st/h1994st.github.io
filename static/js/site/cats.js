// The three cats on the footer line (facet's cast).
import { createCat } from "/vendor/facet/dist/cast/cast.js";

const slot = document.querySelector(".f-footer__cats");
if (slot)
  slot.append(
    createCat("dudu", { label: "" }),
    createCat("nangnang", { label: "" }),
    createCat("duna", { pose: "wave", label: "" }),
  );
