// The Storage Chests Guide: a chaptered book opened by using it, given once to every player.

import { ItemStack, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

export const GUIDE = "stc:guide";
const GIVEN = "stc:got_guide";

const CHAPTERS = [
  {
    title: "Storage chests",
    icon: "textures/items/stc_undyed_storage_chest",
    body: [
      "A §6Storage Chest§r holds §a27 stacks§r, like a chest or a shulker box.",
      "",
      "The difference: when you pick it up, §aeverything inside comes with it§r. Carry a whole chest of ores home from a mine, or move your storage room without emptying it.",
      "",
      "No trip to the End needed - it's made from a chest and two iron ingots.",
    ],
  },
  {
    title: "Placing and opening",
    icon: "textures/items/stc_yellow_storage_chest",
    body: [
      "§lPlace:§r hold the chest and use it on a block, like placing any block.",
      "§lOpen:§r use the placed chest.",
      "   PS5 / controller: L2.   PC: right-click.   Touch: tap it.",
      "",
      "You can stand on top of a storage chest, and it doesn't burn or blow up.",
    ],
  },
  {
    title: "Picking it up",
    icon: "textures/items/stc_blue_storage_chest",
    body: [
      "§lHit§r the placed chest once and it drops as an item, with its items still inside.",
      "",
      "The item's description shows how many stacks it's holding. Place it again and everything is exactly where you left it - enchantments, names and all.",
      "",
      "A storage chest can't be carried inside another storage chest. If you pick one up with another inside, the inner one pops out.",
    ],
  },
  {
    title: "Dyeing",
    icon: "textures/items/stc_red_storage_chest",
    body: [
      "Hold any §ldye§r and use it on a placed chest to colour it. Ink sacs, bone meal, lapis and cocoa beans work too.",
      "",
      "Use a §lwater bucket§r on it to wash the colour off. The water isn't used up.",
      "",
      "The colour stays when you pick the chest up. Colour-code your storage: one colour for ores, one for food, one for building blocks.",
      "",
      "Dye the chest when it's placed, not in the crafting grid.",
    ],
  },
  {
    title: "Crafting recipes",
    icon: "textures/items/stc_green_storage_chest",
    body: [
      "Use a crafting table. Top row first:",
      "",
      "§lStorage Chest§r",
      "§7    -      ·§f Iron Ingot§7 ·     -",
      "§7    -      ·§6   Chest   §7 ·     -",
      "§7    -      ·§f Iron Ingot§7 ·     -§r",
      "",
      "§lStorage Chests Guide§r",
      "Book + Chest, in any slots.",
      "",
      "Everything is also in the creative inventory.",
    ],
  },
  {
    title: "Good to know",
    icon: "textures/items/stc_guide",
    body: [
      "• Hoppers and comparators don't connect to storage chests.",
      "• An empty chest broken in Creative doesn't drop, like a shulker box.",
      "• If a chest item is lost (burnt, despawned), its items are lost too - keep it safe like a shulker box.",
      "• Lost this book? Craft another from a Book and a Chest.",
    ],
  },
];

export async function openGuide(player, page) {
  if (page === undefined) {
    const menu = new ActionFormData()
      .title("Storage Chests")
      .body("Chests you can pick up with everything inside.\nPick a chapter:");
    for (const c of CHAPTERS) menu.button(c.title, c.icon);
    const r = await menu.show(player);
    if (r.canceled || r.selection === undefined) return;
    return openGuide(player, r.selection);
  }

  const chapter = CHAPTERS[page];
  const form = new ActionFormData().title(chapter.title).body(chapter.body.join("\n"));
  const hasNext = page + 1 < CHAPTERS.length;
  form.button("< Contents");
  if (hasNext) form.button(`Next: ${CHAPTERS[page + 1].title} >`);
  const r = await form.show(player);
  if (r.canceled || r.selection === undefined) return;
  return openGuide(player, r.selection === 0 ? undefined : page + 1);
}

/** Give the guide once per player, the first time they join with the add-on. */
// Retries until the player's inventory is ready; only marks the gift as given once it lands.
export function giveGuideOnce(player, attempt = 0) {
  if (!player.isValid || player.getDynamicProperty(GIVEN)) return;
  const container = player.getComponent("minecraft:inventory")?.container;
  if (!container) {
    if (attempt < 10) system.runTimeout(() => giveGuideOnce(player, attempt + 1), 20);
    return;
  }
  const leftover = container.addItem(new ItemStack(GUIDE, 1));
  if (leftover) player.dimension.spawnItem(leftover, player.location);
  player.setDynamicProperty(GIVEN, true);
  player.sendMessage("§6Storage Chests:§r you've been given a guide book. Use it to learn how storage chests work.");
}
