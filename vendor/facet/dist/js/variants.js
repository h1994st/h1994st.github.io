// Variants: a [data-f-variants="look"] control switches every [data-f-variant="look:x"] element
// inside the control's parent (its scope). It comes in two forms.
// - Radios (recommended; works without JS): <div class="f-segmented" role="radiogroup"
//   aria-label="Look" data-f-variants="look"> holding <label><input type="radio" name="look"
//   value="x" checked />X</label> options. With CSS alone (variants.css) the checked radio's
//   position picks the variant at the same position among its siblings. This module takes over and
//   matches each radio's value to the variant's value instead, which also tells apart two controls
//   in one parent.
// - Buttons (JS only): the control ships hidden and holds <button data-variant="x" aria-pressed>
//   options, and the non-default variants ship hidden, so without JS the first variant shows and
//   there are no dead buttons. This module shows the control and keeps aria-pressed in sync.
// The pressed button or checked radio (else the first option) picks the variant; elements of other
// groups are never touched (data-f-variant is split on its last colon, so group "a" and group "a:b"
// are distinct). A control this module manages gets data-f-variants-live, which turns the CSS off.
// Edge cases: an element whose value has no option stays hidden; a control with no options is
// skipped and left as is; variants added after init are not picked up (call init again). Cleanup
// restores the control's hidden state, the options' pressed or checked state and the variants'
// hidden state, and removes data-f-variants-live, so the CSS takes over again.
const done = new WeakSet();
const OPTION = 'button[data-variant], input[type="radio"]';
const isRadio = (o) => o.matches('input[type="radio"]');
const valueOf = (o) => (isRadio(o) ? o.value : o.dataset.variant);
const isOn = (o) => (isRadio(o) ? o.checked : o.getAttribute("aria-pressed") === "true");

export function init(root = document) {
  const off = [];
  for (const control of root.querySelectorAll("[data-f-variants]")) {
    if (done.has(control) || !control.parentElement) continue;
    const group = control.dataset.fVariants;
    const scope = control.parentElement;
    const options = [...control.querySelectorAll(OPTION)];
    if (!group || !options.length) continue;
    done.add(control);
    const parse = (el) => {
      const s = el.dataset.fVariant;
      const i = s.lastIndexOf(":");
      return { group: s.slice(0, i), value: s.slice(i + 1) };
    };
    const targets = [...scope.querySelectorAll("[data-f-variant]")].filter(
      (el) => parse(el).group === group,
    );
    const initial = targets.map((el) => [el, el.hidden]);
    const was = options.map((o) => (isRadio(o) ? o.checked : o.getAttribute("aria-pressed")));
    const wasHidden = control.hidden;
    const select = (value) => {
      for (const o of options) {
        if (isRadio(o)) o.checked = o.value === value;
        else o.setAttribute("aria-pressed", String(o.dataset.variant === value));
      }
      for (const el of targets) el.hidden = parse(el).value !== value;
    };
    control.setAttribute("data-f-variants-live", "");
    select(valueOf(options.find(isOn) || options[0]));
    control.hidden = false;
    // Buttons answer click; radios answer change, which also covers arrow keys.
    const onPick = (e) => {
      const o = e.target.closest?.(OPTION);
      if (o && control.contains(o) && e.type === (isRadio(o) ? "change" : "click")) {
        select(valueOf(o));
      }
    };
    control.addEventListener("click", onPick);
    control.addEventListener("change", onPick);
    off.push(() => {
      control.removeEventListener("click", onPick);
      control.removeEventListener("change", onPick);
      control.removeAttribute("data-f-variants-live");
      control.hidden = wasHidden;
      for (const [el, h] of initial) el.hidden = h;
      options.forEach((o, i) => {
        if (isRadio(o)) o.checked = was[i];
        else if (was[i] === null) o.removeAttribute("aria-pressed");
        else o.setAttribute("aria-pressed", was[i]);
      });
      done.delete(control);
    });
  }
  return () => off.forEach((f) => f());
}
