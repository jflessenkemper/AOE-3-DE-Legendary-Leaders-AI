//==============================================================================
// RULE explorationAgeWalling
// Start a basic ring wall around the main base in the Exploration Age.
//==============================================================================
bool llShouldBuildLegendaryWalls(bool earlyGame = false)
{
   if (cvOkToBuildWalls == false)
   {
      return (false);
   }

   // Doctrine veto: MobileNoWalls (Napoleon / Crazy Horse / Hiawatha /
   // Montezuma / Usman) overrides everything. No early walls, no late walls,
   // no gap fills, no upgrades. Their playstyle is open-field manoeuvre.
   if (gLLWallStrategy == cLLWallStrategyMobileNoWalls)
   {
      return (false);
   }

   if (earlyGame == true)
   {
      return (gLLEarlyWallingEnabled);
   }

   if (gLLWallLevel <= 0)
   {
      return (false);
   }

   return (gLLLateWallingEnabled);
}

float llGetLegendaryWallRadius(bool lateGame = false)
{
   float wallRadius = 42.0;

   if (lateGame == true)
   {
      wallRadius = 75.0;
   }
   if (gIslandMap == true)
   {
      wallRadius = lateGame == true ? 95.0 : 55.0;
   }

   if (gLLWallLevel == 1)
   {
      wallRadius = wallRadius - 6.0;
   }
   else if (gLLWallLevel == 3)
   {
      wallRadius = wallRadius + 6.0;
   }
   else if (gLLWallLevel >= 4)
   {
      wallRadius = wallRadius + 10.0;
   }

   if (gLLBuildStyle == cLLBuildStyleCompactFortifiedCore)
   {
      wallRadius = wallRadius - 4.0;
   }
   else if (gLLBuildStyle == cLLBuildStyleMobileFrontierScatter)
   {
      wallRadius = wallRadius + 8.0;
   }

   return (wallRadius);
}

int llGetLegendaryWallGateCount(bool lateGame = false)
{
   // Raised from 4/15 to 6/18. More gates = better sally routes and the
   // engine lays down more wall pieces per plan (each gate anchors an arc).
   int gateCount = lateGame == true ? 18 : 6;

   if (gLLWallLevel == 1)
   {
      gateCount = gateCount + 2;
   }
   else if (gLLWallLevel == 3)
   {
      gateCount = gateCount - 1;
   }
   else if (gLLWallLevel >= 4)
   {
      gateCount = gateCount - 2;
   }

   if (gateCount < 3)
   {
      gateCount = 3;
   }

   return (gateCount);
}

// Shift the wall ring center slightly along the base's front vector (toward
// the likely enemy arc). A full ring still surrounds the base, but the
// extra bias thickens wall coverage on the contested side where it matters
// most. Returns the input unchanged if no front vector is registered.
vector llGetForwardBiasedWallCenter(vector baseCenter = cInvalidVector,
                                    int mainBaseID = -1,
                                    float biasFactor = 0.25)
{
   if ((baseCenter == cInvalidVector) || (mainBaseID < 0))
   {
      return (baseCenter);
   }
   vector frontVec = kbBaseGetFrontVector(cMyID, mainBaseID);
   if ((frontVec == cInvalidVector) ||
       ((xsVectorGetX(frontVec) == 0.0) && (xsVectorGetZ(frontVec) == 0.0)))
   {
      return (baseCenter);
   }
   float radius = llGetLegendaryWallRadius(false);
   float shift = radius * biasFactor;
   float nx = xsVectorGetX(baseCenter) + xsVectorGetX(frontVec) * shift;
   float nz = xsVectorGetZ(baseCenter) + xsVectorGetZ(frontVec) * shift;
   return (xsVectorSet(nx, xsVectorGetY(baseCenter), nz));
}

//==============================================================================
// Per-doctrine wall strategy dispatch. Each strategy plans its Age-1
// fortifications in a historically-grounded way.
//==============================================================================

// FortressRing: full 360-degree ring wall with extra thickness/gates.
// Valette, Pachacuti, Frederick, Suleiman, Catherine, Bourbon France.
// Keeps symmetric center — fortress doctrine is all-around defense.
int llPlanFortressRingWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false);
   int planID = aiPlanCreate("FortressRing Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   // Heavy villager commitment — a ~264-unit perimeter at radius 42 needs a
   // sustained pool, not a 3–5 starter crew that finishes its first segment
   // and goes home. Bumped 3,5 -> 6,12 so the ring actually closes.
   // min=2 (was 6): a stalled plan only locks 2 villagers idle, not 6.
   // max=12: still scales up when there are wall pieces to place.
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 12);
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   // Fewer gates = fewer gaps. Fortress doctrine wants a dense wall.
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 4);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 88);  // raised 75 -> 88 so wall wins over barracks/houses
   aiPlanSetActive(planID, true);
   llProbe("plan.wall.create", "type=FortressRing radius=" + radius +
      " gates=4 vils=6-12 priority=88 plan=" + planID);
   return (planID);
}

// ChokepointSegments: walls only at natural terrain pinches (Andes/Alps/passes).
// Shivaji (Maratha hill forts), Pachacuti (valley mouths), Kangxi (Great Wall).
// Fallback to a tighter ring if chokepoint detection fails on flat maps —
// biased forward toward enemy since chokepoints always face outward.
int llPlanChokepointWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false) - 4.0;
   vector center = llGetForwardBiasedWallCenter(baseCenter, mainBaseID, 0.35);
   int planID = aiPlanCreate("Chokepoint Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 10);  // min=2 to release idlers when plan stalls
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, center);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 3);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 85);
   aiPlanSetActive(planID, true);
   llProbe("plan.wall.create", "type=Chokepoint radius=" + radius +
      " gates=3 vils=5-10 priority=85 plan=" + planID);
   return (planID);
}

// CoastalBatteries: land-side partial ring (Wellington Torres Vedras, Henry Elmina).
// Ring center pushed inland (away from the coast arc) so the wall covers
// the landward approach more thickly — matches real peninsular doctrine.
int llPlanCoastalBatteriesWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false);
   vector center = llGetForwardBiasedWallCenter(baseCenter, mainBaseID, 0.20);
   int planID = aiPlanCreate("CoastalBatteries Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 10);  // min=2 to release idlers when plan stalls
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, center);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 4);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 86);
   aiPlanSetActive(planID, true);
   llProbe("plan.wall.create", "type=CoastalBatteries radius=" + radius +
      " gates=4 vils=6-10 priority=86 plan=" + planID);
   return (planID);
}

// FrontierPalisades: quick lighter ring, many gates, less stone.
// Washington, Jefferson, Brock, Papineau, Houston, Kruger, Mannerheim, Morazán.
int llPlanFrontierPalisadeWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false) + 2.0;
   vector center = llGetForwardBiasedWallCenter(baseCenter, mainBaseID, 0.15);
   int planID = aiPlanCreate("FrontierPalisade Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 8);   // min=2 to release idlers when plan stalls
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, center);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 5);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 82);  // wood-cheap palisades, complete first
   aiPlanSetActive(planID, true);
   llProbe("plan.wall.create", "type=FrontierPalisade radius=" + radius +
      " gates=5 vils=4-8 priority=82 plan=" + planID);
   return (planID);
}

// UrbanBarricade: tight compact inner ring (Robespierre Paris, Garibaldi cities).
int llPlanUrbanBarricadeWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false) - 8.0;
   vector center = llGetForwardBiasedWallCenter(baseCenter, mainBaseID, 0.15);
   int planID = aiPlanCreate("UrbanBarricade Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 8);   // min=2 to release idlers when plan stalls
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, center);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 3);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 84);
   aiPlanSetActive(planID, true);
   llProbe("plan.wall.create", "type=UrbanBarricade radius=" + radius +
      " gates=3 vils=4-8 priority=84 plan=" + planID);
   return (planID);
}

// MobileNoWalls: no walls at all, leaner strategy built elsewhere.
// Returns -1 to signal "skip entirely".
int llPlanMobileNoWalls(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   return (-1);  // intentionally no wall plan
}

// Strategy dispatch — called from the rule.
int llPlanExplorationAgeWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   // LL-WALL probe — records which doctrine branch ran and the base center.
   // One emission per AI per match (rule self-disables after first dispatch),
   // so the replay parser can map leader → actual wall strategy exercised.
   llProbe("plan.wall", "strategy=" + gLLWallStrategy + " base=" + mainBaseID +
      " center=" + llFmtVec(baseCenter) + " wallLevel=" + gLLWallLevel +
      " earlyWalls=" + gLLEarlyWallingEnabled);

   if (gLLWallStrategy == cLLWallStrategyFortressRing)       return (llPlanFortressRingWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyChokepointSegments) return (llPlanChokepointWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyCoastalBatteries)   return (llPlanCoastalBatteriesWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyFrontierPalisades)  return (llPlanFrontierPalisadeWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyUrbanBarricade)     return (llPlanUrbanBarricadeWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyMobileNoWalls)      return (llPlanMobileNoWalls(mainBaseID, baseCenter));
   // Fallback — FortressRing if unknown.
   llProbe("plan.wall", "fallback=FortressRing unknownStrategy=" + gLLWallStrategy);
   return (llPlanFortressRingWall(mainBaseID, baseCenter));
}

// PERPETUAL WALLING MODEL
// =======================
// Walls are top-priority protection and the AI dedicates villagers to them
// every age. We do NOT disable these rules after placing a plan — we keep
// them ticking so:
//   (a) if the engine evicts / completes the wall plan, we replace it;
//   (b) if the base expands or walls are destroyed, gap-fill + new rings
//       kick in automatically;
//   (c) villager allocation on the standing plan stays topped up.
// Anti-spam is enforced by aiPlanGetIDByTypeAndVariableType dedup: we never
// create a second ring plan while one is active. MobileNoWalls doctrines
// opt out cleanly via xsDisableSelf at rule entry.
rule explorationAgeWalling
inactive
group tcComplete
minInterval 20
{
   // LL-WALL-GATE probe — fires every tick of the rule, so the replay parser
   // sees exactly which gate causes the rule to bail. Compact tag because
   // this can fire many times per match per AI.
   static int gateTickProbe = 0;
   gateTickProbe = gateTickProbe + 1;

   if (cvOkToBuild == false)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " bail=cvOkToBuild");
      llLogDecision("WALL", "exploration walling disabled by config (cvOkToBuild)");
      xsDisableSelf();
      return;
   }
   if (llShouldBuildLegendaryWalls(true) == false)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe +
         " bail=llShould early=" + gLLEarlyWallingEnabled +
         " level=" + gLLWallLevel +
         " okWalls=" + cvOkToBuildWalls);
      llLogDecision("WALL", "exploration walling disabled by config (llShould)");
      xsDisableSelf();
      return;
   }

   // Hand off to delayWallsNew (which is perpetual from Age 3 onward) once
   // we're past Exploration — keeps responsibilities clean.
   if (kbGetAge() > cAge1)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " bail=ageOver age=" + kbGetAge());
      xsDisableSelf();
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   if (mainBaseID < 0)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " bail=noMainBase");
      return;
   }

   // Anti-spam: skip while any ring plan is active or while existing walls
   // already surround the base (gap-fill owns that case).
   int existingRingPlan = aiPlanGetIDByTypeAndVariableType(cPlanBuildWall, cBuildWallPlanWallType, cBuildWallPlanWallTypeRing, true);
   if (existingRingPlan >= 0)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " skip=ringActive plan=" + existingRingPlan);
      xsEnableRule("fillInWallGapsNew");
      return;
   }

   int existingWalls = kbUnitCount(cMyID, cUnitTypeAbstractWall, cUnitStateABQ);
   if (existingWalls > 0)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " skip=wallsExist count=" + existingWalls);
      xsEnableRule("fillInWallGapsNew");
      // Don't disable — if the plan disappears later and all walls die,
      // we want this rule to recreate the ring instead of going silent.
      return;
   }

   float wood = kbResourceGet(cResourceWood);
   if (wood < 75.0)
   {
      llProbe("wall.gate", "tick=" + gateTickProbe + " wait=lowWood wood=" + wood);
      return;
   }

   vector baseCenter = kbBaseGetLocation(cMyID, mainBaseID);
   if (baseCenter == cInvalidVector)
   {
      return;
   }

   int wallPlanID = llPlanExplorationAgeWall(mainBaseID, baseCenter);
   if (wallPlanID < 0)
   {
      // MobileNoWalls doctrine decision is permanent.
      llLogDecision("WALL", "strategy=" + gLLWallStrategy + " declined to build walls (MobileNoWalls)");
      xsDisableSelf();
      return;
   }

   llLogPlanEvent("create", wallPlanID, "exploration-wall strategy=" + gLLWallStrategy + " center=" + baseCenter);
   xsEnableRule("fillInWallGapsNew");
   // Stay active: anti-spam dedup above prevents duplicate plans, but if
   // this plan ever dies we want to place a fresh one.
}

//==============================================================================
// RULE enhancedWalls
//==============================================================================
rule enhancedWalls
inactive
minInterval 10
{
   vector myBaseLoc = kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID));
   vector mainBaseCenter = kbAreaGetCenter(kbAreaGetIDByPosition(myBaseLoc));
   vector mainBaseFront = kbBaseGetFrontVector(cMyID, kbBaseGetMainID(cMyID));
   float woodAmount = kbResourceGet(cResourceWood);

   //buildSquareWall(mainBaseCenter, kbBaseGetMainID(cMyID), 100, 9);

   if (gWallBuildingSuccess == true) {
      xsDisableSelf();
   }
}
//==============================================================================
// RULE delayWallsNew
//==============================================================================
// Persistent Fortress+ walling. Fires every 30s from Age 3 onward for the
// rest of the match. Anti-spam dedup prevents multiple ring plans on the
// same base. Outer ring supplement kicks in at Age 4 so the defended
// perimeter expands as the base grows — but only one outer ring, ever.
rule delayWallsNew
inactive
minInterval 30
{
   if (llShouldBuildLegendaryWalls(false) == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() < cAge3)
   {
      return;
   }

   if (gLLWallStrategy == cLLWallStrategyMobileNoWalls)
   {
      llLogDecision("WALL", "late walling declined - MobileNoWalls doctrine");
      xsDisableSelf();
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   if (mainBaseID < 0)
   {
      return;
   }
   vector baseCenter = kbBaseGetLocation(cMyID, mainBaseID);
   if (baseCenter == cInvalidVector)
   {
      return;
   }

   // Anti-spam: is there ALREADY an active ring plan on this base?
   // If yes we leave it alone — no duplicate ring spam. The plan stays
   // alive and the engine keeps placing pieces as wood allows.
   bool ringActive = (aiPlanGetIDByTypeAndVariableType(
      cPlanBuildWall, cBuildWallPlanWallType, cBuildWallPlanWallTypeRing, true) >= 0);

   // Wider outer ring for late-game walls; more gates for sally options.
   // FortressRing = symmetric; all others bias forward toward the enemy arc.
   float wallRadius = llGetLegendaryWallRadius(true);
   vector wallCenter = baseCenter;
   if (gLLWallStrategy != cLLWallStrategyFortressRing)
   {
      wallCenter = llGetForwardBiasedWallCenter(baseCenter, mainBaseID, 0.18);
   }

   // Static flag so the outer supplement only ever fires once.
   static int outerRingPlaced = 0;
   bool placingOuter = false;

   if (ringActive == true)
   {
      // Main ring is already active. Consider placing the OUTER supplement
      // when we hit Age 4 (Industrial) — a single wider ring that doubles
      // the defended perimeter. Only once per match per AI.
      if ((kbGetAge() >= cAge4) && (outerRingPlaced == 0))
      {
         placingOuter = true;
         wallRadius = wallRadius * 1.35;  // 35% wider outer ring
      }
      else
      {
         // Nothing to do this tick — ring alive, no supplement needed yet.
         return;
      }
   }

   int wallPlanID = aiPlanCreate(placingOuter ? "OuterWallRing" : "WallInBase", cPlanBuildWall);
   if (wallPlanID < 0)
   {
      return;
   }

   aiPlanSetVariableInt(wallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   // 3–5 dedicated villagers — walls are top-priority protection.
   aiPlanAddUnitType(wallPlanID, gEconUnit, 0, 3, 5);
   aiPlanSetVariableVector(wallPlanID, cBuildWallPlanWallRingCenterPoint, 0, wallCenter);
   aiPlanSetVariableFloat(wallPlanID, cBuildWallPlanWallRingRadius, 0.0, wallRadius);
   aiPlanSetVariableInt(wallPlanID, cBuildWallPlanNumberOfGates, 0, llGetLegendaryWallGateCount(true));
   aiPlanSetBaseID(wallPlanID, mainBaseID);
   aiPlanSetEscrowID(wallPlanID, cEconomyEscrowID);
   // Priority 75 for primary ring, 70 for outer supplement (don't starve
   // the main ring if wood contention arises).
   aiPlanSetDesiredPriority(wallPlanID, placingOuter ? 70 : 75);
   aiPlanSetActive(wallPlanID, true);
   xsEnableRule("fillInWallGapsNew");

   if (placingOuter == true)
   {
      outerRingPlaced = 1;
   }

   llLogPlanEvent("create", wallPlanID,
      (placingOuter ? "outer-wall" : "late-wall") +
      " strategy=" + gLLWallStrategy +
      " center=" + llFmtVec(wallCenter) +
      " radius=" + wallRadius +
      " gates=" + llGetLegendaryWallGateCount(true));
   llProbe("plan.wall",
      "phase=" + (placingOuter ? "outer" : "late") +
      " strategy=" + gLLWallStrategy +
      " base=" + mainBaseID +
      " center=" + llFmtVec(wallCenter) +
      " radius=" + wallRadius +
      " wallLevel=" + gLLWallLevel);
   // Stay active: if this plan ever dies, re-create it next tick.
}
//==============================================================================
// RULE fillInWallGapsNew
//==============================================================================
rule fillInWallGapsNew
  minInterval 51
  inactive
{
   float wallRadius = llGetLegendaryWallRadius(true); //kbGetMapXSize() / 7.0;

   if (llShouldBuildLegendaryWalls(false) == false)
   {
      xsDisableSelf();
      return;
   }

   // Doctrine gate: MobileNoWalls leaders (Napoleon, Crazy Horse, Hiawatha,
   // Montezuma, Usman) must NEVER build walls. delayWallsNew already honours
   // this; fillInWallGapsNew used to leak through and that's what produced
   // Napoleon's walls in the 16:27 replay.
   if (gLLWallStrategy == cLLWallStrategyMobileNoWalls)
   {
      llLogDecision("WALL", "gap-fill declined - MobileNoWalls doctrine");
      xsDisableSelf();
      return;
   }

  if(aiPlanGetIDByTypeAndVariableType(cPlanBuildWall, cBuildWallPlanWallType, cBuildWallPlanWallTypeRing, true) >= 1)
      return;

   int wallPlanID=aiPlanCreate("fillInWallGapsNew", cPlanBuildWall);
   if (wallPlanID != -1)
   {
         aiPlanSetVariableInt(wallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
         aiPlanAddUnitType(wallPlanID, gEconUnit, 0, 1, 2);
         aiPlanSetVariableVector(wallPlanID, cBuildWallPlanWallRingCenterPoint, 0, kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID)));
         aiPlanSetVariableFloat(wallPlanID, cBuildWallPlanWallRingRadius, 0.0, wallRadius);
         aiPlanSetVariableInt(wallPlanID, cBuildWallPlanNumberOfGates, 0, llGetLegendaryWallGateCount(true));
         aiPlanSetBaseID(wallPlanID, kbBaseGetMainID(cMyID));
         aiPlanSetEscrowID(wallPlanID, cEconomyEscrowID);
         aiPlanSetDesiredPriority(wallPlanID, 65);
         aiPlanSetActive(wallPlanID, true);
   }
}
//==============================================================================
// RULE wallPlanStallWatchdog
// Wall plans hold gEconUnit villagers exclusively. When a plan can't make
// progress (no buildable arc, wood-starved, base relocated), the held
// villagers go IDLE — that's the bug the user observed in the 16:27 replay.
// This rule walks every active wall plan, ages it via a static map, and
// destroys plans that haven't completed in `cWallPlanMaxAgeSec`. The next
// walling rule tick will recreate a fresh plan with a fresh layout.
//==============================================================================
const int cWallPlanMaxAgeSec = 240;  // 4 min — enough for a normal ring to complete

rule wallPlanStallWatchdog
inactive
minInterval 30
{
   int planID = aiPlanGetIDByTypeAndVariableType(cPlanBuildWall,
                    cBuildWallPlanWallType, cBuildWallPlanWallTypeRing, true);
   if (planID < 0) { return; }

   // User-variable slot 0 holds the creation timestamp (ms). aiPlan user
   // vars default to 0, so a never-stamped plan reads back 0 — we stamp on
   // first sight, then evaluate stall on subsequent ticks.
   int created = aiPlanGetUserVariableInt(planID, 0, 0);
   int now     = xsGetTime();

   if (created == 0)
   {
      aiPlanSetUserVariableInt(planID, 0, 0, now);
      return;
   }

   int ageMs = now - created;
   if (ageMs < (cWallPlanMaxAgeSec * 1000)) { return; }

   // Stalled. Destroy so the held villagers free up and the perpetual
   // rule recreates a fresh plan with a recomputed layout.
   llProbe("plan.wall.stall", "plan=" + planID + " ageMs=" + ageMs +
      " strategy=" + gLLWallStrategy);
   llLogPlanEvent("destroy-stalled", planID,
      "ageSec=" + (ageMs / 1000) + " strategy=" + gLLWallStrategy);
   aiPlanDestroy(planID);
}

//==============================================================================
// RULE bastionUpgradeMonitor
// Make sure we research bastion so our walls are stronger.
//==============================================================================
rule bastionUpgradeMonitor
inactive
minInterval 90
{
   int upgradePlanID = -1;
   int myWallId = getUnit(cUnitTypeAbstractWall, cMyID);

   if ((kbTechGetStatus(cTechBastion) == cTechStatusActive))
   {
      xsDisableSelf();
      return;
   }

   researchSimpleTechByCondition(cTechBastion, 
   []() -> bool { return (kbTechGetStatus(cTechBastion) == cTechStatusObtainable); },
   cUnitTypeAbstractWall, myWallId, 70);
}
//==============================================================================
// factoryWall
// Wall-in the first factory we find.
//==============================================================================
rule factoryWall
inactive
minInterval 10
{
   int factoriesQuery = createSimpleUnitQuery(cUnitTypeFactory, cMyID, cUnitStateABQ);
   int factoriesFound = kbUnitQueryExecute(factoriesQuery);

   if (factoriesFound > 0) {
      vector factoryPos = kbUnitGetPosition(kbUnitQueryGetResult(factoriesQuery, 0));
      kbUnitQueryDestroy(factoriesQuery);

      int wallPlanID = aiPlanCreate("Factory Wall", cPlanBuildWall);
      int numberOfGates = 4;
      float baseWallRadius = 12.0;
      vector baseWallCenter = factoryPos; // Set the center to the factory position

      if (wallPlanID != -1)
      {
         aiPlanSetVariableInt(wallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
         aiPlanAddUnitType(wallPlanID, cUnitTypeAbstractVillager, 1, 1, 1);
         aiPlanSetVariableVector(wallPlanID, cBuildWallPlanWallRingCenterPoint, 0, baseWallCenter);
         aiPlanSetVariableInt(wallPlanID, cBuildPlanLocationPreference, 0, cBuildingPlacementPreferenceFront);
         aiPlanSetVariableFloat(wallPlanID, cBuildWallPlanWallRingRadius, 0, baseWallRadius);
         aiPlanSetVariableInt(wallPlanID, cBuildWallPlanNumberOfGates, 0, numberOfGates);
         aiPlanSetBaseID(wallPlanID, kbBaseGetMainID(cMyID));
         aiPlanSetEscrowID(wallPlanID, cEconomyEscrowID);
         aiPlanSetDesiredPriority(wallPlanID, 75);
         aiPlanSetActive(wallPlanID, true);
         debugBuildings("Enabling Factory Wall Plan for Base ID: " + kbBaseGetMainID(cMyID));
         xsDisableSelf();
      }
   }
}
//==============================================================================
// RULE rebuildLostForts
// Make sure we maintain the maximum number of forts.
//==============================================================================
rule rebuildLostForts
minInterval 10
inactive
{
   int fortsWanted = llGetWantedFortCount();

   if (fortsWanted < 1)
   {
      if (gFortRebuildPlan >= 0)
      {
         aiPlanDestroy(gFortRebuildPlan);
         gFortRebuildPlan = -1;
      }
      return;
   }

   llVerboseEcho("Fort Limit: "+kbGetBuildLimit(cMyID, gFortUnit)+"Forts We Have: "
   +kbUnitCount(cMyID, gFortUnit, cUnitStateABQ)+"");
if (fortsWanted > kbUnitCount(cMyID, gFortUnit, cUnitStateABQ)) {
		llVerboseEcho("I need to rebuild forts now!");
      // Nobody is making a fort, let's start a plan.
      if (gFortRebuildPlan == -1) {
         gFortRebuildPlan = aiPlanCreate("Fortress Build Plan", cPlanBuild);
         int heroQuery = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive);
         int numberHeroesFound = kbUnitQueryExecute(heroQuery);
         int heroPlanID = -1;
         int heroID = -1;
         int unitID = -1;

         if (numberHeroesFound < 1) {
            return;
         }

         aiPlanSetVariableInt(gFortRebuildPlan, cBuildPlanBuildingTypeID, 0, gFortUnit);
         // Priority.
         aiPlanSetDesiredPriority(gFortRebuildPlan, 100);
         aiPlanSetDesiredResourcePriority(gFortRebuildPlan, 100);
         // Mil vs. Econ.
         aiPlanSetMilitary(gFortRebuildPlan, true);
         aiPlanSetEconomy(gFortRebuildPlan, false);
         // Escrow.
         aiPlanSetEscrowID(gFortRebuildPlan, cMilitaryEscrowID);
         // Builders.
         for (int n = 0; n < numberHeroesFound; n++)
         {
            unitID = kbUnitQueryGetResult(heroQuery, n);
            if (unitID < 0)
            {
               continue;
            }
            // if (kbProtoUnitCanTrain(kbUnitGetProtoUnitID(unitID), cUnitTypeTradingPost) == false)
            // {
            //    continue;
            // }
            heroPlanID = kbUnitGetPlanID(heroID);
            if ((heroPlanID < 0))
            {
               heroID = unitID;
               break;
            }
         }
         if (heroID != -1) // We have found a suitable Hero, so we will add him to the plan.
         {
            debugBuildings("We are adding 1 " + kbGetProtoUnitName(kbUnitGetProtoUnitID(heroID)) + " with ID: " +
               heroID + " to our Fort build plan.");
            aiPlanAddUnitType(gFortRebuildPlan, cUnitTypeHero, 1, 1, 1);
            aiPlanAddUnit(gFortRebuildPlan, heroID);
            aiPlanSetNoMoreUnits(gFortRebuildPlan, true);
            int forwardBaseFortQuery = createSimpleUnitQuery(gFortUnit, cMyID, cUnitStateABQ);
            kbUnitQuerySetMaximumDistance(forwardBaseFortQuery, 50.0);
            kbUnitQuerySetPosition(forwardBaseFortQuery, gForwardBaseLocation);
            if ((gLLPreferForwardFortifiedBase == true) && (gForwardBaseLocation != cInvalidVector) &&
               (kbUnitQueryExecute(forwardBaseFortQuery) < 1)) {
               aiPlanSetVariableVector(gFortRebuildPlan, cBuildPlanCenterPosition, 0, gForwardBaseLocation);
               aiPlanSetVariableFloat(gFortRebuildPlan, cBuildPlanCenterPositionDistance, 0, 30.0);
            }
         } else {
            aiPlanDestroy(gFortRebuildPlan);
            return;
         }
      
         aiPlanSetActive(gFortRebuildPlan);
         llVerboseEcho("Fort building activated!");
         llVerboseEcho("**** STARTING FORT PLAN, plan ID "+gFortRebuildPlan);
      }
	} else {
      aiPlanDestroy(gFortRebuildPlan);
      gFortRebuildPlan = -1;
   }

   // Start training at the forward base...
   if (kbBaseGetActive(cMyID, gIslandBaseID) == true) {
      updateSecondaryBaseMilitaryTrainPlans(gIslandBaseID);
   } else {
      updateSecondaryBaseMilitaryTrainPlans(gForwardBaseID);
   }

	return;
}
//==============================================================================
// RULE fortUpgradeMonitor
// Make sure we upgrade those forts!
//==============================================================================
rule fortUpgradeMonitor
inactive
minInterval 90
{
   int upgradePlanID = -1;
   int myFortId = getUnit(cUnitTypeFortFrontier, cMyID);

   if ((kbTechGetStatus(cTechRevetment) == cTechStatusActive) && (kbTechGetStatus(cTechStarFort) == cTechStatusActive))
   {
      xsDisableSelf();
      return;
   }

   researchSimpleTechByCondition(cTechRevetment, 
   []() -> bool { return (kbTechGetStatus(cTechRevetment) == cTechStatusObtainable); },
   cUnitTypeFortFrontier, myFortId, 60);
   researchSimpleTechByCondition(cTechStarFort, 
   []() -> bool { return (kbTechGetStatus(cTechStarFort) == cTechStatusObtainable); },
   cUnitTypeFortFrontier, myFortId, 60);
}
//==============================================================================
// forwardBaseWall
// Wall-in the forward base.
//==============================================================================
rule forwardBaseWall
inactive
minInterval 10
{
   if (gForwardBaseState == cForwardBaseStateNone || gForwardBaseID == -1)
   {
      return;
   } else if (distance(kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID)), 
               kbBaseGetLocation(cMyID, gForwardBaseID)) < 20.0) {
      xsDisableSelf();
   }
   
   int wallPlanID = aiPlanCreate("Forward base wall", cPlanBuildWall);
   int numberOfGates = 4;
   float baseWallRadius = 27.0;
   vector baseWallCenter = gForwardBaseLocation;

   //(gForwardBaseLocation, gForwardBaseID, 95, 4);
   //buildPentagonWall(gForwardBaseLocation, gForwardBaseID, 95, 5);
   //buildPentagonWall(gForwardBaseLocation, -1, 95, 5);

   if (wallPlanID != -1)
   {
      aiPlanSetVariableInt(wallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
      aiPlanAddUnitType(wallPlanID, cUnitTypeAbstractVillager, 1, 1, 1);
      aiPlanSetVariableVector(wallPlanID, cBuildWallPlanWallRingCenterPoint, 0, baseWallCenter);
      aiPlanSetVariableInt(wallPlanID, cBuildPlanLocationPreference, 0, cBuildingPlacementPreferenceFront);
      aiPlanSetVariableFloat(wallPlanID, cBuildWallPlanWallRingRadius, 0, baseWallRadius);
      aiPlanSetVariableInt(wallPlanID, cBuildWallPlanNumberOfGates, 0, numberOfGates);
      aiPlanSetBaseID(wallPlanID, kbBaseGetMainID(cMyID));
      aiPlanSetEscrowID(wallPlanID, cMilitaryEscrowID);
      aiPlanSetDesiredPriority(wallPlanID, 75);
      aiPlanSetActive(wallPlanID, true);
      //sendStatement(cPlayerRelationAllyExcludingSelf, cAICommPromptToAllyWhenIWallIn);
      debugBuildings("Enabling Wall Plan for Base ID: " + kbBaseGetMainID(cMyID));
   }
   xsEnableRule("forwardBaseStables");
   xsEnableRule("forwardBaseTowers");
   xsDisableSelf();
}
//==============================================================================
// forwardBaseStables
// Build stables and barracks at the forward base.
//==============================================================================
rule forwardBaseStables
inactive
minInterval 10
{
   int forwardBaseStablesVal = kbUnitQueryExecute(createSimpleUnitQuery(cUnitTypeAbstractStables, cMyID, 
   cUnitStateABQ, gForwardBaseLocation, 40.0));
   int forwardBaseBarracksVal = kbUnitQueryExecute(createSimpleUnitQuery(cUnitTypeBarracks, cMyID, 
   cUnitStateABQ, gForwardBaseLocation, 40.0));
   llVerboseEcho("Stables: "+forwardBaseStablesVal+" Base State: "+gForwardBaseState+"");
   if (gForwardBaseState == cForwardBaseStateNone)
   {
      return;
   } 
   
   if (gForwardBaseState == cForwardBaseStateActive && forwardBaseStablesVal < 1
      && aiPlanGetActive(gForwardBaseStablesPlan) == false) {
      aiPlanDestroy(gForwardBaseStablesPlan);
      gForwardBaseStablesPlan = createSpacedLocationBuildPlan(cUnitTypeStable, 1, 45, true, cMilitaryEscrowID, gForwardBaseLocation, 1);
      llVerboseEcho("Stables Plan created!");
   } else if (gForwardBaseState == cForwardBaseStateActive && forwardBaseStablesVal > 0) {
      // Start training at the forward base...
      if (kbBaseGetActive(cMyID, gIslandBaseID) == true) {
         updateSecondaryBaseMilitaryTrainPlans(gIslandBaseID);
      } else {
         updateSecondaryBaseMilitaryTrainPlans(gForwardBaseID);
      }
   }
   if (gForwardBaseState == cForwardBaseStateActive && forwardBaseBarracksVal < 1
      && aiPlanGetActive(gForwardBaseBarracksPlan) == false) {
      aiPlanDestroy(gForwardBaseBarracksPlan);
      gForwardBaseBarracksPlan = createSpacedLocationBuildPlan(cUnitTypeBarracks, 1, 45, true, cMilitaryEscrowID, gForwardBaseLocation, 1);
      llVerboseEcho("Barracks Plan created!");
   } else if (gForwardBaseState == cForwardBaseStateActive && forwardBaseBarracksVal > 0) {
      // Start training at the forward base...
      if (kbBaseGetActive(cMyID, gIslandBaseID) == true) {
         updateSecondaryBaseMilitaryTrainPlans(gIslandBaseID);
      } else {
         updateSecondaryBaseMilitaryTrainPlans(gForwardBaseID);
      }
   }
}
//==============================================================================
// forwardBaseTowers
// Build three towers at the forward base if we can.
//==============================================================================
rule forwardBaseTowers
inactive
minInterval 10
{
   int forwardBaseTowersVal = kbUnitQueryExecute(createSimpleUnitQuery(gTowerUnit, cMyID, cUnitStateABQ, 
   gForwardBaseLocation, 40.0));
   int additionalTowersAvailable = kbGetBuildLimit(cMyID, gTowerUnit) - kbUnitQueryExecute(createSimpleUnitQuery(gTowerUnit, cMyID, cUnitStateABQ));
   int desiredForwardBaseTowers = gLLForwardBaseTowerCount;
   if (gForwardBaseState == cForwardBaseStateNone)
   {
      return;
   }

   if (desiredForwardBaseTowers < 0)
   {
      desiredForwardBaseTowers = 0;
   }

   if (additionalTowersAvailable > desiredForwardBaseTowers) {
      additionalTowersAvailable = desiredForwardBaseTowers;
   }

   if ((gForwardBaseState == cForwardBaseStateActive) && (desiredForwardBaseTowers > 0) &&
      (forwardBaseTowersVal < desiredForwardBaseTowers) && (additionalTowersAvailable > 0)) {
      createSpacedLocationBuildPlan(gTowerUnit, additionalTowersAvailable, 50, true, cMilitaryEscrowID, gForwardBaseLocation, 1);
   }
}
//==============================================================================
// maxFortManager
// Maintain the maximum number of forts at all times.
//==============================================================================
// rule maxFortManager
// inactive
// minInterval 40
// {
//    static int fortPlan = -1;
//    int villagerPlan = -1;
//    int limit = 0;

//    limit = kbGetBuildLimit(cMyID, gFortUnit);
//    if (limit < 1)
//       return;

//    if (fortPlan < 0)
//    {
//       fortPlan = createSimpleMaintainPlan(gFortUnit, limit, true, -1, 1);
//       aiPlanSetDesiredPriority(fortPlan, 85);
//       //aiPlanSetVariableInt(missionaryPlan, cTrainPlanBuildFromType, 0, cUnitTypeChurch);
//       llVerboseEcho("Fort maintain plan!");
//    }
//    else
//    {
//       aiPlanSetVariableInt(fortPlan, cTrainPlanNumberToMaintain, 0, limit);
//    }
// }
//==============================================================================
// maxTowerManager
// Maintain the maximum number of towers at all times.
//==============================================================================
rule maxTowerManager
inactive
minInterval 10
{
   int limit = kbGetBuildLimit(cMyID, gTowerUnit);
   int unitQuery = createSimpleUnitQuery(gTowerUnit, cMyID, cUnitStateABQ);
   int numberFound = kbUnitQueryExecute(unitQuery);
   int age = kbGetAge();
//aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, gTowerUnit) < 0
   if (numberFound < limit && age >= cAge4)
   {
      createSimpleBuildPlan(gTowerUnit, 1, 75, false, cMilitaryEscrowID, kbBaseGetMainID(cMyID), 1);
   }
   updateWantedTowers();
}
//==============================================================================
// establishTradePostsWithNatives
// Double-check to make sure we are trying to maintain native alliances.
//==============================================================================
rule establishTradePostsWithNatives
inactive
minInterval 10
{
   int unitQuery = createSimpleUnitQuery(cUnitTypeSocket, cPlayerRelationAny, cUnitStateAny);
   int numberFound = kbUnitQueryExecute(unitQuery);
   vector mainBaseVec = kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID));
   int mainBaseGroupId = kbAreaGroupGetIDByPosition(mainBaseVec);
   vector unitLocation = cInvalidVector;
   int unitLocationId = -1;
   int unitLocationGroupId = -1;
   int unitID = -1;

   for (i = 0; < numberFound) {
      unitID = kbUnitQueryGetResult(unitQuery, i);
      unitLocation = kbUnitGetPosition(unitID);
      unitLocationId = kbAreaGetIDByPosition(unitLocation);
      unitLocationGroupId = kbAreaGroupGetIDByPosition(unitLocation);
      if (getUnitByLocation(cUnitTypeTradingPost, cPlayerRelationAny, cUnitStateABQ, unitLocation, 10.0) > 0)
      {
         continue;
      } else if (kbAreAreaGroupsPassableByLand(mainBaseGroupId, unitLocationGroupId) == true) {
         unitLocation = kbUnitGetPosition(unitID);
      }
   }
   
   if (unitLocation != cInvalidVector && aiPlanGetActive(gTradePostBuildingPlan) == false) {
      aiPlanDestroy(gTradePostBuildingPlan);
      gTradePostBuildingPlan = aiPlanCreate("Trading Post Build Plan", cPlanBuild);
      aiPlanSetVariableInt(gTradePostBuildingPlan, cBuildPlanBuildingTypeID, 0, cUnitTypeTradingPost);
      aiPlanSetVariableInt(gTradePostBuildingPlan, cBuildPlanSocketID, 0, unitID);

      int villagerQuery = createSimpleUnitQuery(cUnitTypeAbstractVillager, cMyID, cUnitStateAlive);
      aiPlanAddUnitType(gTradePostBuildingPlan, cUnitTypeAbstractVillager, 1, 1, 1);
      aiPlanAddUnit(gTradePostBuildingPlan, kbUnitQueryGetResult(villagerQuery, 0));
      aiPlanSetDesiredPriority(gTradePostBuildingPlan, 60);
      aiPlanSetActive(gTradePostBuildingPlan);
   }
}
//==============================================================================
// lakotaTeePeeManager
// Maintain the maximum number of teepees at all times.
//==============================================================================
rule lakotaTeePeeManager
active
minInterval 10
{
   if (cMyCiv != cCivXPSioux)
   {
      xsDisableSelf();
      return;
   }
   int limit = kbGetBuildLimit(cMyID, cUnitTypeTeepee);
   int unitQuery = createSimpleUnitQuery(cUnitTypeTeepee, cMyID, cUnitStateABQ);
   int numberFound = kbUnitQueryExecute(unitQuery);
   int age = kbGetAge();

   if (age == cAge1) {
      limit = 1;
   } else if (age == cAge2) {
      limit = 3;
   } else if (age == cAge3) {
      limit = 7;
   }

   if (numberFound < limit && aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, cUnitTypeTeepee) < 0)
   {
      createSimpleBuildPlan(cUnitTypeTeepee, 1, 75, false, cEconomyEscrowID, kbBaseGetMainID(cMyID), 1);
   }
}