//==============================================================================
/* aiEliteTactics.xs

   Keeps non-elite troops screening elite units and heroes while under pressure.
   Once the screen collapses, elite withdrawal depends on leader playstyle.
*/
//==============================================================================

extern int gLLEliteGuardPlanID = -1;
extern int gLLEliteGuardAnchorUnitID = -1;

int llGetPlaystyleBucket(void)
{
   if (btOffenseDefense >= 0.35)
   {
      return (2);
   }

   if (btOffenseDefense <= -0.25)
   {
      return (0);
   }

   return (1);
}

int llGetNearbyEnemyPressureCount(vector location = cInvalidVector, float radius = 28.0)
{
   if ((location == cInvalidVector) || (radius <= 0.0))
   {
      return (0);
   }

   int enemyQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cPlayerRelationEnemyNotGaia,
      cUnitStateAlive, location, radius);
   return (kbUnitQueryExecute(enemyQueryID));
}

int llGetNearbyNonEliteSupportCount(vector location = cInvalidVector, float radius = 26.0)
{
   if ((location == cInvalidVector) || (radius <= 0.0))
   {
      return (0);
   }

   int count = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive, location, radius);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == true)
      {
         continue;
      }

      count = count + 1;
   }

   return (count);
}

int llGetTotalNonEliteTroopCount(void)
{
   int count = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == true)
      {
         continue;
      }

      count = count + 1;
   }

   return (count);
}

int llGetNearbyEliteCoreCount(vector location = cInvalidVector, float radius = 30.0)
{
   if ((location == cInvalidVector) || (radius <= 0.0))
   {
      return (0);
   }

   int count = 0;

   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive, location, radius);
   count = count + kbUnitQueryExecute(heroQueryID);

   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive, location, radius);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == false)
      {
         continue;
      }

      count = count + 1;
   }

   return (count);
}

int llGetThreatenedEliteAnchorID(void)
{
   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive);
   int heroCount = kbUnitQueryExecute(heroQueryID);
   for (int i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      if (llGetNearbyEnemyPressureCount(kbUnitGetPosition(heroID), 28.0) > 0)
      {
         return (heroID);
      }
   }

   int eliteQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int eliteCount = kbUnitQueryExecute(eliteQueryID);
   for (int i = 0; < eliteCount)
   {
      int unitID = kbUnitQueryGetResult(eliteQueryID, i);
      if (llIsEliteUnit(unitID) == false)
      {
         continue;
      }

      if (llGetNearbyEnemyPressureCount(kbUnitGetPosition(unitID), 28.0) > 0)
      {
         return (unitID);
      }
   }

   return (-1);
}

void llDestroyEliteGuardPlan(void)
{
   if (gLLEliteGuardPlanID >= 0)
   {
      aiPlanDestroy(gLLEliteGuardPlanID);
   }

   gLLEliteGuardPlanID = -1;
   gLLEliteGuardAnchorUnitID = -1;
}

void llRebuildEliteGuardPlan(int anchorUnitID = -1)
{
   if (anchorUnitID < 0)
   {
      llDestroyEliteGuardPlan();
      return;
   }

   vector anchorLocation = kbUnitGetPosition(anchorUnitID);
   if (anchorLocation == cInvalidVector)
   {
      llDestroyEliteGuardPlan();
      return;
   }

   llDestroyEliteGuardPlan();

   int planID = aiPlanCreate("Legendary Elite Guard", cPlanCombat);
   aiPlanSetVariableInt(planID, cCombatPlanCombatType, 0, cCombatPlanCombatTypeDefend);
   aiPlanSetVariableInt(planID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
   aiPlanSetVariableVector(planID, cCombatPlanTargetPoint, 0, anchorLocation);
   aiPlanSetVariableFloat(planID, cCombatPlanTargetEngageRange, 0, 26.0);
   aiPlanSetVariableFloat(planID, cCombatPlanGatherDistance, 0, 14.0);
   aiPlanSetVariableInt(planID, cCombatPlanRefreshFrequency, 0, 200);
   aiPlanSetVariableInt(planID, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeNone);
   aiPlanSetDesiredPriority(planID, 70);

   int addedUnits = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive, anchorLocation, 34.0);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == true)
      {
         continue;
      }

      int currentPlanID = kbUnitGetPlanID(unitID);
      if (currentPlanID >= 0)
      {
         aiPlanRemoveUnit(currentPlanID, unitID);
      }

      aiPlanAddUnitType(planID, kbUnitGetProtoUnitID(unitID), 0, 0, 1);
      if (aiPlanAddUnit(planID, unitID) == true)
      {
         addedUnits = addedUnits + 1;
      }

      if (addedUnits >= 16)
      {
         break;
      }
   }

   if (addedUnits <= 0)
   {
      aiPlanDestroy(planID);
      return;
   }

   aiPlanSetActive(planID);
   gLLEliteGuardPlanID = planID;
   gLLEliteGuardAnchorUnitID = anchorUnitID;
   debugLegendaryLeaders("created elite guard plan " + planID + " around anchor unit " + anchorUnitID +
      " using " + addedUnits + " non-elite troops.");
}

void llRetreatEliteCore(int anchorUnitID = -1, float radius = 36.0)
{
   if (anchorUnitID < 0)
   {
      return;
   }

   vector anchorLocation = kbUnitGetPosition(anchorUnitID);
   if (anchorLocation == cInvalidVector)
   {
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   vector retreatPoint = kbBaseGetMilitaryGatherPoint(cMyID, mainBaseID);
   if (retreatPoint == cInvalidVector)
   {
      retreatPoint = kbBaseGetLocation(cMyID, mainBaseID);
   }
   if (retreatPoint == cInvalidVector)
   {
      return;
   }

   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive, anchorLocation, radius);
   int heroCount = kbUnitQueryExecute(heroQueryID);
   for (int i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      int currentPlanID = kbUnitGetPlanID(heroID);
      if (currentPlanID >= 0)
      {
         aiPlanRemoveUnit(currentPlanID, heroID);
      }
      aiTaskUnitMove(heroID, retreatPoint);
   }

   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive, anchorLocation, radius);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == false)
      {
         continue;
      }

      int currentPlanID = kbUnitGetPlanID(unitID);
      if (currentPlanID >= 0)
      {
         aiPlanRemoveUnit(currentPlanID, unitID);
      }
      aiTaskUnitMove(unitID, retreatPoint);
   }

   debugLegendaryLeaders("elite core around anchor unit " + anchorUnitID + " ordered to retreat to " + retreatPoint + ".");
}

rule legendaryEliteGuardMonitor
inactive
minInterval 5
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   int anchorUnitID = llGetThreatenedEliteAnchorID();
   if (anchorUnitID < 0)
   {
      llDestroyEliteGuardPlan();
      return;
   }

   vector anchorLocation = kbUnitGetPosition(anchorUnitID);
   int enemyPressure = llGetNearbyEnemyPressureCount(anchorLocation, 28.0);
   if (enemyPressure <= 0)
   {
      llDestroyEliteGuardPlan();
      return;
   }

   int nearbyScreenCount = llGetNearbyNonEliteSupportCount(anchorLocation, 26.0);
   if (nearbyScreenCount > 0)
   {
      if ((gLLEliteGuardPlanID < 0) || (gLLEliteGuardAnchorUnitID != anchorUnitID))
      {
         llRebuildEliteGuardPlan(anchorUnitID);
      }
      else
      {
         aiPlanSetVariableVector(gLLEliteGuardPlanID, cCombatPlanTargetPoint, 0, anchorLocation);
      }
      return;
   }

   llDestroyEliteGuardPlan();

   if (llGetTotalNonEliteTroopCount() > 0)
   {
      return;
   }

   int playstyleBucket = llGetPlaystyleBucket();
   if (playstyleBucket >= 2)
   {
      debugLegendaryLeaders("elite core remains engaged because leader playstyle is aggressive.");
      return;
   }

   if ((playstyleBucket == 1) && (enemyPressure <= llGetNearbyEliteCoreCount(anchorLocation, 30.0)))
   {
      debugLegendaryLeaders("elite core remains engaged because balanced leader still has a favorable local fight.");
      return;
   }

   llRetreatEliteCore(anchorUnitID);
}