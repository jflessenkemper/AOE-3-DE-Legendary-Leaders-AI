//==============================================================================
/* aiHumanAssists.xs
   
   Create an AI for Definitive Edition that just prepares the kb & sets up some basic plans for the Human players to use for things like auto-scout and managing resource gatherers.

*/
//==============================================================================

mutable vector getStartingLocation(void) { return (kbGetPlayerStartingPosition(cMyID)); }

mutable void selectTowerBuildPlanPosition(int buildPlan = -1, int baseID = -1) {}
mutable void selectShrineBuildPlanPosition(int planID = -1, int baseID = -1) {}
mutable void selectTorpBuildPlanPosition(int planID = -1, int baseID = -1) {}
mutable void selectTCBuildPlanPosition(int buildPlan = -1, int baseID = -1) {}
mutable void selectTeepeeBuildPlanPosition(int buildPlan = -1, int baseID = -1) {}
mutable bool selectTribalMarketplaceBuildPlanPosition(int buildPlan = -1, int baseID = -1) { return (false); }
mutable bool selectFieldBuildPlanPosition(int planID = -1, int baseID = -1) { return (false); }
mutable void selectMountainMonasteryBuildPlanPosition(int planID = -1, int baseID = -1) {}
mutable void selectGranaryBuildPlanPosition(int planID = -1, int baseID = -1) {}
mutable void selectClosestBuildPlanPosition(int planID = -1, int baseID = -1, int puid = -1) {}
mutable bool selectBuildPlanPosition(int planID = -1, int puid = -1, int baseID = -1) { return (false); }
mutable bool addBuilderToPlan(int planID = -1, int puid = -1, int numberBuilders = 1) { return (false); }
mutable void sendStatement(int playerIDorRelation = -1, int commPromptID = -1, vector vec = cInvalidVector) {}
mutable void sendChatLine(int playerIDorRelation = -1, string message = "") {}
mutable void llSendPrisonAlertToPlayer(int playerID = -1, vector prisonLocation = cInvalidVector, string alertMessage = "") {}
mutable void llSendEnemyPrisonTaunt(vector prisonLocation = cInvalidVector) {}

include "aiHeader.xs";
include "core\aiGlobals.xs";
include "core\aiUtilities.xs";
include "core\aiPrisoners.xs";

extern float gTSFactorDistance = -200.0;  // negative is good
extern float gTSFactorPoint = 10.0;			// positive is good
extern float gTSFactorTimeToDone = 0.0;	// positive is good
extern float gTSFactorBase = 100.0;			// positive is good
extern float gTSFactorDanger = -10.0;		// negative is good

vector llGetHumanSurrenderDestination(int unitID = -1)
{
   if (unitID < 0)
   {
      return (cInvalidVector);
   }

   int enemyPlayerID = llGetCapturingPlayerForUnit(unitID);
   if (enemyPlayerID >= 0)
   {
      vector enemyShipmentLocation = llGetShipmentGatherLocationForPlayer(enemyPlayerID);
      if (enemyShipmentLocation != cInvalidVector)
      {
         return (enemyShipmentLocation);
      }
   }

   int enemyQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cPlayerRelationEnemyNotGaia,
      cUnitStateAlive, kbUnitGetPosition(unitID), 36.0);
   if (kbUnitQueryExecute(enemyQueryID) > 0)
   {
      return (kbUnitGetPosition(kbUnitQueryGetResult(enemyQueryID, 0)));
   }

   int tcQueryID = createSimpleUnitQuery(cUnitTypeTownCenter, cPlayerRelationEnemyNotGaia, cUnitStateAlive,
      kbUnitGetPosition(unitID), 300.0);
   if (kbUnitQueryExecute(tcQueryID) > 0)
   {
      return (kbUnitGetPosition(kbUnitQueryGetResult(tcQueryID, 0)));
   }

   return (cInvalidVector);
}

rule legendaryHumanSurrenderMonitor
inactive
minInterval 8
{
   llLogRuleTick("legendaryHumanSurrenderMonitor");
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   float healthThreshold = 0.25;
   float eliteSupportRadius = 24.0;
   int unitID = -1;

   int landQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int landCount = kbUnitQueryExecute(landQueryID);
   int i = 0;
   for (i = 0; < landCount)
   {
      unitID = kbUnitQueryGetResult(landQueryID, i);
      if (llGetTrackedSurrenderIndex(unitID) >= 0)
      {
         continue;
      }

      if (llHasEnemyPressureForSurrender(unitID) == false)
      {
         continue;
      }

      string surrenderBlockReason = llGetUnitSurrenderBlockReason(unitID, healthThreshold, eliteSupportRadius);
      if (surrenderBlockReason != "")
      {
         llLogSurrenderBlock("human", unitID, surrenderBlockReason);
         continue;
      }

      llTrackSurrenderingUnit(unitID);
   }

   int navalQueryID = createSimpleUnitQuery(cUnitTypeAbstractWarShip, cMyID, cUnitStateAlive);
   int navalCount = kbUnitQueryExecute(navalQueryID);
   i = 0;
   for (i = 0; < navalCount)
   {
      unitID = kbUnitQueryGetResult(navalQueryID, i);
      if (llGetTrackedSurrenderIndex(unitID) >= 0)
      {
         continue;
      }

      if (llHasEnemyPressureForSurrender(unitID) == false)
      {
         continue;
      }

      string navalSurrenderBlockReason = llGetUnitSurrenderBlockReason(unitID, healthThreshold, eliteSupportRadius);
      if (navalSurrenderBlockReason != "")
      {
         llLogSurrenderBlock("human", unitID, navalSurrenderBlockReason);
         continue;
      }

      llTrackSurrenderingUnit(unitID);
   }
}

rule legendaryHumanSurrenderMove
inactive
minInterval 2
{
   llLogRuleTick("legendaryHumanSurrenderMove");
   if ((gLLPrisonSystemEnabled == false) || (gLLSurrenderUnitIDs < 0))
   {
      return;
   }

   int i = 0;
   for (i = 0; < cLLMaxSurrenderUnits)
   {
      int unitID = xsArrayGetInt(gLLSurrenderUnitIDs, i);
      if (unitID < 0)
      {
         continue;
      }

      if (kbUnitGetHealth(unitID) <= 0.0)
      {
         llClearTrackedSurrenderIndex(i);
         continue;
      }

      int surrenderTime = xsArrayGetInt(gLLSurrenderTimes, i);
      int trackedDuration = xsGetTime() - surrenderTime;
      int surrenderState = xsArrayGetInt(gLLSurrenderStates, i);
      int captorPlayerID = xsArrayGetInt(gLLSurrenderCaptors, i);
      int originalOwnerID = xsArrayGetInt(gLLSurrenderOriginalOwners, i);

      if (trackedDuration > cLLMaxSurrenderLifetime)
      {
         llClearTrackedSurrenderIndex(i);
         continue;
      }

      if (captorPlayerID < 0)
      {
         captorPlayerID = llGetCapturingPlayerForUnit(unitID);
         xsArraySetInt(gLLSurrenderCaptors, i, captorPlayerID);
      }

      vector destination = llGetPrisonHoldingPoint(captorPlayerID, i);
      if (destination == cInvalidVector)
      {
         destination = llGetHumanSurrenderDestination(unitID);
         if (destination == cInvalidVector)
         {
            continue;
         }
      }

      if (surrenderState == cLLSurrenderStateImprisoned)
      {
         if ((originalOwnerID >= 0) && (llHasFriendlyExplorerNearby(originalOwnerID, kbUnitGetPosition(unitID), cLLPrisonReclaimRadius) == true))
         {
            vector returnLocation = llGetReturnLocationForPlayer(originalOwnerID);
            llClearTrackedSurrenderIndex(i);
            if (returnLocation != cInvalidVector)
            {
               llLogUnitAction("human-surrender-return", unitID, "destination=" + returnLocation);
               aiTaskUnitMove(unitID, returnLocation);
            }
            continue;
         }

         llReleaseSurrenderingUnit(unitID);
         llLogUnitAction("human-surrender-imprisoned-move", unitID, "destination=" + destination);
         aiTaskUnitMove(unitID, destination);
         continue;
      }

      if (distance(kbUnitGetPosition(unitID), destination) < cLLSurrenderArrivalRadius)
      {
         xsArraySetInt(gLLSurrenderStates, i, cLLSurrenderStateImprisoned);
         llReleaseSurrenderingUnit(unitID);
         llLogUnitAction("human-surrender-arrival-move", unitID, "destination=" + destination);
         aiTaskUnitMove(unitID, destination);
         continue;
      }

      llReleaseSurrenderingUnit(unitID);
      llLogUnitAction("human-surrender-move", unitID, "destination=" + destination);
      aiTaskUnitMove(unitID, destination);
   }
}

//==============================================================================
// main
//==============================================================================
void main(void)
{
   llVerboseEcho("Human player assists AI startup.");
   llVerboseEcho("Game type is " + aiGetGameType() + ", 0=Scn, 1=Saved, 2=Rand, 3=GC, 4=Cmpgn");
   llVerboseEcho("Map name is " + cRandomMapName);

   aiRandSetSeed(-1);         // Set our random seed.  "-1" is a random init.
   kbAreaCalculate();         // Analyze the map, create area matrix
   aiSetEscrowsDisabled(true); // Disable escrows so we can have full control of our resources

   //-- set the default Resource Selector factor.
   kbSetTargetSelectorFactor(cTSFactorDistance, gTSFactorDistance);
   kbSetTargetSelectorFactor(cTSFactorPoint, gTSFactorPoint);
   kbSetTargetSelectorFactor(cTSFactorTimeToDone, gTSFactorTimeToDone);
   kbSetTargetSelectorFactor(cTSFactorBase, gTSFactorBase);
   kbSetTargetSelectorFactor(cTSFactorDanger, gTSFactorDanger);

   llLogEvent("RULE", "human assist rout rules disabled; player-controlled units keep manual control");
}


