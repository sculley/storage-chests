// Storage Chests - entry point. Wires custom components and events to the chest and guide.

import { system, world } from "@minecraft/server";
import { CHEST, DEFAULT_NAME, dye, pickUp, place } from "./chest.js";
import { giveGuideOnce, openGuide } from "./guide.js";

// Holding the use button fires repeatedly; ignore repeats within a few ticks.
const lastUse = new Map();
function isRepeat(player) {
  const now = system.currentTick;
  const repeat = now - (lastUse.get(player.id) ?? -100) < 8;
  lastUse.set(player.id, now);
  return repeat;
}

system.beforeEvents.startup.subscribe(({ itemComponentRegistry }) => {
  itemComponentRegistry.registerCustomComponent("stc:storage_chest", {
    onUseOn({ source, block, blockFace, itemStack }) {
      if (!source || source.typeId !== "minecraft:player" || isRepeat(source)) return;
      system.run(() => place(source, block, blockFace, itemStack));
    },
  });
  itemComponentRegistry.registerCustomComponent("stc:guide", {
    onUse({ source }) {
      if (!isRepeat(source)) openGuide(source);
    },
  });
});

// Using a dye or water bucket on a placed chest colours it instead of opening it.
world.beforeEvents.playerInteractWithEntity.subscribe((e) => {
  if (e.target.typeId !== CHEST) return;
  if (e.itemStack && dye(e.player, e.target, e.itemStack)) {
    e.cancel = true;
    return;
  }
  // Chests placed with version 1.0.0 have no name tag, so their screen says "Unknown". Name them now
  // and open the screen a tick later, once the name has arrived.
  if (!e.target.nameTag) {
    e.cancel = true;
    const chest = e.target;
    system.run(() => {
      if (chest.isValid) chest.nameTag = DEFAULT_NAME;
    });
  }
});

// Name 1.0.0 chests as soon as they load, so most never show "Unknown".
world.afterEvents.entityLoad.subscribe(({ entity }) => {
  if (entity.typeId === CHEST && !entity.nameTag) entity.nameTag = DEFAULT_NAME;
});

// One hit picks a chest up.
world.afterEvents.entityHitEntity.subscribe(({ damagingEntity, hitEntity }) => {
  if (hitEntity.typeId === CHEST && damagingEntity.typeId === "minecraft:player") pickUp(damagingEntity, hitEntity);
});

// Give the guide a moment after joining — in a brand-new world the inventory isn't ready at spawn.
world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
  if (initialSpawn) system.runTimeout(() => giveGuideOnce(player), 40);
});
// Catch the host, whose spawn can happen before scripts finish loading.
world.afterEvents.worldLoad.subscribe(() => {
  system.runTimeout(() => world.getAllPlayers().forEach((p) => giveGuideOnce(p)), 40);
});

world.afterEvents.playerLeave.subscribe(({ playerId }) => lastUse.delete(playerId));
