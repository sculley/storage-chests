// The 17 chest colours: undyed plus the 16 dyes, in Minecraft's dye order.
// Index = the chest entity's "stc:colour" property. Keep in step with COLOURS in tools/render_textures.py.

export const COLOURS = [
  "undyed",
  "white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
  "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black",
];

/** Item id for a chest of the given colour index. */
export const itemFor = (colour) => (colour > 0 ? `stc:${COLOURS[colour]}_storage_chest` : "stc:storage_chest");

/** Every storage chest item id. */
export const CHEST_ITEMS = new Set(COLOURS.map((_, i) => itemFor(i)));

/** Colour index of a storage chest item (0 if it isn't one). */
export function colourOfItem(typeId) {
  return Math.max(0, COLOURS.findIndex((_, i) => itemFor(i) === typeId));
}

// Items that also work as dyes in vanilla.
const OTHER_DYES = {
  "minecraft:ink_sac": "black",
  "minecraft:bone_meal": "white",
  "minecraft:lapis_lazuli": "blue",
  "minecraft:cocoa_beans": "brown",
};

/** Colour a held item would paint a chest, or undefined if it isn't a dye. A water bucket washes it back to undyed. */
export function colourOfDye(typeId) {
  if (typeId === "minecraft:water_bucket") return 0;
  const name = OTHER_DYES[typeId] ?? /^minecraft:(\w+)_dye$/.exec(typeId)?.[1];
  const i = COLOURS.indexOf(name);
  return i > 0 ? i : undefined;
}
