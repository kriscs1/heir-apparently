// What the loading screens say while a world gets ready: one at a time, in a shuffled order, a new one every few
// seconds. The start screen (web/home/index.html) has the same list: tests/test_central.py keeps the two the same.
// (just for fun: never a hint at a quest, never a place or a thing the player hasn't met)
export const SAYINGS = [
  "Herding the sheep back into their pens...",
  "Teaching the chickens to cross the road...",
  "Sweeping the tavern floor...",
  "Waking the blacksmith (gently)...",
  "Reminding the goblins to look menacing...",
  "Hiding the good loot at the bottom of the chest...",
  "Persuading the rats to stay in the cellar...",
  "Tuning the bard's lute (it won't help)...",
  "Laying the map down, one tile at a time...",
  "Putting the ore back in the rocks...",
  "Telling the skeletons to lie still a moment longer...",
  "Fluffing the pillows at the inn...",
  "Feeding the fish so they'll bite later...",
  "Lighting the lanterns...",
  "Checking under the bridges...",
  "Sharpening swords nobody asked to have sharpened...",
  "Settling an argument between two shopkeepers...",
  "Asking the weather what it fancies today...",
  "Rounding up the cows that wandered off...",
  "Convincing the wolves it isn't feeding time...",
  "Stacking the firewood...",
  "Oiling the doors that creak (most of them)...",
  "Counting the coins in the bank, twice...",
  "Untangling the fishing nets...",
  "Asking the guards to stand a little straighter...",
  "Shooing the crows off the crops...",
  "Growing the trees back...",
  "Unrolling the roads...",
  "Sorting the herbs from the weeds...",
  "Dusting the bookshelves nobody reads...",
];

// Shows a saying in el and changes it every few seconds till the returned stop() is called
export function tellSayings(el, ms = 2800) {
  const order = SAYINGS.map((s) => [Math.random(), s]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
  let i = 0;
  const next = () => { el.textContent = order[i++ % order.length]; };
  next();
  const timer = setInterval(next, ms);
  return () => clearInterval(timer);
}
