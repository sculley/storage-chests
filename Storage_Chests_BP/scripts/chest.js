// Placing, picking up and dyeing storage chests.
//
// A placed chest is an entity (custom blocks can't hold items), so it opens like a chest minecart.
// When you pick one up, the chest entity is saved into a structure with everything inside it, and the
// structure's name goes on the dropped item. Placing that item puts the structure back. Structures keep
// items exactly, enchantments, names and all.

import { EquipmentSlot, ItemStack, StructureSaveMode, system, world } from "@minecraft/server";
import { CHEST_ITEMS, colourOfDye, colourOfItem, itemFor } from "./colours.js";

export const CHEST = "stc:storage_chest";
const COLOUR = "stc:colour"; // entity property
const CONTENTS = "stc:contents"; // item dynamic property: name of the structure holding its items
const PENDING = "stc:pending"; // entity dynamic property: set while it is being packed or unpacked

const FACE = { Up: [0, 1, 0], Down: [0, -1, 0], North: [0, 0, -1], South: [0, 0, 1], East: [1, 0, 0], West: [-1, 0, 0] };
const busy = new Set();

const isCreative = (player) => String(player.getGameMode()).toLowerCase() === "creative";
const say = (player, text) => player.onScreenDisplay.setActionBar(text);
const floor = (v) => ({ x: Math.floor(v.x), y: Math.floor(v.y), z: Math.floor(v.z) });
const centre = (cell) => ({ x: cell.x + 0.5, y: cell.y, z: cell.z + 0.5 });
const newId = () => `stc:c${Date.now().toString(36)}${Math.floor(Math.random() * 36 ** 6).toString(36)}`;

/** Entities other than dropped items and XP whose position is inside a block cell. */
function entitiesIn(dimension, cell) {
  return dimension
    .getEntities({ location: cell, volume: { x: 0.99, y: 0.99, z: 0.99 } })
    .filter((e) => e.typeId !== "minecraft:item" && e.typeId !== "minecraft:xp_orb");
}

/** Remove one of the item the player is holding (not in Creative). */
function useUpHeld(player, typeId) {
  if (isCreative(player)) return;
  const equipment = player.getComponent("minecraft:equippable");
  const held = equipment?.getEquipment(EquipmentSlot.Mainhand);
  if (!held || held.typeId !== typeId) return;
  if (held.amount > 1) {
    held.amount -= 1;
    equipment.setEquipment(EquipmentSlot.Mainhand, held);
  } else {
    equipment.setEquipment(EquipmentSlot.Mainhand, undefined);
  }
}

/** Turn a chest to face the player, centre it in its block and paint it. */
function settle(chest, cell, player, colour) {
  const yaw = Math.round(player.getRotation().y / 90) * 90 + 180;
  chest.teleport(centre(cell), { rotation: { x: 0, y: yaw } });
  chest.setProperty(COLOUR, colour);
  chest.setDynamicProperty(PENDING, undefined);
}

/** Place a storage chest item against the block face the player used it on. */
export function place(player, block, blockFace, item) {
  const [dx, dy, dz] = FACE[blockFace] ?? [0, 1, 0];
  const cell = { x: block.location.x + dx, y: block.location.y + dy, z: block.location.z + dz };
  const dimension = block.dimension;

  let target;
  try {
    target = dimension.getBlock(cell);
  } catch {} // outside the world
  if (!target || !(target.isAir || target.isLiquid) || entitiesIn(dimension, cell).length) {
    return say(player, "§cThere's no room for a storage chest there.");
  }

  const colour = colourOfItem(item.typeId);
  const id = item.getDynamicProperty(CONTENTS);

  if (typeof id === "string" && world.structureManager.get(id)) {
    try {
      world.structureManager.place(id, dimension, cell, { includeBlocks: false, includeEntities: true });
    } catch (error) {
      // Keep the item (and so the structure) if the chest couldn't be put back.
      console.warn(`[Storage Chests] couldn't unpack a chest: ${error}`);
      return say(player, "§cThat storage chest couldn't be placed there. Try somewhere else.");
    }
    world.structureManager.delete(id);
    useUpHeld(player, item.typeId);
    dimension.playSound("dig.stone", centre(cell));
    // The unpacked entity can take a tick to appear; find it by the name it was packed under.
    system.run(() => {
      const chest = dimension
        .getEntities({ type: CHEST, location: centre(cell), maxDistance: 3 })
        .find((e) => e.getDynamicProperty(PENDING) === id);
      if (chest) settle(chest, cell, player, colour);
    });
    return;
  }
  if (typeof id === "string") say(player, "§eThis chest's contents couldn't be found, so it's empty.");
  useUpHeld(player, item.typeId);
  dimension.playSound("dig.stone", centre(cell));
  settle(dimension.spawnEntity(CHEST, centre(cell)), cell, player, colour);
}

/** Hit a placed chest: it drops as an item with everything still inside. */
export function pickUp(player, chest) {
  if (busy.has(chest.id)) return;
  const container = chest.getComponent("minecraft:inventory")?.container;
  if (!container) return;
  busy.add(chest.id);

  const dimension = chest.dimension;
  const cell = floor(chest.location);
  const dropAt = centre(cell);
  const item = new ItemStack(itemFor(chest.getProperty(COLOUR) ?? 0), 1);

  // A storage chest can't be carried inside another one: those come out first.
  let stacks = 0;
  for (let slot = 0; slot < container.size; slot++) {
    const stack = container.getItem(slot);
    if (!stack) continue;
    if (CHEST_ITEMS.has(stack.typeId)) {
      container.setItem(slot, undefined);
      dimension.spawnItem(stack, dropAt);
    } else {
      stacks++;
    }
  }

  const finish = () => {
    busy.delete(chest.id);
    if (!chest.isValid) return;
    if (stacks > 0) {
      const id = newId();
      chest.setDynamicProperty(PENDING, id);
      const here = floor(chest.location);
      try {
        world.structureManager.createFromWorld(id, dimension, here, here, {
          includeBlocks: false,
          includeEntities: true,
          saveMode: StructureSaveMode.World,
        });
      } catch (error) {
        // Never remove a chest whose items weren't saved.
        chest.setDynamicProperty(PENDING, undefined);
        chest.teleport(dropAt);
        console.warn(`[Storage Chests] couldn't pack a chest: ${error}`);
        return say(player, "§cThat storage chest couldn't be picked up. Try again.");
      }
      item.setDynamicProperty(CONTENTS, id);
      item.setLore([`§7${stacks} stack${stacks === 1 ? "" : "s"} inside`]);
    }
    chest.remove();
    dimension.playSound("random.pop", dropAt);
    // Like a shulker box, an empty chest broken in Creative doesn't drop.
    if (stacks > 0 || !isCreative(player)) dimension.spawnItem(item, dropAt);
  };

  // The structure takes everything in the chest's block, so anything else standing in it would be
  // copied. In that rare case, lift the chest to the empty top of the world for a tick and pack it there.
  if (stacks > 0 && entitiesIn(dimension, cell).some((e) => e.id !== chest.id)) {
    chest.teleport({ x: dropAt.x, y: dimension.heightRange.max - 2, z: dropAt.z });
    system.runTimeout(finish, 1);
  } else {
    finish();
  }
}

/** Use a dye (or a water bucket) on a placed chest. Returns true if the item was a dye. */
export function dye(player, chest, item) {
  const colour = colourOfDye(item.typeId);
  if (colour === undefined) return false;
  system.run(() => {
    if (!chest.isValid || chest.getProperty(COLOUR) === colour) return;
    chest.setProperty(COLOUR, colour);
    chest.dimension.playSound("dig.cloth", chest.location);
    if (item.typeId !== "minecraft:water_bucket") useUpHeld(player, item.typeId);
  });
  return true;
}
