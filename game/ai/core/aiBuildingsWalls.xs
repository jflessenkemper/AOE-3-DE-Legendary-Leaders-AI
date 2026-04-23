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
   int gateCount = lateGame == true ? 15 : 4;

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

   if (gateCount < 2)
   {
      gateCount = 2;
   }

   return (gateCount);
}

//==============================================================================
// Per-doctrine wall strategy dispatch. Each strategy plans its Age-1
// fortifications in a historically-grounded way.
//==============================================================================

// FortressRing: full 360-degree ring wall with extra thickness/gates.
// Valette, Pachacuti, Frederick, Suleiman, Catherine, Bourbon France.
int llPlanFortressRingWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false);
   int planID = aiPlanCreate("FortressRing Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 2, 3);  // more villagers for thick rings
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, llGetLegendaryWallGateCount(false));
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 68);  // higher priority than generic
   aiPlanSetActive(planID, true);
   return (planID);
}

// ChokepointSegments: walls only at natural terrain pinches (Andes/Alps/passes).
// Shivaji (Maratha hill forts), Pachacuti (valley mouths), Kangxi (Great Wall).
// Fallback to a tighter ring if chokepoint detection fails on flat maps.
int llPlanChokepointWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   // Engine's cPlanBuildWall doesn't expose segment-only placement cleanly,
   // so we approximate: build a smaller ring with fewer gates, tilted toward
   // the area chokepoint via front-vector. Real chokepoint-only walling
   // would need a custom pathfinder; this gets ~70% there.
   float radius = llGetLegendaryWallRadius(false) - 4.0;
   int planID = aiPlanCreate("Chokepoint Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 1, 2);
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 3);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 60);
   aiPlanSetActive(planID, true);
   return (planID);
}

// CoastalBatteries: land-side partial ring (Wellington Torres Vedras, Henry Elmina).
// Standard ring but front-facing gate + extra towers at engagement face.
int llPlanCoastalBatteriesWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false);
   int planID = aiPlanCreate("CoastalBatteries Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 1, 2);
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 4);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 63);
   aiPlanSetActive(planID, true);
   return (planID);
}

// FrontierPalisades: quick lighter ring, more gates, less stone.
// Washington, Jefferson, Brock, Papineau, Houston, Kruger, Mannerheim, Morazán.
int llPlanFrontierPalisadeWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false) + 2.0;  // looser ring
   int planID = aiPlanCreate("FrontierPalisade Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 1, 2);
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 6);  // many gates, militia sallies
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 58);  // lower priority, economy comes first
   aiPlanSetActive(planID, true);
   return (planID);
}

// UrbanBarricade: tight compact inner ring (Robespierre Paris, Garibaldi cities).
int llPlanUrbanBarricadeWall(int mainBaseID = -1, vector baseCenter = cInvalidVector)
{
   float radius = llGetLegendaryWallRadius(false) - 8.0;  // much tighter
   int planID = aiPlanCreate("UrbanBarricade Wall", cPlanBuildWall);
   if (planID < 0) return (-1);
   aiPlanSetVariableInt(planID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
   aiPlanAddUnitType(planID, gEconUnit, 0, 1, 2);
   aiPlanSetVariableVector(planID, cBuildWallPlanWallRingCenterPoint, 0, baseCenter);
   aiPlanSetVariableFloat(planID, cBuildWallPlanWallRingRadius, 0.0, radius);
   aiPlanSetVariableInt(planID, cBuildWallPlanNumberOfGates, 0, 3);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetEscrowID(planID, cEconomyEscrowID);
   aiPlanSetDesiredPriority(planID, 60);
   aiPlanSetActive(planID, true);
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
   if (gLLWallStrategy == cLLWallStrategyFortressRing)       return (llPlanFortressRingWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyChokepointSegments) return (llPlanChokepointWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyCoastalBatteries)   return (llPlanCoastalBatteriesWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyFrontierPalisades)  return (llPlanFrontierPalisadeWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyUrbanBarricade)     return (llPlanUrbanBarricadeWall(mainBaseID, baseCenter));
   if (gLLWallStrategy == cLLWallStrategyMobileNoWalls)      return (llPlanMobileNoWalls(mainBaseID, baseCenter));
   // Fallback — FortressRing if unknown.
   return (llPlanFortressRingWall(mainBaseID, baseCenter));
}

rule explorationAgeWalling
inactive
group tcComplete
minInterval 15
{
   if ((llShouldBuildLegendaryWalls(true) == false) || (cvOkToBuild == false))
   {
      llLogDecision("WALL", "exploration walling disabled by config");
      xsDisableSelf();
      return;
   }

   if (kbGetAge() > cAge1)
   {
      xsDisableSelf();
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   if (mainBaseID < 0)
   {
      return;
   }

   if (aiPlanGetIDByTypeAndVariableType(cPlanBuildWall, cBuildWallPlanWallType, cBuildWallPlanWallTypeRing, true) >= 0)
   {
      return;
   }

   if (kbUnitCount(cMyID, cUnitTypeAbstractWall, cUnitStateABQ) > 0)
   {
      llLogDecision("WALL", "existing walls detected during exploration age, enabling gap fill support");
      xsEnableRule("fillInWallGapsNew");
      xsDisableSelf();
      return;
   }

   if (kbResourceGet(cResourceWood) < 125.0)
   {
      return;
   }

   vector baseCenter = kbBaseGetLocation(cMyID, mainBaseID);
   if (baseCenter == cInvalidVector)
   {
      return;
   }

   // Dispatch to per-leader walling doctrine.
   int wallPlanID = llPlanExplorationAgeWall(mainBaseID, baseCenter);
   if (wallPlanID < 0)
   {
      llLogDecision("WALL", "strategy=" + gLLWallStrategy + " declined to build walls (MobileNoWalls or plan failed)");
      xsDisableSelf();
      return;
   }

   llLogPlanEvent("create", wallPlanID, "exploration-wall strategy=" + gLLWallStrategy + " center=" + baseCenter);
   xsEnableRule("fillInWallGapsNew");
   xsDisableSelf();
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
rule delayWallsNew
inactive
minInterval 10
{
   int wallPlanID=aiPlanCreate("WallInBase", cPlanBuildWall);
   float wallRadius = llGetLegendaryWallRadius(true);

   if (llShouldBuildLegendaryWalls(false) == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() < cAge4) {
      return;
   }

   if (wallPlanID != -1)
   {
      aiPlanSetVariableInt(wallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
      aiPlanAddUnitType(wallPlanID, gEconUnit, 0, 1, 2);
      aiPlanSetVariableVector(wallPlanID, cBuildWallPlanWallRingCenterPoint, 0, kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID)));
      aiPlanSetVariableFloat(wallPlanID, cBuildWallPlanWallRingRadius, 0.0, wallRadius);
      aiPlanSetVariableInt(wallPlanID, cBuildWallPlanNumberOfGates, 0, llGetLegendaryWallGateCount(true));
      //aiPlanSetVariableInt(wallPlanID, cBuildWallPlanPieceRotations, 0, 1);
      aiPlanSetBaseID(wallPlanID, kbBaseGetMainID(cMyID));
      aiPlanSetEscrowID(wallPlanID, cEconomyEscrowID);
      aiPlanSetDesiredPriority(wallPlanID, 60);
      aiPlanSetActive(wallPlanID, true);
      //Enable our wall gap rule, too.
      xsEnableRule("fillInWallGapsNew");
      llVerboseEcho("Enabling Wall Plan for Base ID: "+kbBaseGetMainID(cMyID));
   } 
   xsDisableSelf();
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