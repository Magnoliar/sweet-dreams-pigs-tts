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
  MARKET_DECK    = { -21.5, 1.3, -2.5 },
  STAPLE_DECK    = { -21.5, 1.3, -7.5 },
  PINK_DRAW      = { -10.0, 1.3, -11.6 },
  PINK_DISCARD   = { 7.0, 1.3, -11.6 },
  YELLOW_DRAW    = { 10.0, 1.3, 11.6 },
  YELLOW_DISCARD = { -7.0, 1.3, 11.6 },
  HOUSERULE_DECK = { -21.5, 1.3, 7.5 },
  SNORE_BOWL     = { 16.5, 1.2, -9.5 },
  BLANKET_SUPPLY = { 15.0, 1.2, 9.5 },
  MARKET_SLOTS   = {
    { -18.0, 1.2, 5.0 },
    { -14.5, 1.2, 5.0 },
    { -18.0, 1.2, 0.0 },
    { -14.5, 1.2, 0.0 },
    { -18.0, 1.2, -5.0 },
    { -14.5, 1.2, -5.0 },
  },
  SNORE_SUPPLY_BASES = {
    { 21.8, 1.2, -4.5 },
    { 21.8, 1.2, -2.5 },
    { 21.8, 1.2, -0.5 },
  }
}

-- 游戏状态
state = {
  stars = { Pink = 0, Yellow = 0 },
  round = 1,
  turn = "Pink",
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
    end
  end

  Wait.time(function()
    calibrateBoardSnapPoints()
    buildControlPanelUI()
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
  addBtn(statusText, "noop", 0, -0.42, 3900, 390, { 0.24, 0.16, 0.12 }, { 1, 0.94, 0.82 }, 175)

  addBtn("[开局] 一键开局 / 重置", "onClickNewGame", 0, -0.31, 3900, 430, { 0.96, 0.78, 0.35 }, { 0.20, 0.10, 0.05 }, 190)

  -- 粉方按钮 (左半 / 粉色系)
  addBtn("粉猪睡醒摘星", "onClickPinkWake",   -0.24, -0.17, 1850, 430, { 0.98, 0.72, 0.80 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉猪算呼噜",   "onClickPinkSnore",  -0.24, -0.04, 1850, 430, { 0.96, 0.80, 0.86 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉猪结束回合", "onClickPinkEnd",    -0.24,  0.09, 1850, 430, { 0.94, 0.62, 0.73 }, { 0.25, 0.06, 0.12 }, 165)
  addBtn("粉 +1分",      "onClickPinkStarPlus",  -0.35, 0.23, 880, 390, { 1.0, 0.84, 0.45 }, { 0.25, 0.06, 0.12 }, 160)
  addBtn("粉 -1分",      "onClickPinkStarMinus", -0.13, 0.23, 880, 390, { 0.88, 0.82, 0.84 }, { 0.25, 0.06, 0.12 }, 160)

  -- 黄方按钮 (右半 / 黄色系)
  addBtn("黄猪睡醒摘星", "onClickYellowWake",   0.24, -0.17, 1850, 430, { 0.98, 0.86, 0.45 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄猪算呼噜",   "onClickYellowSnore",  0.24, -0.04, 1850, 430, { 0.98, 0.91, 0.62 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄猪结束回合", "onClickYellowEnd",    0.24,  0.09, 1850, 430, { 0.94, 0.78, 0.30 }, { 0.25, 0.16, 0.04 }, 165)
  addBtn("黄 +1分",      "onClickYellowStarPlus",  0.13, 0.23, 880, 390, { 1.0, 0.84, 0.45 }, { 0.25, 0.16, 0.04 }, 160)
  addBtn("黄 -1分",      "onClickYellowStarMinus", 0.35, 0.23, 880, 390, { 0.88, 0.86, 0.78 }, { 0.25, 0.16, 0.04 }, 160)

  addBtn("出牌区横置=跳过(0云) | 背面扣置=弃牌助梦", "noop", 0, 0.38, 3900, 340, { 0.32, 0.24, 0.18 }, { 0.96, 0.92, 0.86 }, 145)
end

function noop() end

-- ==========================================
-- 工具函数
-- ==========================================
function parseGMNotes(obj)
  if not obj then return {} end
  local raw = obj.getGMNotes() or ""
  if raw == "" then return {} end
  local ok, tbl = pcall(function() return JSON.decode(raw) end)
  if ok and type(tbl) == "table" then return tbl end
  return {}
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
  state.stars.Pink = 0
  state.stars.Yellow = 0
  state.round = 1
  state.turn = "Pink"

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

  -- 回收双方手牌、出牌区、弃牌堆到各自抽牌堆位置并洗匀发牌
  resetPlayerCards("Pink", 4)
  resetPlayerCards("Yellow", 5)

  -- 集市洗匀并翻开 5 张（或 6 张）
  resetMarketCards()

  updateHudStatus()
  broadcastToAll("🐷 《猪你好梦》新局开始！粉方先手抽 4 张，黄方后手抽 5 张（黄方首回合碗里额外 +2☁️）。", { 1, 0.9, 0.5 })
end

function resetPlayerCards(color, dealCount)
  local drawPos = (color == "Pink") and POS.PINK_DRAW or POS.YELLOW_DRAW
  local uprightY = (color == "Pink") and 180 or 0
  local playZone = getObjectFromGUID((color == "Pink") and GUIDS.PINK_PLAY_ZONE or GUIDS.YELLOW_PLAY_ZONE)
  local discardZone = getObjectFromGUID((color == "Pink") and GUIDS.PINK_DISCARD_ZONE or GUIDS.YELLOW_DISCARD_ZONE)

  -- 收回手牌
  local handObjs = Player[color] and Player[color].getHandObjects() or {}
  for _, obj in ipairs(handObjs) do
    obj.setPositionSmooth({ drawPos[1], drawPos[2] + 0.5, drawPos[3] }, false, true)
    obj.setRotationSmooth({ 0, uprightY, 180 }, false, true)
  end

  -- 收回出牌区和弃牌区
  for _, z in ipairs({ playZone, discardZone }) do
    if z then
      for _, obj in ipairs(z.getObjects()) do
        if obj.type == "Deck" or obj.type == "Card" then
          obj.setPositionSmooth({ drawPos[1], drawPos[2] + 0.5, drawPos[3] }, false, true)
          obj.setRotationSmooth({ 0, uprightY, 180 }, false, true)
        end
      end
    end
  end

  Wait.time(function()
    local deck = mergeDecksOrCardsAt(drawPos, 2.5)
    if deck then
      if not deck.is_face_down then deck.flip() end
      if deck.type == "Deck" then deck.shuffle() end
      Wait.time(function()
        local d2 = findDeckOrCardAt(drawPos, 2.5)
        if d2 then d2.deal(dealCount, color) end
      end, 0.5)
    end
  end, 0.75)
end

function resetMarketCards()
  local mPos = POS.MARKET_DECK
  for i = 1, 6 do
    local z = getObjectFromGUID(GUIDS.MARKET_SLOT_ZONES[i])
    if z then
      for _, obj in ipairs(z.getObjects()) do
        if obj.type == "Deck" or obj.type == "Card" then
          obj.setPositionSmooth({ mPos[1], mPos[2] + 0.5, mPos[3] }, false, true)
          obj.setRotationSmooth({ 0, 180, 180 }, false, true)
        end
      end
    end
  end

  Wait.time(function()
    local deck = mergeDecksOrCardsAt(mPos, 2.5)
    if deck then
      if deck.type == "Deck" then deck.shuffle() end
      Wait.time(function()
        refillMarketSlots()
      end, 0.5)
    end
  end, 0.75)
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
  for _, pig in ipairs(wakingPigs) do
    local pp = pig.getPosition()
    -- 检查是否有被子盖在附近
    for idx, bGuid in ipairs(GUIDS.BLANKETS) do
      local blanket = getObjectFromGUID(bGuid)
      if blanket then
        local bp = blanket.getPosition()
        local dist = math.sqrt((bp.x - pp.x)^2 + (bp.z - pp.z)^2)
        if dist < 2.2 then
          blanket.setPositionSmooth({ POS.BLANKET_SUPPLY[1], POS.BLANKET_SUPPLY[2] + (idx - 1) * 0.16, POS.BLANKET_SUPPLY[3] }, false, false)
        end
      end
    end
    pig.setRotationSmooth({ 0, uprightY, 0 }, false, false)
  end

  local newScore = state.stars[color] + gained
  moveScoreMarker(color, newScore)

  local msg = string.format(
    "🌅 %s 睡醒摘星：睡毯熟睡 %d 只 (+%d⭐) + 贴贴 %d 对 (+%d⭐) = 共 +%d⭐！（当前 %d/15⭐）",
    getColorLabel(color), sleepers, sleepers, pairsCount, pairsCount, gained, state.stars[color]
  )
  broadcastToAll(msg, getColorTint(color))

  if state.stars[color] >= 15 then
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

  if playZone then
    for _, obj in ipairs(playZone.getObjects()) do
      if obj.type == "Card" then
        local meta = parseGMNotes(obj)
        if obj.is_face_down then
          dreamSnore = dreamSnore + (tonumber(meta.dream) or 1)
        else
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

  local total = cardSnore + dreamSnore + rugSleepers + pillowBonus

  -- 从供应区移入相应数量的 1 点呼噜筹码到小木碗
  local allChips = getAllSnoreChips()
  local moved = 0
  for _, chip in ipairs(allChips) do
    if moved >= total then break end
    local p = chip.getPosition()
    -- 只移动在供应区（x > 20）的筹码
    if p.x > 20.0 then
      moved = moved + 1
      local angle = (moved * 1.1)
      local rad = 0.5 + (moved % 3) * 0.35
      chip.setPositionSmooth({
        POS.SNORE_BOWL[1] + math.cos(angle) * rad,
        POS.SNORE_BOWL[2] + 0.6 + math.floor(moved / 6) * 0.2,
        POS.SNORE_BOWL[3] + math.sin(angle) * rad
      }, false, false)
    end
  end

  local msg = string.format(
    "☁️ %s 算呼噜：牌面 +%d☁️ | 盖牌助梦 +%d☁️ | 跳过 %d 张 | 睡毯熟睡 %d 只 (+%d☁️) | 枕头格 +%d☁️ ➔ 共 %d☁️！",
    getColorLabel(color), cardSnore, dreamSnore, skippedCount, rugSleepers, rugSleepers, pillowBonus, total
  )
  broadcastToAll(msg, getColorTint(color))
end

-- ==========================================
-- 4. 结束回合（清碗 + 弃牌 + 摸 5 + 补集市）
-- ==========================================
function onClickPinkEnd() endTurn("Pink") end
function onClickYellowEnd() endTurn("Yellow") end

function endTurn(color)
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
  updateHudStatus()

  broadcastToAll(string.format("🔄 %s 结束回合：已清碗、弃牌、摸 5 张并补齐集市！", getColorLabel(color)), getColorTint(color))
end

function drawCardsWithReshuffle(color, need, drawPos, discardPos, uprightY)
  local drawDeck = findDeckOrCardAt(drawPos, 2.5)
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
    local discards = findAllDecksAndCardsAt(discardPos, 2.5)
    if #discards == 0 then return end
    for idx, d in ipairs(discards) do
      d.setPositionSmooth({ drawPos[1], drawPos[2] + 0.3 + (idx - 1) * 0.1, drawPos[3] }, false, true)
      d.setRotationSmooth({ 0, uprightY, 180 }, false, true)
    end
    Wait.time(function()
      local newDeck = mergeDecksOrCardsAt(drawPos, 2.5)
      if newDeck then
        if not newDeck.is_face_down then newDeck.flip() end
        if newDeck.type == "Deck" then newDeck.shuffle() end
        Wait.time(function()
          local d2 = findDeckOrCardAt(drawPos, 2.5)
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
  broadcastToAll(string.format("⭐ %s 手动 %+d⭐ ➔ 当前 %d/15⭐", getColorLabel(color), delta, state.stars[color]), getColorTint(color))
end
