# Bambu Lab A1: Model Size vs Slicer Settings Master Guide
**Target Printer:** Bambu Lab A1 (0.4 mm Nozzle)  
**Target Filaments:** PLA Basic, PLA Matte, PLA Silk  
**Author:** Antigravity 3D Master Agent

---

## Quick Reference Size Matrix

| Category | Height (Z) | Layer Height | Wall Loops | Infill | Support Style | Brim Required? | Print Speed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Micro / Miniature** | **20 – 50 mm** *(2 – 5 cm)* | **`0.08` – `0.12 mm`** | `2 – 3` | `10 – 15% Gyroid` | **`Tree Slim`** | No (unless base < 1cm) | **Slow** (Outer wall 40-60 mm/s) |
| **Small / Standard** | **50 – 100 mm** *(5 – 10 cm)* | **`0.16 mm`** *(Optimal)* | `3` | `15% Gyroid` | **`Tree Slim`** | **`Outer Brim 5 mm`** | Standard (Outer wall 80-120 mm/s) |
| **Medium / Tall** | **100 – 180 mm** *(10 – 18 cm)* | **`0.16` – `0.20 mm`** | `3 – 4` | `12 – 15% Gyroid` | **`Tree Hybrid`** | **`Outer Brim 6 – 8 mm`** | Normal (Slow down top 20%) |
| **Giant / Max A1** | **180 – 256 mm** *(18 – 25.6 cm)* | **`0.20 mm`** *(Standard)* | `4` | `10 – 12% Gyroid` | **`Tree Strong`** | **`Outer Brim 8 – 10 mm`** | Slow Y-acceleration (4000 mm/s²) |

---

## 1. Category 1: Micro / Miniature (20 mm to 50 mm / 2 cm to 5 cm)
*Examples: 4cm Ayyappan idol, tabletop RPG miniatures, keychains, rings, tiny statues.*

### Recommended Settings:
* **Layer Height:** **`0.08 mm`** (Ultra-fine) or **`0.12 mm`** (High Quality).
* **Wall Loops:** **`2 to 3`** (Walls will form nearly the entire solid object).
* **Infill:** **`10% to 15% Gyroid`**.
* **Support:** 
  * Type: `Tree (auto)`
  * Style: **`Tree Slim`**
  * Top Z Distance: **`0.16 mm`** (PLA Basic) / **`0.20 mm`** (PLA Silk)
  * Branch Diameter: **`1.5 – 2.0 mm`**
* **Cooling:** Minimum layer time **`8 seconds`** (Allows tiny layers to solidify before the next layer is printed).
* **Outer Wall Speed:** **`40 – 60 mm/s`**.

### What happens if you use standard/wrong settings? (Failures):
1. **Broken Hands / Fingers:** If you leave Support Style as `Default`, the tree branches will be thicker than the idol's arms. When snapping off supports, the hands will snap off with them.
2. **Melted / Blobby Face:** Because each layer is tiny, the hot nozzle stays over the face continuously. Without adequate layer cooling time, facial features (eyes, nose) turn into a melted blob.
3. **Nozzle Physical Limit:** Features thinner than **0.4 mm** (the nozzle diameter) simply cannot be printed; Bambu Studio will ignore them unless `Detect thin walls` or Arachne wall generator is active.

---

## 2. Category 2: Small to Standard (50 mm to 100 mm / 5 cm to 10 cm)
*Examples: 10cm full-detail idol (original single_color.stl), desk toys, phone stands.*

### Recommended Settings:
* **Layer Height:** **`0.16 mm Optimal`** (The absolute sweet spot for detail vs time).
* **Wall Loops:** **`3`** (Solid, rigid, prevents infill shadows).
* **Infill:** **`15% Gyroid`**.
* **Support:**
  * Type: `Tree (auto)`
  * Style: **`Tree Slim`**
  * Top Z Distance: **`0.18 mm`**.
* **Brim:** **`Outer brim only (5 mm)`**.
* **Outer Wall Speed:** **`60 – 100 mm/s`** (Keep at 50 mm/s for Silk PLA).

### What happens if you use standard/wrong settings? (Failures):
1. **Grid Infill Collision:** At 10 cm, internal inertia builds up. If infill is set to `Grid`, the nozzle will cross over ridges, make a clicking sound, and knock the print off the bed around layer 300–400.
2. **Bed Detachment on Y-Axis:** At 10 cm height, the back-and-forth movement of the A1 bed creates leverage on the base. If printed **without a Brim**, the model will tip over midway through printing.

---

## 3. Category 3: Medium to Tall (100 mm to 180 mm / 10 cm to 18 cm)
*Examples: Large decorative statues, vases, mechanical brackets, functional enclosures.*

### Recommended Settings:
* **Layer Height:** **`0.16 mm`** (for detailed art) or **`0.20 mm`** (for functional items).
* **Wall Loops:** **`3 to 4`** (Essential for structural rigidity).
* **Infill:** **`12% to 15% Gyroid`** (Higher infill only adds unnecessary weight and print time).
* **Support:**
  * Type: `Tree (auto)`
  * Style: **`Tree Hybrid`** (More stable trunk base for tall reach).
* **Brim:** **`Outer brim only (6 to 8 mm)`** with `0.1 mm` brim-object gap.
* **Orientation Rule:** Always align the longest dimension along the **Y-axis** (front-to-back) to minimize swaying.

### What happens if you use standard/wrong settings? (Failures):
1. **Wobble & Layer Shifting at the Top:** As the model reaches 15 cm, the top sways during rapid Y-axis bed motion. Layers will become wavy or shift by 1–2 mm.
2. **Excessive Print Time & Waste:** Using 25%+ infill on a 15 cm model can add 6+ hours of printing and waste 150g of filament with zero strength advantage.

---

## 4. Category 4: Giant / Max Volume (180 mm to 256 mm / 18 cm to 25.6 cm)
*Examples: Life-sized busts, full-plate architectural prints, large cosplay helmets/props.*

### Recommended Settings:
* **Layer Height:** **`0.20 mm Standard`** (or Variable Layer Height: 0.24mm in torso, 0.12mm in head).
* **Wall Loops:** **`4`** (Critical: 4 walls prevent buckling under model weight).
* **Infill:** **`10% to 12% Gyroid`**.
* **Support:**
  * Type: `Tree (auto)`
  * Style: **`Tree Strong`** or **`Tree Hybrid`** (Supports must withstand violent bed acceleration).
* **Brim:** **`Outer brim 8 to 10 mm`** (Mandatory!).
* **Speed / Acceleration:** Reduce **Default acceleration** from `6000` to **`3500 – 4000 mm/s²`** to prevent severe top-level resonance.

### What happens if you use standard/wrong settings? (Failures):
1. **Catastrophic Bed Ejection:** A 25 cm tall print acting as a 250 mm lever arm will easily peel off the bed under 500 mm/s travel speed unless braced with a wide 8–10 mm brim.
2. **Bottom Corner Warping:** Massive plastic volume cools and shrinks, curling the bottom corners upward off the textured plate.

---

## 5. The 0.4 mm Nozzle Physical Limit (Golden Rule)

Always remember the **"Rule of Multiples"** for your 0.4 mm nozzle:
* **Minimum Wall Thickness:** `0.8 mm` (2 wall passes of 0.4 mm). Anything thinner than 0.8 mm will be fragile like paper.
* **Minimum Feature Resolution:** `0.4 mm`. A feature smaller than 0.4 mm (like a 0.2 mm finger tip on a 3 cm model) cannot physically be extruded by a 0.4 mm hole.
* **Maximum Layer Height:** `0.28 mm` (Never exceed 75% of nozzle diameter; otherwise, layer adhesion fails completely).
* **Minimum Layer Height:** `0.08 mm` (Below 0.08 mm, a 0.2 mm nozzle is required).

