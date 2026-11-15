-- 《猪你好梦》Tabletop Simulator 自动化脚本 (Global.lua)
-- 包含：一键开局/重置、睡醒摘星（3x3熟睡猪+贴贴+收被子+自动计分）、算呼噜（出牌区正置/横置/盖牌+熟睡猪+枕头+软绵大枕头）、结束回合（清碗+弃牌+摸5洗牌+补集市）、手动±1⭐

GUIDS = {
  BOARD             = "b0a001",
  CONTROL_PANEL     = "c71001",
  PINK_MARKER       = "5c0001",
  YELLOW_MARKER     = "5c0002",
  SNORE_BOWL        = "b0w101",
  MARKET_DECK       = "d3c001",
  STAPLE_DECK       = "d3c002",
  PINK_DECK         = "d3c003",
  YELLOW_DECK       = "d3c004",
  HOUSERULE_DECK    = "d3c005",
  PINK_PLAY_ZONE    = "20e101",
  YELLOW_PLAY_ZONE  = "20e102",
  PINK_DISCARD_ZONE = "20e103",
  YELLOW_DISCARD_ZONE = "20e104",
  HOUSERULE_ZONE    = "20e105",
  SNORE_BOWL_ZONE   = "20e106",
  MARKET_SLOT_ZONES = {
    "20e201", "20e202", "20e203", "20e204", "20e205", "20e206"
  },
  MARKET_BUY_BTNS   = {
    "b0y001", "b0y002", "b0y003", "b0y004", "b0y005", "b0y006"
  },
  STAPLE_BUY_BTN    = "b0y007",
  PINK_PIGS         = { "p19101", "p19102", "p19103" },
  YELLOW_PIGS       = { "p19201", "p19202", "p19203" },
  BLANKETS          = { "b1a001", "b1a002", "b1a003", "b1a004", "b1a005", "b1a006" },
}

-- 2000 x 1600 主棋盘精确像素坐标（与 tts/04_主棋盘_5x5布艺拼图棋盘.png 一致）
BOARD_W = 2000.0
BOARD_H = 1600.0
GRID_COL_PX = { 445.0, 726.5, 1007.0, 1287.0, 1565.5 }
GRID_ROW_PX = { 224.0, 502.0, 781.0, 1061.0, 1340.5 }

YELLOW_TRACK_X = 181.5
YELLOW_TRACK_Y = {
  101.0, 150.0, 248.5, 349.0, 445.0, 544.5, 642.5, 739.5,
  837.5, 936.0, 1034.5, 1132.0, 1231.5, 1330.0, 1427.0, 1476.0
}

PINK_TRACK_X = 1824.0
PINK_TRACK_Y = {
  1476.0, 1426.5, 1329.5, 1231.5, 1132.5, 1034.0, 936.0, 837.5,
  739.0, 642.0, 542.0, 444.0, 346.5, 246.5, 149.0, 101.0
}

-- 固定桌面坐标
POS = {
  MARKET_DECK    = { -16.5, 1.3, -2.0 },
  STAPLE_DECK    = { -16.5, 1.3, -6.0 },
  PINK_DRAW      = { -7.0, 1.3, -8.2 },
  PINK_DISCARD   = { 5.0, 1.3, -8.2 },
  YELLOW_DRAW    = { 7.0, 1.3, 8.2 },
  YELLOW_DISCARD = { -5.0, 1.3, 8.2 },
  HOUSERULE_DECK = { -16.5, 1.3, 6.0 },
  SNORE_BOWL     = { 12.2, 1.2, -6.2 },
  BLANKET_SUPPLY = { 12.2, 1.2, 6.2 },
  MARKET_SLOTS   = {
    { -13.3, 1.2, 4.5 },
    { -10.2, 1.2, 4.5 },
    { -13.3, 1.2, 0.0 },
    { -10.2, 1.2, 0.0 },
    { -13.3, 1.2, -4.5 },
    { -10.2, 1.2, -4.5 },
  },
  SNORE_SUPPLY_BASES = {
    { 16.8, 1.2, -3.5 },
    { 16.8, 1.2, -1.5 },
    { 16.8, 1.2, 0.5 },
  }
}

-- 游戏状态
state = {
  stars = { Pink = 0, Yellow = 0 },
  round = 1,
  turn = "Pink",
  buysThisTurn = 0,
  mktDiscUsed = false,
  target = 15,
  savedCloud = { Pink = 0, Yellow = 0 },
  warmBlanketBonus = { Pink = 0, Yellow = 0 },
}

local hudExpanded = true

function onClickToggleHud(player, value, id)
  hudExpanded = not hudExpanded
  UI.setAttribute("hudExpanded", "active", tostring(hudExpanded))
  UI.setAttribute("hudCollapsed", "active", tostring(not hudExpanded))
end

-- ==========================================
-- 生命周期
-- ==========================================
function onLoad(save_state)
  if save_state and save_state ~= "" then
    local ok, decoded = pcall(function() return JSON.decode(save_state) end)
    if ok and type(decoded) == "table" then
      if decoded.stars then
        state.stars.Pink = tonumber(decoded.stars.Pink) or 0
        state.stars.Yellow = tonumber(decoded.stars.Yellow) or 0
      end
      state.round = tonumber(decoded.round) or 1
      state.turn = decoded.turn or "Pink"
      state.buysThisTurn = tonumber(decoded.buysThisTurn) or 0
      state.mktDiscUsed = (decoded.mktDiscUsed == true)
      state.target = tonumber(decoded.target) or 15
      if decoded.savedCloud then
        state.savedCloud.Pink = tonumber(decoded.savedCloud.Pink) or 0
        state.savedCloud.Yellow = tonumber(decoded.savedCloud.Yellow) or 0
      end
      if decoded.warmBlanketBonus then
        state.warmBlanketBonus.Pink = tonumber(decoded.warmBlanketBonus.Pink) or 0
        state.warmBlanketBonus.Yellow = tonumber(decoded.warmBlanketBonus.Yellow) or 0
      end
    end
  end

  Wait.time(function()
    calibrateBoardSnapPoints()
    buildControlPanelUI()
    buildMarketBuyButtonsUI()
  end, 0.5)
end

function onSave()
  return JSON.encode(state)
end

-- ==========================================
-- 棋盘坐标与吸附点校准
-- ==========================================
function pixelToWorld(px, py, yOffset)
  local board = getObjectFromGUID(GUIDS.BOARD)
  if not board then return { 0, 1.5, 0 } end
  local bounds = board.getBounds()
  local wx = bounds.center.x + (px / BOARD_W - 0.5) * bounds.size.x
  local wz = bounds.center.z + (0.5 - py / BOARD_H) * bounds.size.z
  local wy = bounds.center.y + bounds.size.y * 0.5 + (yOffset or 0.15)
  return { wx, wy, wz }
end

function calibrateBoardSnapPoints()
  local board = getObjectFromGUID(GUIDS.BOARD)
  if not board then return end
  local bounds = board.getBounds()
  if bounds.size.x < 1 or bounds.size.z < 1 then return end

  local snaps = {}

  -- 25 个棋盘格中心
  for r = 1, 5 do
    for c = 1, 5 do
      local wp = pixelToWorld(GRID_COL_PX[c], GRID_ROW_PX[r], 0.05)
      local lp = board.positionToLocal(wp)
      table.insert(snaps, {
        position = { lp.x, lp.y, lp.z },
        rotation = { 0, 0, 0 },
        rotation_snap = false,
      })
    end
  end

  -- 左侧黄方 0..15 美梦分轨
  for i = 1, 16 do
    local wp = pixelToWorld(YELLOW_TRACK_X, YELLOW_TRACK_Y[i], 0.05)
    local lp = board.positionToLocal(wp)
    table.insert(snaps, {
      position = { lp.x, lp.y, lp.z },
      rotation = { 0, 0, 0 },
      rotation_snap = false,
    })
  end

  -- 右侧粉方 0..15 美梦分轨
  for i = 1, 16 do
    local wp = pixelToWorld(PINK_TRACK_X, PINK_TRACK_Y[i], 0.05)
    local lp = board.positionToLocal(wp)
    table.insert(snaps, {
      position = { lp.x, lp.y, lp.z },
      rotation = { 0, 0, 0 },
      rotation_snap = false,
    })
  end

  board.setSnapPoints(snaps)
end

-- ==========================================
-- 控制面板 UI (3D 面板 + 2D XmlUI 同步)
-- ==========================================
function getHudStatusText()
  return string.format("第 %d 轮 | 粉 %d星 vs 黄 %d星", state.round, state.stars.Pink, state.stars.Yellow)
end

function updateHudStatus()
  local statusText = getHudStatusText()
  local panel = getObjectFromGUID(GUIDS.CONTROL_PANEL)
  if panel then
    panel.editButton({ index = 0, label = statusText })
  end
  UI.setAttribute("hudStatus", "text", statusText)
end

function buildControlPanelUI()
  local statusText = getHudStatusText()
  UI.setAttribute("hudStatus", "text", statusText)

  local panel = getObjectFromGUID(GUIDS.CONTROL_PANEL)
  if not panel then return end
  panel.clearButtons()

  local function addBtn(label, fn, x, z, w, h, bg, fg, fs)
    panel.createButton({
      click_function = fn,
      function_owner = Global,
      label = label,
      position = { x, 0.55, z },
      rotation = { 0, 0, 0 },
      scale = { 0.12, 1, 0.082 },
      width = w,
      height = h,
      font_size = fs or 165,
      color = bg or { 0.95, 0.90, 0.82 },
      font_color = fg or { 0.18, 0.12, 0.08 },
    })
  end

  local statusText = getHudStatusText()
  addBtn(statusText, "noop", 0, -0.42, 3800, 390, { 0.24, 0.16, 0.12 }, { 1, 0.94, 0.82 }, 175)

  addBtn("[开局] 一键开局 / 重置", "onClickNewGame", 0, -0.31, 3800, 430, { 0.96, 0.78, 0.35 }, { 0.20, 0.10, 0.05 }, 190)

  -- 粉方按钮 (左半 / 粉色系)
  addBtn("粉猪睡醒摘星", "onClickPinkWake",   -0.24, -0.17, 1800, 430, { 0.98, 0.72, 0.80 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉猪算呼噜",   "onClickPinkSnore",  -0.24, -0.04, 1800, 430, { 0.96, 0.80, 0.86 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉猪结束回合", "onClickPinkEnd",    -0.24,  0.09, 1800, 430, { 0.94, 0.62, 0.73 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉 +1分",      "onClickPinkStarPlus",  -0.35, 0.23, 860, 390, { 1.0, 0.84, 0.45 }, { 0.25, 0.06, 0.12 }, 160)
  addBtn("粉 -1分",      "onClickPinkStarMinus", -0.13, 0.23, 860, 390, { 0.88, 0.82, 0.84 }, { 0.25, 0.06, 0.12 }, 160)

  -- 黄方按钮 (右半 / 黄色系)
  addBtn("黄猪睡醒摘星", "onClickYellowWake",   0.24, -0.17, 1800, 430, { 0.98, 0.86, 0.45 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄猪算呼噜",   "onClickYellowSnore",  0.24, -0.04, 1800, 430, { 0.98, 0.91, 0.62 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄猪结束回合", "onClickYellowEnd",    0.24,  0.09, 1800, 430, { 0.94, 0.78, 0.30 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄 +1分",      "onClickYellowStarPlus",  0.13, 0.23, 860, 390, { 1.0, 0.84, 0.45 }, { 0.25, 0.16, 0.04 }, 160)
  addBtn("黄 -1分",      "onClickYellowStarMinus", 0.35, 0.23, 860, 390, { 0.88, 0.86, 0.78 }, { 0.25, 0.16, 0.04 }, 160)

  addBtn("出牌区横置=跳过(0云) | 背面扣置=弃牌助梦", "noop", 0, 0.38, 3800, 340, { 0.32, 0.24, 0.18 }, { 0.96, 0.92, 0.86 }, 145)
end

function buildMarketBuyButtonsUI()
  local function setupBuyTile(guid, fnName)
    local tile = getObjectFromGUID(guid)
    if not tile then return end
    tile.clearButtons()
    tile.createButton({
      click_function = fnName,
      function_owner = Global,
      label = "购买",
      position = { 0, 0.55, 0 },
      rotation = { 0, 0, 0 },
      scale = { 0.22, 1, 0.66 },
      width = 2100,
      height = 680,
      font_size = 240,
      color = { 0.96, 0.78, 0.35 },
      font_color = { 0.20, 0.10, 0.05 },
    })
  end

  local mCount = getMarketCount()
  for i = 1, 6 do
    if i <= mCount then
      setupBuyTile(GUIDS.MARKET_BUY_BTNS[i], "onClickBuySlot" .. i)
    else
      local tile = getObjectFromGUID(GUIDS.MARKET_BUY_BTNS[i])
      if tile then tile.clearButtons() end
    end
  end
  setupBuyTile(GUIDS.STAPLE_BUY_BTN, "onClickBuyStaple")
end

function noop() end

-- ==========================================
-- 工具函数
-- ==========================================
function parseGMNotesRaw(raw)
  if not raw or raw == "" then return {} end
  local ok, tbl = pcall(function() return JSON.decode(raw) end)
  if ok and type(tbl) == "table" then return tbl end
  return {}
end

function parseGMNotes(obj)
  if not obj then return {} end
  return parseGMNotesRaw(obj.getGMNotes() or "")
end

function hasSeries(meta, target)
  if not meta or type(meta.series) ~= "table" then return false end
  for _, s in ipairs(meta.series) do
    if s == target then return true end
  end
  return false
end

function getColorLabel(color)
  if color == "Pink" then return "粉小猪" end
  if color == "Yellow" then return "黄小猪" end
  return color
end

function getColorTint(color)
  if color == "Pink" then return { 1.0, 0.55, 0.72 } end
  if color == "Yellow" then return { 1.0, 0.84, 0.28 } end
  return { 1, 1, 1 }
end

function isPigSleeping(pig)
  if not pig then return false end
  if pig.is_face_down then return true end
  local rot = pig.getRotation()
  local dz = math.abs((rot.z + 180) % 360 - 180)
  local dx = math.abs((rot.x + 180) % 360 - 180)
  return (dz > 120) or (dx > 120)
end

function getPigGridCell(pig)
  local board = getObjectFromGUID(GUIDS.BOARD)
  if not board or not pig then return nil, nil end
  local bounds = board.getBounds()
  local cellW = (bounds.size.x * (GRID_COL_PX[5] - GRID_COL_PX[1]) / 4.0) / BOARD_W
  local cellH = (bounds.size.z * (GRID_ROW_PX[5] - GRID_ROW_PX[1]) / 4.0) / BOARD_H
  local p = pig.getPosition()

  local bestC, bestR, bestDist = nil, nil, 9999
  for r = 1, 5 do
    for c = 1, 5 do
      local wp = pixelToWorld(GRID_COL_PX[c], GRID_ROW_PX[r], 0.15)
      local dx = p.x - wp[1]
      local dz = p.z - wp[3]
      local d = math.sqrt(dx * dx + dz * dz)
      if d < bestDist then
        bestDist = d
        bestC = c
        bestR = r
      end
    end
  end

  local threshold = math.max(cellW, cellH) * 0.62
  if bestDist <= threshold then
    return bestC, bestR
  end
  return nil, nil
end

function getActiveHouseRuleKey()
  local zone = getObjectFromGUID(GUIDS.HOUSERULE_ZONE)
  if not zone then return nil end
  for _, obj in ipairs(zone.getObjects()) do
    if obj.type == "Card" and not obj.is_face_down then
      local meta = parseGMNotes(obj)
      if meta.type == "house_rule" and meta.key then
        return meta.key
      end
    end
  end
  return nil
end

function getMarketCount()
  if getActiveHouseRuleKey() == "small_market" then
    return 6
  end
  return 5
end

function getTargetStars()
  if getActiveHouseRuleKey() == "fast_sprint" then
    return 12
  end
  return state.target or 15
end

function getMaxBuys()
  if getActiveHouseRuleKey() == "apple_sale" then
    return 4
  end
  return 3
end

function moveScoreMarker(color, newScore)
  local clamped = math.max(0, math.min(15, newScore))
  state.stars[color] = clamped
  local markerGuid = (color == "Pink") and GUIDS.PINK_MARKER or GUIDS.YELLOW_MARKER
  local marker = getObjectFromGUID(markerGuid)
  if marker then
    local idx = clamped + 1
    local px = (color == "Pink") and PINK_TRACK_X or YELLOW_TRACK_X
    local py = (color == "Pink") and PINK_TRACK_Y[idx] or YELLOW_TRACK_Y[idx]
    local wp = pixelToWorld(px, py, 0.25)
    marker.setPositionSmooth(wp, false, false)
  end
  updateHudStatus()
end

function getAllSnoreChips()
  local chips = {}
  for _, obj in ipairs(getAllObjects()) do
    local meta = parseGMNotes(obj)
    if meta.type == "snore_chip" then
      table.insert(chips, obj)
    end
  end
  return chips
end

function returnAllSnoreChipsToSupply()
  local chips = getAllSnoreChips()
  for i, chip in ipairs(chips) do
    local stackIdx = ((i - 1) % 3) + 1
    local level = math.floor((i - 1) / 3)
    local base = POS.SNORE_SUPPLY_BASES[stackIdx]
    chip.setPositionSmooth({ base[1], base[2] + level * 0.16, base[3] }, false, false)
    chip.setRotationSmooth({ 0, 180, 0 }, false, false)
  end
end

function returnSnoreChipsToSupply(chipsList)
  if not chipsList or #chipsList == 0 then return end
  local returningSet = {}
  for _, chip in ipairs(chipsList) do
    returningSet[chip] = true
  end

  -- 标记供应区已被占用的 (stackIdx, level) 槽位，避免与已有筹码碰撞
  local occupied = { {}, {}, {} }
  for _, chip in ipairs(getAllSnoreChips()) do
    if not returningSet[chip] then
      local p = chip.getPosition()
      if p.x > 14.5 then
        local bestStack = nil
        local bestDist = 9999
        for stackIdx, base in ipairs(POS.SNORE_SUPPLY_BASES) do
          local dx = p.x - base[1]
          local dz = p.z - base[3]
          local d = math.sqrt(dx * dx + dz * dz)
          if d < 0.8 and d < bestDist then
            bestDist = d
            bestStack = stackIdx
          end
        end
        if bestStack then
          local base = POS.SNORE_SUPPLY_BASES[bestStack]
          local lvl = math.max(0, math.floor((p.y - base[2]) / 0.16 + 0.5))
          occupied[bestStack][lvl] = true
        end
      end
    end
  end

  for _, chip in ipairs(chipsList) do
    local chosenStack, chosenLvl = 1, 0
    local found = false
    for lvl = 0, 30 do
      for stackIdx = 1, 3 do
        if not occupied[stackIdx][lvl] then
          chosenStack = stackIdx
          chosenLvl = lvl
          occupied[stackIdx][lvl] = true
          found = true
          break
        end
      end
      if found then break end
    end
    local base = POS.SNORE_SUPPLY_BASES[chosenStack]
    chip.setPositionSmooth({ base[1], base[2] + chosenLvl * 0.16, base[3] }, false, false)
    chip.setRotationSmooth({ 0, 180, 0 }, false, false)
  end
end

function returnAllBlanketsToSupply()
  for i, guid in ipairs(GUIDS.BLANKETS) do
    local b = getObjectFromGUID(guid)
    if b then
      b.setPositionSmooth({ POS.BLANKET_SUPPLY[1], POS.BLANKET_SUPPLY[2] + (i - 1) * 0.16, POS.BLANKET_SUPPLY[3] }, false, false)
      b.setRotationSmooth({ 0, 180, 0 }, false, false)
    end
  end
end

function findAllDecksAndCardsAt(pos, radius)
  local r = radius or 2.2
  local found = {}
  for _, obj in ipairs(getAllObjects()) do
    if obj.type == "Deck" or obj.type == "Card" then
      local p = obj.getPosition()
      local dx = p.x - pos[1]
      local dz = p.z - pos[3]
      if (dx * dx + dz * dz) <= (r * r) then
        table.insert(found, obj)
      end
    end
  end
  return found
end

function findDeckOrCardAt(pos, radius)
  local found = findAllDecksAndCardsAt(pos, radius)
  -- 优先返回 Deck
  for _, obj in ipairs(found) do
    if obj.type == "Deck" then return obj end
  end
  return found[1]
end

function mergeDecksOrCardsAt(pos, radius)
  local found = findAllDecksAndCardsAt(pos, radius)
  if #found > 1 then
    local grouped = group(found)
    if grouped and grouped[1] then
      return grouped[1]
    end
  end
  return findDeckOrCardAt(pos, radius)
end

-- ==========================================
-- 1. 一键开局 / 重置
-- ==========================================
function onClickNewGame()
  local hrKey = getActiveHouseRuleKey()
  state.stars.Pink = 0
  state.stars.Yellow = 0
  state.round = 1
  state.turn = "Pink"
  state.buysThisTurn = 0
  state.mktDiscUsed = false
  state.target = (hrKey == "fast_sprint") and 12 or 15
  state.savedCloud = { Pink = 0, Yellow = 0 }
  state.warmBlanketBonus = { Pink = 0, Yellow = 0 }

  moveScoreMarker("Pink", 0)
  moveScoreMarker("Yellow", 0)
  returnAllSnoreChipsToSupply()
  returnAllBlanketsToSupply()

  -- 重置 6 只小猪到初始地板格
  local pinkCols = { 2, 3, 4 }
  for i, guid in ipairs(GUIDS.PINK_PIGS) do
    local pig = getObjectFromGUID(guid)
    if pig then
      local wp = pixelToWorld(GRID_COL_PX[pinkCols[i]], GRID_ROW_PX[5], 0.25)
      pig.setPositionSmooth(wp, false, false)
      pig.setRotationSmooth({ 0, 180, 0 }, false, false)
    end
  end
  local yellowCols = { 2, 3, 4 }
  for i, guid in ipairs(GUIDS.YELLOW_PIGS) do
    local pig = getObjectFromGUID(guid)
    if pig then
      local wp = pixelToWorld(GRID_COL_PX[yellowCols[i]], GRID_ROW_PX[1], 0.25)
      pig.setPositionSmooth(wp, false, false)
      pig.setRotationSmooth({ 0, 0, 0 }, false, false)
    end
  end

  -- 回收所有牌（含手牌区、出牌区、弃牌堆、集市槽位及混入牌堆的集市/苹果牌）并洗匀重发
  local pinkDeal = (hrKey == "fast_sprint") and 5 or 4
  buildMarketBuyButtonsUI()
  resetAllGameCardsAndDeal(pinkDeal, 5)

  updateHudStatus()
  broadcastToAll(
    string.format("🐷 《猪你好梦》新局开始！粉方先手抽 %d 张，黄方后手抽 5 张（黄方首回合碗里额外 +2☁️，目标 %d⭐）。", pinkDeal, state.target),
    { 1, 0.9, 0.5 }
  )
end

function homePosAndRotForRole(role, fallbackPos, fallbackRot)
  if role == "pink_starter" then
    return POS.PINK_DRAW, { 0, 180, 180 }
  elseif role == "yellow_starter" then
    return POS.YELLOW_DRAW, { 0, 0, 180 }
  elseif role == "staple" then
    return POS.STAPLE_DECK, { 0, 180, 0 }
  elseif role == "market" then
    return POS.MARKET_DECK, { 0, 180, 180 }
  end
  return fallbackPos, fallbackRot
end

function routeCardObjToHome(obj, fallbackPos, fallbackRot, stackIdx)
  if not obj then return stackIdx end
  local meta = parseGMNotes(obj)
  if meta.type == "help" or meta.type == "house_rule" then
    return stackIdx
  end
  local targetPos, targetRot = homePosAndRotForRole(meta.role, fallbackPos, fallbackRot)
  if targetPos and targetRot then
    obj.setPosition({ targetPos[1], targetPos[2] + 0.15 + stackIdx * 0.03, targetPos[3] })
    obj.setRotation(targetRot)
    return stackIdx + 1
  end
  return stackIdx
end

function extractMismatchedFromDeck(deck, expectedRole, stackIdx)
  if not deck or deck.type ~= "Deck" then return stackIdx end
  local items = deck.getObjects()
  local toExtract = {}
  for _, info in ipairs(items) do
    local meta = parseGMNotesRaw(info.gm_notes or "")
    if meta.type ~= "help" and meta.type ~= "house_rule" and meta.role and meta.role ~= expectedRole then
      table.insert(toExtract, { guid = info.guid, role = meta.role })
    end
  end
  for _, entry in ipairs(toExtract) do
    if deck.type ~= "Deck" then break end
    local targetPos, targetRot = homePosAndRotForRole(entry.role, nil, nil)
    if targetPos then
      deck.takeObject({
        guid = entry.guid,
        position = { targetPos[1], targetPos[2] + 0.25 + stackIdx * 0.03, targetPos[3] },
        rotation = targetRot,
        smooth = false,
      })
      stackIdx = stackIdx + 1
    end
  end
  return stackIdx
end

function resetAllGameCardsAndDeal(pinkDeal, yellowDeal)
  local stackIdx = 0
  local handTriggers = {
    { guid = "0a0001", color = "Pink", pos = POS.PINK_DRAW, rot = { 0, 180, 180 } },
    { guid = "0a0002", color = "Yellow", pos = POS.YELLOW_DRAW, rot = { 0, 0, 180 } },
  }

  -- 1. 即时清空双方手牌（Seated 玩家手牌 + HandTrigger 区域）
  for _, ht in ipairs(handTriggers) do
    local seen = {}
    local handObjs = Player[ht.color] and Player[ht.color].getHandObjects() or {}
    for _, obj in ipairs(handObjs) do
      if obj and (obj.type == "Card" or obj.type == "Deck") and not seen[obj.getGUID()] then
        seen[obj.getGUID()] = true
        stackIdx = routeCardObjToHome(obj, ht.pos, ht.rot, stackIdx)
      end
    end
    local hZone = getObjectFromGUID(ht.guid)
    if hZone then
      for _, obj in ipairs(hZone.getObjects()) do
        if obj and (obj.type == "Card" or obj.type == "Deck") and not seen[obj.getGUID()] then
          seen[obj.getGUID()] = true
          stackIdx = routeCardObjToHome(obj, ht.pos, ht.rot, stackIdx)
        end
      end
    end
  end

  -- 2. 即时清空双方出牌区、弃牌区与集市槽位
  local zoneTargets = {
    { guid = GUIDS.PINK_PLAY_ZONE, pos = POS.PINK_DRAW, rot = { 0, 180, 180 } },
    { guid = GUIDS.PINK_DISCARD_ZONE, pos = POS.PINK_DRAW, rot = { 0, 180, 180 } },
    { guid = GUIDS.YELLOW_PLAY_ZONE, pos = POS.YELLOW_DRAW, rot = { 0, 0, 180 } },
    { guid = GUIDS.YELLOW_DISCARD_ZONE, pos = POS.YELLOW_DRAW, rot = { 0, 0, 180 } },
  }
  for i = 1, 6 do
    table.insert(zoneTargets, { guid = GUIDS.MARKET_SLOT_ZONES[i], pos = POS.MARKET_DECK, rot = { 0, 180, 180 } })
  end
  for _, zt in ipairs(zoneTargets) do
    local z = getObjectFromGUID(zt.guid)
    if z then
      for _, obj in ipairs(z.getObjects()) do
        if obj and (obj.type == "Card" or obj.type == "Deck") then
          if obj.type == "Deck" then
            -- 若是混合牌堆，先放回 fallback 位置再按 role 拆出
            obj.setPosition({ zt.pos[1], zt.pos[2] + 0.15 + stackIdx * 0.03, zt.pos[3] })
            obj.setRotation(zt.rot)
            stackIdx = stackIdx + 1
          else
            stackIdx = routeCardObjToHome(obj, zt.pos, zt.rot, stackIdx)
          end
        end
      end
    end
  end

  -- 3. 合并 4 个基础牌堆并把混入其中的他处卡牌归位
  Wait.time(function()
    local piles = {
      { pos = POS.PINK_DRAW, role = "pink_starter", radius = 1.8 },
      { pos = POS.YELLOW_DRAW, role = "yellow_starter", radius = 1.8 },
      { pos = POS.MARKET_DECK, role = "market", radius = 2.5 },
      { pos = POS.STAPLE_DECK, role = "staple", radius = 1.8 },
    }
    local idx2 = 0
    for _, p in ipairs(piles) do
      local d = mergeDecksOrCardsAt(p.pos, p.radius)
      if d then
        if d.type == "Deck" then
          idx2 = extractMismatchedFromDeck(d, p.role, idx2)
        elseif d.type == "Card" then
          local meta = parseGMNotes(d)
          if meta.role and meta.role ~= p.role then
            idx2 = routeCardObjToHome(d, p.pos, { 0, 180, 180 }, idx2)
          end
        end
      end
    end

    -- 4. 最终合并、洗牌并重新发牌与翻开集市
    Wait.time(function()
      local pDeck = mergeDecksOrCardsAt(POS.PINK_DRAW, 1.8)
      if pDeck then
        if not pDeck.is_face_down then pDeck.flip() end
        if pDeck.type == "Deck" then pDeck.shuffle() end
      end
      local yDeck = mergeDecksOrCardsAt(POS.YELLOW_DRAW, 1.8)
      if yDeck then
        if not yDeck.is_face_down then yDeck.flip() end
        if yDeck.type == "Deck" then yDeck.shuffle() end
      end
      local mDeck = mergeDecksOrCardsAt(POS.MARKET_DECK, 2.5)
      if mDeck then
        if not mDeck.is_face_down then mDeck.flip() end
        if mDeck.type == "Deck" then mDeck.shuffle() end
      end
      mergeDecksOrCardsAt(POS.STAPLE_DECK, 1.8)

      Wait.time(function()
        local pd2 = findDeckOrCardAt(POS.PINK_DRAW, 1.8)
        if pd2 then pd2.deal(pinkDeal, "Pink") end
        local yd2 = findDeckOrCardAt(POS.YELLOW_DRAW, 1.8)
        if yd2 then yd2.deal(yellowDeal, "Yellow") end
        refillMarketSlots()
      end, 0.35)
    end, 0.35)
  end, 0.25)
end

function refillMarketSlots()
  local marketDeck = findDeckOrCardAt(POS.MARKET_DECK, 2.5)
  if not marketDeck then return end
  local count = getMarketCount()
  for i = 1, count do
    local z = getObjectFromGUID(GUIDS.MARKET_SLOT_ZONES[i])
    local hasCard = false
    if z then
      for _, obj in ipairs(z.getObjects()) do
        if obj.type == "Card" or obj.type == "Deck" then
          hasCard = true
          break
        end
      end
    end
    if not hasCard then
      local sp = POS.MARKET_SLOTS[i]
      if marketDeck.type == "Deck" and marketDeck.getQuantity() > 1 then
        marketDeck.takeObject({
          position = sp,
          rotation = { 0, 180, 0 },
          smooth = true,
        })
      elseif marketDeck.type == "Card" then
        marketDeck.setPositionSmooth(sp, false, false)
        marketDeck.setRotationSmooth({ 0, 180, 0 }, false, false)
        break
      end
    end
  end
end

-- ==========================================
-- 2. 睡醒摘星
-- ==========================================
function onClickPinkWake() wakeAndScore("Pink") end
function onClickYellowWake() wakeAndScore("Yellow") end

function wakeAndScore(color)
  local pigGuids = (color == "Pink") and GUIDS.PINK_PIGS or GUIDS.YELLOW_PIGS
  local rugGrid = { {}, {}, {}, {}, {} }
  local sleepers = 0
  local wakingPigs = {}

  for _, guid in ipairs(pigGuids) do
    local pig = getObjectFromGUID(guid)
    if pig and isPigSleeping(pig) then
      local c, r = getPigGridCell(pig)
      if c and r and c >= 2 and c <= 4 and r >= 2 and r <= 4 then
        sleepers = sleepers + 1
        rugGrid[c][r] = true
      end
      table.insert(wakingPigs, pig)
    end
  end

  -- 统计正交相邻贴贴对数
  local pairsCount = 0
  for c = 2, 4 do
    for r = 2, 4 do
      if rugGrid[c][r] then
        if c < 4 and rugGrid[c + 1][r] then pairsCount = pairsCount + 1 end
        if r < 4 and rugGrid[c][r + 1] then pairsCount = pairsCount + 1 end
      end
    end
  end

  local gained = sleepers + pairsCount

  -- 翻回清醒 + 回收盖在猪身上的毛毡小被子
  local uprightY = (color == "Pink") and 180 or 0
  local blanketWakeCount = 0
  for _, pig in ipairs(wakingPigs) do
    local pp = pig.getPosition()
    local hadBlanket = false
    -- 检查是否有被子盖在附近
    for idx, bGuid in ipairs(GUIDS.BLANKETS) do
      local blanket = getObjectFromGUID(bGuid)
      if blanket then
        local bp = blanket.getPosition()
        local dist = math.sqrt((bp.x - pp.x)^2 + (bp.z - pp.z)^2)
        if dist < 1.3 then
          hadBlanket = true
          blanket.setPositionSmooth({ POS.BLANKET_SUPPLY[1], POS.BLANKET_SUPPLY[2] + (idx - 1) * 0.16, POS.BLANKET_SUPPLY[3] }, false, false)
        end
      end
    end
    if hadBlanket then
      blanketWakeCount = blanketWakeCount + 1
    end
    pig.setRotationSmooth({ 0, uprightY, 0 }, false, false)
  end

  local hrKey = getActiveHouseRuleKey()
  if hrKey == "warm_blanket" then
    state.warmBlanketBonus[color] = blanketWakeCount
  else
    state.warmBlanketBonus[color] = 0
  end

  local newScore = state.stars[color] + gained
  moveScoreMarker(color, newScore)
  local target = getTargetStars()

  local blanketNote = (hrKey == "warm_blanket" and blanketWakeCount > 0)
    and string.format("（暖呼呼被窝：本回合算呼噜 +%d☁️）", blanketWakeCount)
    or ""
  local msg = string.format(
    "🌅 %s 睡醒摘星：睡毯熟睡 %d 只 (+%d⭐) + 贴贴 %d 对 (+%d⭐) = 共 +%d⭐！（当前 %d/%d⭐）%s",
    getColorLabel(color), sleepers, sleepers, pairsCount, pairsCount, gained, state.stars[color], target, blanketNote
  )
  broadcastToAll(msg, getColorTint(color))

  if state.stars[color] >= target then
    broadcastToAll(string.format("🏆 %s 率先达到 %d⭐！请确认是否满足终局胜利条件！", getColorLabel(color), state.stars[color]), { 1, 0.85, 0.2 })
  end
end

-- ==========================================
-- 3. 算呼噜
-- ==========================================
function onClickPinkSnore() calculateSnore("Pink") end
function onClickYellowSnore() calculateSnore("Yellow") end

function calculateSnore(color)
  local playZone = getObjectFromGUID((color == "Pink") and GUIDS.PINK_PLAY_ZONE or GUIDS.YELLOW_PLAY_ZONE)
  local uprightY = (color == "Pink") and 180 or 0

  local cardSnore = 0
  local dreamSnore = 0
  local skippedCount = 0
  local sleepSeriesCount = 0
  local activePlayCount = 0
  local faceDownDreamCount = 0

  if playZone then
    for _, obj in ipairs(playZone.getObjects()) do
      if obj.type == "Card" then
        local meta = parseGMNotes(obj)
        if obj.is_face_down then
          faceDownDreamCount = faceDownDreamCount + 1
          dreamSnore = dreamSnore + (tonumber(meta.dream) or 1)
        else
          activePlayCount = activePlayCount + 1
          if hasSeries(meta, "sleep") then
            sleepSeriesCount = sleepSeriesCount + 1
          end
          local rot = obj.getRotation()
          local diff = math.abs((rot.y - uprightY + 180) % 360 - 180)
          if diff >= 45 and diff <= 135 then
            skippedCount = skippedCount + 1
          else
            cardSnore = cardSnore + (tonumber(meta.cloud) or 0)
          end
        end
      end
    end
  end

  -- 统计 3x3 睡毯熟睡猪 & 中央枕头格 (3,3)
  local pigGuids = (color == "Pink") and GUIDS.PINK_PIGS or GUIDS.YELLOW_PIGS
  local rugSleepers = 0
  local pillowBonus = 0
  local hrKey = getActiveHouseRuleKey()

  for _, guid in ipairs(pigGuids) do
    local pig = getObjectFromGUID(guid)
    if pig and isPigSleeping(pig) then
      local c, r = getPigGridCell(pig)
      if c and r and c >= 2 and c <= 4 and r >= 2 and r <= 4 then
        rugSleepers = rugSleepers + 1
        if c == 3 and r == 3 then
          pillowBonus = pillowBonus + ((hrKey == "pillow_double") and 2 or 1)
        end
      end
    end
  end

  local sleepResBonus = 0
  if sleepSeriesCount >= 2 then
    sleepResBonus = (hrKey == "double_res") and 2 or 1
  end
  local yellowT1Bonus = (state.round == 1 and color == "Yellow") and 2 or 0

  local piggyBonus = (hrKey == "piggy_bank") and (tonumber(state.savedCloud[color]) or 0) or 0
  state.savedCloud[color] = 0

  local warmBlanketBonus = (hrKey == "warm_blanket") and (tonumber(state.warmBlanketBonus[color]) or 0) or 0
  state.warmBlanketBonus[color] = 0

  local nightPartyBonus = (hrKey == "night_party") and math.min(2, math.max(0, activePlayCount - 2)) or 0
  local dreamBoostBonus = (hrKey == "dream_boost") and math.min(2, faceDownDreamCount) or 0

  local total = cardSnore + dreamSnore + rugSleepers + pillowBonus + sleepResBonus + yellowT1Bonus
    + piggyBonus + warmBlanketBonus + nightPartyBonus + dreamBoostBonus

  -- 从供应区移入相应数量的 1 点呼噜筹码到小木碗
  local allChips = getAllSnoreChips()
  local moved = 0
  for _, chip in ipairs(allChips) do
    if moved >= total then break end
    local p = chip.getPosition()
    -- 只移动在供应区（x > 14.5）的筹码
    if p.x > 14.5 then
      moved = moved + 1
      local angle = (moved * 1.1)
      local rad = 0.15 + (moved % 3) * 0.16
      chip.setPositionSmooth({
        POS.SNORE_BOWL[1] + math.cos(angle) * rad,
        POS.SNORE_BOWL[2] + 0.6 + math.floor(moved / 6) * 0.2,
        POS.SNORE_BOWL[3] + math.sin(angle) * rad
      }, false, false)
    end
  end

  local extraParts = {}
  if sleepResBonus > 0 then
    table.insert(extraParts, string.format("安睡共鸣 +%d☁️", sleepResBonus))
  end
  if yellowT1Bonus > 0 then
    table.insert(extraParts, string.format("黄方首回合 +%d☁️", yellowT1Bonus))
  end
  if piggyBonus > 0 then
    table.insert(extraParts, string.format("小猪存钱罐 +%d☁️", piggyBonus))
  end
  if warmBlanketBonus > 0 then
    table.insert(extraParts, string.format("暖呼呼被窝 +%d☁️", warmBlanketBonus))
  end
  if nightPartyBonus > 0 then
    table.insert(extraParts, string.format("越夜越精神 +%d☁️", nightPartyBonus))
  end
  if dreamBoostBonus > 0 then
    table.insert(extraParts, string.format("美梦助推器 +%d☁️", dreamBoostBonus))
  end
  local extraStr = (#extraParts > 0) and (" | " .. table.concat(extraParts, " | ")) or ""

  local msg = string.format(
    "☁️ %s 算呼噜：牌面 +%d☁️ | 盖牌助梦 +%d☁️ | 跳过 %d 张 | 睡毯熟睡 %d 只 (+%d☁️) | 枕头格 +%d☁️%s ➔ 共 %d☁️！",
    getColorLabel(color), cardSnore, dreamSnore, skippedCount, rugSleepers, rugSleepers, pillowBonus, extraStr, total
  )
  broadcastToAll(msg, getColorTint(color))
end

-- ==========================================
-- 4. 结束回合（清碗 + 弃牌 + 摸 5 + 补集市）
-- ==========================================
function onClickPinkEnd() endTurn("Pink") end
function onClickYellowEnd() endTurn("Yellow") end

function endTurn(color)
  local hrKey = getActiveHouseRuleKey()
  if hrKey == "piggy_bank" then
    local bowlChips = getBowlSnoreChips()
    local saved = math.min(2, #bowlChips)
    state.savedCloud[color] = saved
    if saved > 0 then
      broadcastToAll(
        string.format("💰 小猪存钱罐：%s 存下 %d☁️ 到下回合！", getColorLabel(color), saved),
        getColorTint(color)
      )
    end
  else
    state.savedCloud[color] = 0
  end

  returnAllSnoreChipsToSupply()

  local playZone = getObjectFromGUID((color == "Pink") and GUIDS.PINK_PLAY_ZONE or GUIDS.YELLOW_PLAY_ZONE)
  local discardPos = (color == "Pink") and POS.PINK_DISCARD or POS.YELLOW_DISCARD
  local drawPos = (color == "Pink") and POS.PINK_DRAW or POS.YELLOW_DRAW
  local uprightY = (color == "Pink") and 180 or 0

  -- 出牌区所有牌移入弃牌堆（正面朝上）
  if playZone then
    for _, obj in ipairs(playZone.getObjects()) do
      if obj.type == "Card" or obj.type == "Deck" then
        obj.setPositionSmooth({ discardPos[1], discardPos[2] + 0.3, discardPos[3] }, false, false)
        obj.setRotationSmooth({ 0, uprightY, 0 }, false, false)
      end
    end
  end

  -- 抽 5 张牌（若牌库不足则自动洗混弃牌堆补抽）
  Wait.time(function()
    drawCardsWithReshuffle(color, 5, drawPos, discardPos, uprightY)
  end, 0.35)

  -- 补齐集市展示区
  Wait.time(function()
    refillMarketSlots()
  end, 0.5)

  -- 轮次推进提示
  if color == "Pink" then
    state.turn = "Yellow"
  else
    state.turn = "Pink"
    state.round = state.round + 1
  end
  state.buysThisTurn = 0
  state.mktDiscUsed = false
  updateHudStatus()

  broadcastToAll(string.format("🔄 %s 结束回合：已清碗、弃牌、摸 5 张并补齐集市！", getColorLabel(color)), getColorTint(color))
end

function drawCardsWithReshuffle(color, need, drawPos, discardPos, uprightY)
  local drawDeck = findDeckOrCardAt(drawPos, 1.5)
  local available = 0
  if drawDeck then
    available = (drawDeck.type == "Deck") and drawDeck.getQuantity() or 1
  end

  if available >= need then
    drawDeck.deal(need, color)
    return
  end

  -- 先摸完剩余的
  if available > 0 and drawDeck then
    drawDeck.deal(available, color)
  end

  local remain = need - available
  -- 把弃牌堆（含刚弃入的散牌）全部翻面移到抽牌堆合并洗匀再补抽
  Wait.time(function()
    local discards = findAllDecksAndCardsAt(discardPos, 1.5)
    if #discards == 0 then return end
    for idx, d in ipairs(discards) do
      d.setPositionSmooth({ drawPos[1], drawPos[2] + 0.3 + (idx - 1) * 0.1, drawPos[3] }, false, true)
      d.setRotationSmooth({ 0, uprightY, 180 }, false, true)
    end
    Wait.time(function()
      local newDeck = mergeDecksOrCardsAt(drawPos, 1.5)
      if newDeck then
        if not newDeck.is_face_down then newDeck.flip() end
        if newDeck.type == "Deck" then newDeck.shuffle() end
        Wait.time(function()
          local d2 = findDeckOrCardAt(drawPos, 1.5)
          if d2 then d2.deal(remain, color) end
        end, 0.45)
      end
    end, 0.65)
  end, 0.6)
end

-- ==========================================
-- 5. 手动 ±1⭐ 计分按钮
-- ==========================================
function onClickPinkStarPlus()  adjustStar("Pink", 1) end
function onClickPinkStarMinus() adjustStar("Pink", -1) end
function onClickYellowStarPlus()  adjustStar("Yellow", 1) end
function onClickYellowStarMinus() adjustStar("Yellow", -1) end

function adjustStar(color, delta)
  local nextScore = state.stars[color] + delta
  moveScoreMarker(color, nextScore)
  local target = getTargetStars()
  broadcastToAll(string.format("⭐ %s 手动 %+d⭐ ➔ 当前 %d/%d⭐", getColorLabel(color), delta, state.stars[color], target), getColorTint(color))
  if state.stars[color] >= target then
    broadcastToAll(string.format("🏆 %s 率先达到 %d⭐！请确认是否满足终局胜利条件！", getColorLabel(color), state.stars[color]), { 1, 0.85, 0.2 })
  end
end

-- ==========================================
-- 6. 自动购买集市 / 常驻卡牌
-- ==========================================
function onClickBuySlot1() buyFromMarketSlot(1) end
function onClickBuySlot2() buyFromMarketSlot(2) end
function onClickBuySlot3() buyFromMarketSlot(3) end
function onClickBuySlot4() buyFromMarketSlot(4) end
function onClickBuySlot5() buyFromMarketSlot(5) end
function onClickBuySlot6() buyFromMarketSlot(6) end
function onClickBuyStaple() buyFromStaple() end

function getBowlSnoreChips()
  local bowlZone = getObjectFromGUID(GUIDS.SNORE_BOWL_ZONE)
  local bowlChips = {}
  if bowlZone then
    for _, obj in ipairs(bowlZone.getObjects()) do
      local m = parseGMNotes(obj)
      if m.type == "snore_chip" then
        table.insert(bowlChips, obj)
      end
    end
  end
  return bowlChips
end

function executeBuyCard(isStaple, targetObj, meta)
  local color = state.turn or "Pink"
  local cardName = meta.name or (isStaple and "消食苹果" or "卡牌")
  local cost = tonumber(meta.cost) or (isStaple and 2 or 0)
  local hrKey = getActiveHouseRuleKey()
  local usedDisc = false

  if (isStaple or meta.key == "apple") and hrKey == "apple_sale" then
    cost = 1
  end

  if not isStaple and hrKey == "small_market" and not state.mktDiscUsed then
    cost = math.max(1, cost - 1)
    usedDisc = true
  end

  local bowlChips = getBowlSnoreChips()
  if #bowlChips < cost then
    broadcastToAll(
      string.format("❌ 碗内呼噜不足：购买《%s》需要 %d☁️，当前碗内仅剩 %d☁️！", cardName, cost, #bowlChips),
      { 1, 0.4, 0.4 }
    )
    return
  end

  -- 扣除 exact cost 枚呼噜筹码并归还供应区，剩余留在碗内
  if cost > 0 then
    local toReturn = {}
    for i = 1, cost do
      table.insert(toReturn, bowlChips[i])
    end
    returnSnoreChipsToSupply(toReturn)
  end

  -- 买到的牌翻面扣置（face-down）放到当前玩家抽牌堆顶
  local drawPos = (color == "Pink") and POS.PINK_DRAW or POS.YELLOW_DRAW
  local uprightY = (color == "Pink") and 180 or 0
  local topPos = { drawPos[1], drawPos[2] + 0.5, drawPos[3] }
  local faceDownRot = { 0, uprightY, 180 }

  if targetObj.type == "Deck" then
    targetObj.takeObject({
      position = topPos,
      rotation = faceDownRot,
      smooth = true,
    })
  else
    targetObj.setPositionSmooth(topPos, false, false)
    targetObj.setRotationSmooth(faceDownRot, false, false)
  end

  state.buysThisTurn = state.buysThisTurn + 1
  if usedDisc then
    state.mktDiscUsed = true
  end

  if not isStaple then
    Wait.time(function()
      refillMarketSlots()
    end, 0.35)
  end

  local remainBowl = #bowlChips - cost
  local maxBuys = getMaxBuys()
  local discNote = usedDisc and "（小集市首购 -1☁️）" or ""
  broadcastToAll(
    string.format("🛒 %s 花费 %d☁️%s 买入《%s》置顶，碗内还剩 %d☁️（已买 %d/%d 张）",
      getColorLabel(color), cost, discNote, cardName, remainBowl, state.buysThisTurn, maxBuys),
    getColorTint(color)
  )
end

function buyFromMarketSlot(slotIdx)
  local color = state.turn or "Pink"
  local maxBuys = getMaxBuys()
  if state.buysThisTurn >= maxBuys then
    broadcastToAll(string.format("❌ 本回合已买满 %d 张！", maxBuys), getColorTint(color))
    return
  end

  if slotIdx < 1 or slotIdx > getMarketCount() then
    broadcastToAll(string.format("❌ 集市槽位 %d 当前未开启！", slotIdx), { 1, 0.4, 0.4 })
    return
  end

  local zone = getObjectFromGUID(GUIDS.MARKET_SLOT_ZONES[slotIdx])
  local targetCard = nil
  if zone then
    for _, obj in ipairs(zone.getObjects()) do
      if obj.type == "Card" and not obj.is_face_down then
        targetCard = obj
        break
      end
    end
  end

  if not targetCard then
    broadcastToAll(string.format("❌ 集市槽位 %d 目前没有可购买的卡牌！", slotIdx), { 1, 0.4, 0.4 })
    return
  end

  local meta = parseGMNotes(targetCard)
  executeBuyCard(false, targetCard, meta)
end

function buyFromStaple()
  local color = state.turn or "Pink"
  local maxBuys = getMaxBuys()
  if state.buysThisTurn >= maxBuys then
    broadcastToAll(string.format("❌ 本回合已买满 %d 张！", maxBuys), getColorTint(color))
    return
  end

  local stapleObj = findDeckOrCardAt(POS.STAPLE_DECK, 2.2)
  if not stapleObj then
    broadcastToAll("❌ 常驻供应《消食苹果》已售罄！", { 1, 0.4, 0.4 })
    return
  end

  local meta = {}
  if stapleObj.type == "Deck" then
    local contained = stapleObj.getObjects()
    if contained and contained[1] and contained[1].gm_notes then
      meta = parseGMNotesRaw(contained[1].gm_notes)
    end
  else
    meta = parseGMNotes(stapleObj)
  end

  executeBuyCard(true, stapleObj, meta)
end
