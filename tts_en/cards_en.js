// Sweet Dreams, Little Pigs! — English Card & House Rule Data for TTS
// Mechanically identical to sim/cards.js.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PigCards = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  const SERIES = {
    start:  { name: 'Starter', icon: '🌾', color: '#c9b48a' },
    staple: { name: 'Staple',  icon: '🍏', color: '#9bc46a' },
    eat:    { name: 'Feast',   icon: '🍎', color: '#f0563a', res: 'Draw 🃏×1 first' },
    push:   { name: 'Bump',    icon: '🐷', color: '#f29a2e', res: 'Bonus 🐾×1' },
    sleep:  { name: 'Snooze',  icon: '💤', color: '#3c5bd9', res: '+☁️×1 & 🛏️×1' },
    pal:    { name: 'Cuddle',  icon: '🌀', color: '#c43c8a', res: 'Bonus 💤×1' },
  };

  const C = (key, name, series, cost, cloud, steps, text, flavor, extra) =>
    Object.assign(
      {
        key,
        name,
        series,
        cost,
        cloud,
        dreamCloud: (series === 'start' || series === 'staple' || cost <= 2) ? 1 : 2,
        steps,
        text,
        flavor,
        hooks: {},
      },
      extra || {}
    );

  const CARDS = {
    // Starter Cards
    yawn:    C('yawn',    'Big Yawn',      'start',  0, 1, [], ['No board action'].join(''), 'Mouth wide open, eyelids already losing the fight.'),
    shift:   C('shift',   'Scoot Over',    'start',  0, 0, ['walk', 'sleep'], '🐾×1 ➔ 💤×1', 'The floor is chilly—wiggle closer to the rug.'),
    squeeze: C('squeeze', 'Squeeze In',    'start',  0, 0, ['walk', 'push'],  '🐾×1 ➔ 💥×1', 'Only so much rug to go around—belly-bump your neighbor!'),

    // Staple Supply Card
    apple:   C('apple',   'Bedtime Apple', 'staple', 2, 1, ['draw', 'walk', 'trash'], '🃏×1 ➔ 🐾×1 ➔ 🔥×1', 'A crisp apple and a short stroll before bed.'),

    // Feast Series
    melon:    C('melon',    'Half a Melon',   'eat', 3, 0, ['draw', 'walk', 'sleep'], '🃏×1 ➔ 🐾×1 ➔ 💤×1', 'Scoop it clean—a round belly makes a great pillow.'),
    corn:     C('corn',     'Count Kernels',  'eat', 4, 0, ['draw', 'draw', 'walk', 'trash'], '🃏×2 ➔ 🐾×1 ➔ 🔥×1', 'Meant to count kernels to sleep, got hungry instead.', { dreamCloud: 1 }),
    midnight: C('midnight', 'Midnight Feast', 'eat', 5, 0, ['draw', 'draw', 'walk', 'push', 'sleep'], '🃏×2 ➔ 🐾×1 ➔ 💥×1 ➔ 💤×1', 'Smelled stew at midnight—nobody can block this pig!', { dreamCloud: 1 }),
    core:     C('core',     'Apple Core',     'eat', 4, 0, ['draw', 'trash', 'sleep'], '🃏×1 ➔ 🔥×1 ➔ 💤×1; if you Digested a Starter this turn, +⭐×1', 'Nibbled clean to the core—even dreams feel lighter.', { hooks: { trashStar: 1 } }),
    pumpkin:  C('pumpkin',  'Giant Pumpkin',  'eat', 6, 0, ['draw', 'walk', 'push', 'sleep'], '🃏×1 ➔ 🐾×1 ➔ 💥×1 ➔ 💤×1; if all 3 of your pigs are on Rug, +⭐×1', 'Three little pigs around a sweet autumn prize.', { hooks: { pumpkin: 1 } }),

    // Bump Series
    dash:     C('dash',     'Running Start',  'push', 3, 1, ['walk', 'push'], '🐾×1 ➔ 💥×1; if pushed to Floor, draw 🃏×1', 'Just one step back, yet it feels like a 100m sprint.', { hooks: { runDraw: 1 } }),
    overhill: C('overhill', 'Chain Bump',     'push', 3, 0, ['walk', 'linepush', 'sleep'], '🐾×1 ➔ Line Bump* ➔ 💤×1\n*Push the last pig in a row 1 tile away', 'Belly to belly—bump one end, launch the other!'),
    shoo:     C('shoo',     'Shoo Off Bed',   'push', 4, 0, ['walk', 'push', 'draw'], '🐾×1 ➔ 💥×1 ➔ 🃏×1; +☁️×1 per enemy pig on Floor', 'Cold breeze on the floor, loud snores on the rug.', { hooks: { oppFloorCloud: 1 } }),
    excuse:   C('excuse',   'Excuse Me!',     'push', 5, 0, ['walk', 'rowpush'], '🐾×1 ➔ Row Push*\n*Push 1–2 pigs in a line 1 tile & step in', 'Polite words, bulldozer body.'),
    quilt:    C('quilt',    'Pull the Quilt', 'push', 6, 0, ['walk', 'unblanket', 'push', 'sleep'], '🐾×1 ➔ Strip 1 enemy 🛏️ ➔ 💥×1 ➔ 💤×1; wake enemy on Floor: +⭐×1', 'Shove them off the bed, claim the warm spot!', { hooks: { blanketStar: 1 } }),

    // Snooze Series
    pillow:    C('pillow',    'Hit the Pillow', 'sleep', 2, 1, ['walk', 'sleep'], '🐾×1 ➔ 💤×1; if your pig sleeps on Pillow, +☁️×1', 'Head hits the pillow—snooze bubbles in three seconds.', { hooks: { pillowCloud: 1 } }),
    tuck:      C('tuck',      'Tuck In',        'sleep', 2, 1, ['walk', 'sleep', 'blanket'], '🐾×1 ➔ 💤×1 ➔ 🛏️*\n*1 sleeping pig cannot be moved until Wake', 'Tucked in tight—nobody can budge you now.'),
    sleepwalk: C('sleepwalk', 'Sleepwalk',      'sleep', 5, 0, ['sleep', 'sleepwalk'], '💤×1 ➔ Sleepwalk 1*\n*Move any 1 sleeping pig to an adj. empty tile', 'Rolled over with eyes shut, nudged someone off.'),
    train:     C('train',     'Snore Train',    'sleep', 4, 0, ['sleep', 'quake'], '💤×1 ➔ Whistle Quake*\n*Pick your sleeping pig; push all adj. pigs 1 tile', 'Snores rolling like a choo-choo through the room!'),
    hibernate: C('hibernate', 'Hibernate',      'sleep', 4, 2, ['walk', 'sleep', 'sleep'], '🐾×1 ➔ 💤×2', "Pigs don't hibernate—unless the rug is this cozy."),

    // Cuddle Series
    hum:      C('hum',      'Lullaby Hum',    'pal', 2, 1, ['lure', 'walk', 'sleep'], 'Lure* ➔ 🐾×1 ➔ 💤×1\n*Move 1 awake enemy pig to an adj. empty tile', 'Hum a sweet tune to lure blockers off the warm rug.'),
    tail:     C('tail',     'Hook a Tail',    'pal', 4, 0, ['draw', 'swap', 'sleep'], '🃏×1 ➔ Swap* ➔ 💤×1\n*Swap your awake pig with any adjacent pig', "A gentle curly-tail tug, and you've traded spots."),
    marathon: C('marathon', 'Piggy Marathon', 'pal', 2, 1, ['walk', 'walk', 'walk', 'sleep'], '🐾×3 ➔ 💤×1', 'Three steps across a five-tile room—a true marathon!'),
    saveseat: C('saveseat', 'Save a Spot',    'pal', 4, 2, ['teleport', 'sleep', 'sleep'], 'Scamper* ➔ 💤×2\n*Move your awake pig next to another own pig', 'A pat on the rug, and your pal zips right over.'),
    reunion:  C('reunion',  'Family Reunion', 'pal', 6, 1, ['teleport', 'walk', 'sleep', 'sleep'], 'Scamper* ➔ 🐾×1 ➔ 💤×2; all 3 asleep on Rug: +⭐×1\n*Move your awake pig next to another own pig', 'All three pigs snuggled up—time to harvest the stars!', { hooks: { allSleepStar: 1 } }),

    // Dual-Series Cards
    snack:     C('snack',     'Snack Platter',  ['eat', 'pal'],   3, 0, ['draw', 'walk', 'sleep'], '🃏×1 ➔ 🐾×1 ➔ 💤×1; +☁️×1 per extra Market series played (2nd+)', 'Corn and melon together—even tastier with friends.', { hooks: { seriesCloud: 1 } }),
    nudge:     C('nudge',     'Nudge In',       ['push', 'pal'],  3, 0, ['walk', 'push', 'sleep'], '🐾×1 ➔ 💥×1 ➔ 💤×1; if you wake an enemy pig, +☁️×2', 'Nudge them out, curl right into the warm hollow.', { hooks: { wakeCloud: 2 } }),
    snuggle:   C('snuggle',   'Snuggle Up',     ['pal', 'sleep'], 3, 0, ['sleep', 'gather', 'blanket'], '💤×1 ➔ Snuggle* ➔ 🛏️; +☁️×1 per cuddling pair\n*Move your sleeping pig 1 Rug step & tuck it', 'Scoot an inch closer and pull the blanket up tight.', { hooks: { pairCloud: 1 } }),
    hogpillow: C('hogpillow', 'Hog the Pillow', ['sleep', 'eat'], 5, 0, ['draw', 'walk', 'sleep'], '🃏×1 ➔ 🐾×1 ➔ 💤×1; if your pig sleeps on Pillow, +⭐×1', 'The fluffiest golden pillow belongs to whoever rolls there first.', { hooks: { pillowStar: 1 } }),
  };

  const HOUSE_RULES = {
    pillow_double: {
      key: 'pillow_double',
      name: 'Fluffy Pillow',
      tag: 'Center',
      text: 'When tallying Snores, if your pig is sleeping on the center Pillow, its bonus doubles to +2☁️.',
      flavor: 'Fluffy as a cloud tonight—claim it for huge snore bubbles!',
    },
    corner_star: {
      key: 'corner_star',
      name: 'Starry Corners',
      tag: 'Corners',
      text: 'Once per turn: when your pig takes a 💤 Sleep action on any of the 4 Rug corners, gain ⭐×1.',
      flavor: 'Sparkling Dream Stars hide in the four corners of the rug.',
    },
    small_market: {
      key: 'small_market',
      name: 'Cozy Night Market',
      tag: 'Market',
      text: 'Deal 20 random Market types at setup (remove 4). Reveal 6 slots; your 1st Market buy each turn costs -1☁️ (min 1).',
      flavor: 'Four stalls closed early, but the rest hung discount lanterns.',
    },
    wake_bounty: {
      key: 'wake_bounty',
      name: 'Wake-Up Bounty',
      tag: 'Clash',
      text: 'During Romp, each time you push a sleeping enemy pig onto the Floor to wake it, gain +☁️×2 (max 2×/turn).',
      flavor: 'Shove a snoozing rival off the rug and clouds rain into your bowl.',
    },
    double_res: {
      key: 'double_res',
      name: 'Resonance Party',
      tag: 'Combo',
      text: 'All 4 series 2-card Resonance bonuses are doubled: 🍎 Draw 🃏×2, 🐷 Bonus 🐾×2, 💤 +☁️×2 & 🛏️×2, 🌀 Bonus 💤×2.',
      flavor: 'The cabin is buzzing tonight—every matching pair works twice as hard!',
    },
    three_line: {
      key: 'three_line',
      name: 'Three in a Row',
      tag: 'Lineup',
      text: 'At the end of Romp, if all 3 of your sleeping pigs form a straight horizontal or vertical line, gain ⭐×1.',
      flavor: 'Three pigs snoring in a neat row—even the sky drops an extra star.',
    },
    piggy_bank: {
      key: 'piggy_bank',
      name: 'Piggy Bank',
      tag: 'Economy',
      text: 'After buying cards in Dream, you may save up to 2 unspent ☁️ in your bowl for your next turn.',
      flavor: 'Tuck spare snore clouds away to spend after your next nap.',
    },
    apple_sale: {
      key: 'apple_sale',
      name: 'Apple Sale',
      tag: 'Discount',
      text: 'Bedtime Apple costs only 1☁️ this game, and your buy limit increases to 4 cards per turn.',
      flavor: 'Half-price apples at the corner stand—stock up your basket!',
    },
    warm_blanket: {
      key: 'warm_blanket',
      name: 'Toasty Blanket',
      tag: 'Shield',
      text: 'During Wake: for each of your sleeping pigs that wakes up under a Felt Blanket, gain +1☁️ this turn.',
      flavor: 'Snoozing under a warm felt blanket makes dream clouds extra fluffy.',
    },
    night_party: {
      key: 'night_party',
      name: 'Night Owls',
      tag: 'Combo',
      text: 'During Romp, gain +1☁️ when you play your 3rd card and +1☁️ when you play your 4th card (max +2☁️/turn).',
      flavor: 'The humans are asleep—the real piggy party is just beginning!',
    },
    fast_sprint: {
      key: 'fast_sprint',
      name: '12-Star Sprint',
      tag: 'Fast',
      text: 'The victory target is 12⭐. Pink also draws 5 cards on Turn 1 (Yellow still gets +2☁️ on Turn 1).',
      flavor: "Everyone's sleepy tonight—twelve stars and it's lights out!",
    },
    dream_boost: {
      key: 'dream_boost',
      name: 'Dream Booster',
      tag: 'Discard',
      text: 'During Dream: gain +1☁️ for each card you discarded face-down to Dream (max 2 cards, +2☁️/turn).',
      flavor: 'Fold unplayed wishes into paper boats to sail in extra clouds.',
    },
  };

  const RULESET = {
    id: 'standard',
    name: 'Standard Rules',
    cards: CARDS,
    houseRules: Object.keys(HOUSE_RULES),
    starters: [['yawn', 4], ['shift', 4], ['squeeze', 2]],
    staple: ['apple', 8],
    market: [
      ['corn', 3], ['melon', 3], ['midnight', 3], ['pumpkin', 2], ['snack', 2], ['core', 2],
      ['dash', 3], ['overhill', 3], ['excuse', 3], ['quilt', 2], ['nudge', 2], ['shoo', 2],
      ['pillow', 3], ['sleepwalk', 3], ['train', 3], ['hibernate', 2], ['tuck', 3], ['hogpillow', 2],
      ['tail', 3], ['marathon', 3], ['saveseat', 2], ['hum', 3], ['snuggle', 2], ['reunion', 2],
    ],
    target: 15,
    hand: [4, 5],
    firstTurnSleepLimit: 0,
    firstTurnBonus: [0, 2],
    marketSize: 5,
    maxBuys: 3,
  };

  return { SERIES, CARDS, HOUSE_RULES, RULESET, SETS: { standard: RULESET }, C };
});
