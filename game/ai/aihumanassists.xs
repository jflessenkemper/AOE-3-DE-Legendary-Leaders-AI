//==============================================================================
/* aiHumanAssists.xs
   
   Create an AI for Definitive Edition that just prepares the kb & sets up some basic plans for the Human players to use for things like auto-scout and managing resource gatherers.

*/
//==============================================================================

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
   float healthThreshold = 0.10;
   float eliteSupportRadius = 24.0;

   int landQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int landCount = kbUnitQueryExecute(landQueryID);
   for (int i = 0; < landCount)
   {
      int unitID = kbUnitQueryGetResult(landQueryID, i);
      if (llGetTrackedSurrenderIndex(unitID) >= 0)
      {
         continue;
      }

      if (llCanUnitSurrender(unitID, healthThreshold, eliteSupportRadius) == false)
      {
         continue;
      }

      if (llHasEnemyPressureForSurrender(unitID) == false)
      {
         continue;
      }

      llTrackSurrenderingUnit(unitID);
   }

   int navalQueryID = createSimpleUnitQuery(cUnitTypeAbstractWarShip, cMyID, cUnitStateAlive);
   int navalCount = kbUnitQueryExecute(navalQueryID);
   for (int i = 0; < navalCount)
   {
      int unitID = kbUnitQueryGetResult(navalQueryID, i);
      if (llGetTrackedSurrenderIndex(unitID) >= 0)
      {
         continue;
      }

      if (llCanUnitSurrender(unitID, healthThreshold, eliteSupportRadius) == false)
      {
         continue;
      }

      if (llHasEnemyPressureForSurrender(unitID) == false)
      {
         continue;
      }

      llTrackSurrenderingUnit(unitID);
   }
}

rule legendaryHumanSurrenderMove
inactive
minInterval 2
{
   if (gLLSurrenderUnitIDs < 0)
   {
      return;
   }

   for (int i = 0; < cLLMaxSurrenderUnits)
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
               aiTaskUnitMove(unitID, returnLocation);
            }
            continue;
         }

         llReleaseSurrenderingUnit(unitID);
         aiTaskUnitMove(unitID, destination);
         continue;
      }

      if (distance(kbUnitGetPosition(unitID), destination) < cLLSurrenderArrivalRadius)
      {
         xsArraySetInt(gLLSurrenderStates, i, cLLSurrenderStateImprisoned);
         llReleaseSurrenderingUnit(unitID);
         aiTaskUnitMove(unitID, destination);
         continue;
      }

      llReleaseSurrenderingUnit(unitID);
      aiTaskUnitMove(unitID, destination);
   }
}

//==============================================================================
// main
//==============================================================================
void main(void)
{
   aiEcho("Human player assists AI startup.");
   aiEcho("Game type is " + aiGetGameType() + ", 0=Scn, 1=Saved, 2=Rand, 3=GC, 4=Cmpgn");
   aiEcho("Map name is " + cRandomMapName);

   aiRandSetSeed(-1);         // Set our random seed.  "-1" is a random init.
   kbAreaCalculate();         // Analyze the map, create area matrix
   aiSetEscrowsDisabled(true); // Disable escrows so we can have full control of our resources

   //-- set the default Resource Selector factor.
   kbSetTargetSelectorFactor(cTSFactorDistance, gTSFactorDistance);
   kbSetTargetSelectorFactor(cTSFactorPoint, gTSFactorPoint);
   kbSetTargetSelectorFactor(cTSFactorTimeToDone, gTSFactorTimeToDone);
   kbSetTargetSelectorFactor(cTSFactorBase, gTSFactorBase);
   kbSetTargetSelectorFactor(cTSFactorDanger, gTSFactorDanger);

   llEnsureSurrenderArrays();
   xsEnableRule("legendaryHumanSurrenderMonitor");
   xsEnableRule("legendaryHumanSurrenderMove");
}


