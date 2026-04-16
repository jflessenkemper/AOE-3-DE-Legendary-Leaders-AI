//==============================================================================
/* aiEliteTactics.xs

   Keeps non-elite troops screening elite units and heroes while under pressure.
   During active assaults, standard troops lead, elites follow close behind, and
   the explorer stays behind the elite line. If the explorer falls, elites break
   contact and the AI immediately tries to ransom the leader back from home.
*/
//==============================================================================

extern int gLLEliteGuardPlanID = -1;
extern int gLLEliteGuardAnchorUnitID = -1;
extern int gLLEliteSupportPlanID = -1;
extern int gLLEliteSupportAttackPlanID = -1;
extern int gLLEliteSupportLastRefreshTime = -1;

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

vector llGetEliteRetreatPoint(void)
{
   int mainBaseID = kbBaseGetMainID(cMyID);
   vector retreatPoint = kbBaseGetMilitaryGatherPoint(cMyID, mainBaseID);
   if (retreatPoint == cInvalidVector)
   {
      retreatPoint = kbBaseGetLocation(cMyID, mainBaseID);
   }

   return (retreatPoint);
}

vector llGetAssaultOffsetPoint(vector gatherPoint = cInvalidVector, vector targetPoint = cInvalidVector, float offset = 0.0)
{
   if (targetPoint == cInvalidVector)
   {
      return (cInvalidVector);
   }

   if (gatherPoint == cInvalidVector)
   {
      gatherPoint = llGetEliteRetreatPoint();
   }

   if ((gatherPoint == cInvalidVector) || (distance(gatherPoint, targetPoint) < 4.0) || (offset <= 0.0))
   {
      return (targetPoint);
   }

   return (targetPoint - (xsVectorNormalize(targetPoint - gatherPoint) * offset));
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

int llGetTotalEliteTroopCount(void)
{
   int count = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
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

int llGetPrimaryLandAttackPlanID(void)
{
   int numPlans = aiPlanGetActiveCount();
   for (int i = 0; < numPlans; i++)
   {
      int planID = aiPlanGetIDByActiveIndex(i);
      if (aiPlanGetType(planID) != cPlanCombat)
      {
         continue;
      }

      if (aiPlanGetVariableInt(planID, cCombatPlanCombatType, 0) != cCombatPlanCombatTypeAttack)
      {
         continue;
      }

      if (aiPlanGetParentID(planID) >= 0)
      {
         continue;
      }

      if ((planID == gNavyAttackPlan) || (planID == gLandPatrolPlan) || (planID == gWaterPatrolPlan) ||
          (planID == gWaterDockAttackPlan) || (planID == gWarshipExplorePlan) || (planID == gIslandAssaultPlanID) ||
          (planID == gKOTHCombatPlan) || (planID == gKOTHGuardPlan) || (planID == gIslandSearchPlanID) ||
          (planID == gLLEliteSupportPlanID))
      {
         continue;
      }

      return (planID);
   }

   return (-1);
}

vector llGetAttackPlanGatherPoint(int attackPlanID = -1)
{
   if (attackPlanID < 0)
   {
      return (cInvalidVector);
   }

   vector gatherPoint = aiPlanGetVariableVector(attackPlanID, cCombatPlanGatherPoint, 0);
   if (gatherPoint != cInvalidVector)
   {
      return (gatherPoint);
   }

   return (llGetEliteRetreatPoint());
}

vector llGetAttackPlanTargetPoint(int attackPlanID = -1)
{
   if (attackPlanID < 0)
   {
      return (cInvalidVector);
   }

   vector targetPoint = aiPlanGetVariableVector(attackPlanID, cCombatPlanTargetPoint, 0);
   if (targetPoint != cInvalidVector)
   {
      return (targetPoint);
   }

   int targetPlayer = aiPlanGetVariableInt(attackPlanID, cCombatPlanTargetPlayerID, 0);
   int targetBaseID = aiPlanGetVariableInt(attackPlanID, cCombatPlanTargetBaseID, 0);
   if ((targetPlayer >= 0) && (targetBaseID >= 0))
   {
      targetPoint = kbBaseGetLocation(targetPlayer, targetBaseID);
   }

   return (targetPoint);
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

void llDestroyEliteSupportPlan(void)
{
   if (gLLEliteSupportPlanID >= 0)
   {
      aiPlanDestroy(gLLEliteSupportPlanID);
   }

   gLLEliteSupportPlanID = -1;
   gLLEliteSupportAttackPlanID = -1;
   gLLEliteSupportLastRefreshTime = -1;
}

void llResetExplorerControlToBase(void)
{
   if (gExplorerControlPlan < 0)
   {
      return;
   }

   vector retreatPoint = llGetEliteRetreatPoint();
   if (retreatPoint == cInvalidVector)
   {
      return;
   }

   aiPlanSetVariableVector(gExplorerControlPlan, cCombatPlanTargetPoint, 0, retreatPoint);
}

void llPositionExplorerBehindArmy(vector rearPoint = cInvalidVector)
{
   if (rearPoint == cInvalidVector)
   {
      return;
   }

   if (gExplorerControlPlan >= 0)
   {
      aiPlanSetVariableVector(gExplorerControlPlan, cCombatPlanTargetPoint, 0, rearPoint);
   }

   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive);
   int heroCount = kbUnitQueryExecute(heroQueryID);
   for (int i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      int currentPlanID = kbUnitGetPlanID(heroID);
      if ((currentPlanID >= 0) && (currentPlanID != gExplorerControlPlan))
      {
         aiPlanRemoveUnit(currentPlanID, heroID);
      }
      aiTaskUnitMove(heroID, rearPoint);
   }
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

   vector retreatPoint = llGetEliteRetreatPoint();
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

void llRetreatAllEliteUnits(void)
{
   vector retreatPoint = llGetEliteRetreatPoint();
   if (retreatPoint == cInvalidVector)
   {
      return;
   }

   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive);
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

   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
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

   llResetExplorerControlToBase();
   debugLegendaryLeaders("all elite units were ordered to retreat after the explorer fell.");
}

void llTryRansomExplorer(void)
{
   if (aiGetFallenExplorerID() < 0)
   {
      return;
   }

   if (aiPlanGetIDByTypeAndVariableType(cPlanResearch, cResearchPlanProtoUnitCommandID, cProtoUnitCommandRansomExplorer) >= 0)
   {
      return;
   }

   int tcID = getUnit(cUnitTypeTownCenter, cMyID, cUnitStateAlive);
   if (tcID < 0)
   {
      return;
   }

   createProtoUnitCommandResearchPlan(cProtoUnitCommandRansomExplorer, tcID, cMilitaryEscrowID, 95, 95);
   debugLegendaryLeaders("queued explorer ransom through the town center command after losing the leader.");
}

void llRebuildEliteSupportPlan(int attackPlanID = -1, vector gatherPoint = cInvalidVector, vector elitePoint = cInvalidVector,
   int desiredEliteCount = 1)
{
   if ((attackPlanID < 0) || (elitePoint == cInvalidVector) || (desiredEliteCount <= 0))
   {
      llDestroyEliteSupportPlan();
      return;
   }

   llDestroyEliteSupportPlan();

   int mainBaseID = kbBaseGetMainID(cMyID);
   int planID = aiPlanCreate("Legendary Elite Support", cPlanCombat);
   aiPlanSetVariableInt(planID, cCombatPlanCombatType, 0, cCombatPlanCombatTypeDefend);
   aiPlanSetVariableInt(planID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
   aiPlanSetVariableVector(planID, cCombatPlanTargetPoint, 0, elitePoint);
   aiPlanSetVariableVector(planID, cCombatPlanGatherPoint, 0, gatherPoint);
   aiPlanSetVariableFloat(planID, cCombatPlanTargetEngageRange, 0, 24.0);
   aiPlanSetVariableFloat(planID, cCombatPlanGatherDistance, 0, 12.0);
   aiPlanSetVariableInt(planID, cCombatPlanRefreshFrequency, 0, 200);
   aiPlanSetVariableInt(planID, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeNone);
   aiPlanSetDesiredPriority(planID, 82);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetInitialPosition(planID, gatherPoint);

   int addedUnits = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == false)
      {
         continue;
      }

      vector unitLocation = kbUnitGetPosition(unitID);
      int currentPlanID = kbUnitGetPlanID(unitID);
      if ((currentPlanID != attackPlanID) && (currentPlanID != gLLEliteSupportPlanID) &&
          ((distance(unitLocation, elitePoint) > 60.0) && (distance(unitLocation, gatherPoint) > 55.0)))
      {
         continue;
      }

      if ((currentPlanID >= 0) && (currentPlanID != planID))
      {
         aiPlanRemoveUnit(currentPlanID, unitID);
      }

      aiPlanAddUnitType(planID, kbUnitGetProtoUnitID(unitID), 0, 0, 1);
      if (aiPlanAddUnit(planID, unitID) == true)
      {
         addedUnits = addedUnits + 1;
      }

      if (addedUnits >= desiredEliteCount)
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
   gLLEliteSupportPlanID = planID;
   gLLEliteSupportAttackPlanID = attackPlanID;
   gLLEliteSupportLastRefreshTime = xsGetTime();
   debugLegendaryLeaders("created elite support plan " + planID + " for attack plan " + attackPlanID +
      " with " + addedUnits + " elite units guarding the second line.");
}

bool llHandleEliteAssaultFormation(int attackPlanID = -1)
{
   if (attackPlanID < 0)
   {
      llDestroyEliteSupportPlan();
      return (false);
   }

   vector gatherPoint = llGetAttackPlanGatherPoint(attackPlanID);
   vector targetPoint = llGetAttackPlanTargetPoint(attackPlanID);
   if ((gatherPoint == cInvalidVector) || (targetPoint == cInvalidVector))
   {
      llDestroyEliteSupportPlan();
      return (false);
   }

   int nonEliteCount = llGetTotalNonEliteTroopCount();
   int eliteCount = llGetTotalEliteTroopCount();
   int totalArmyCount = nonEliteCount + eliteCount;
   bool largeArmy = ((nonEliteCount >= 12) && (totalArmyCount >= 18));

   float eliteOffset = 7.0;
   float explorerOffset = 14.0;
   int desiredEliteCount = 1;
   if (largeArmy == true)
   {
      eliteOffset = 13.0;
      explorerOffset = 22.0;
      desiredEliteCount = eliteCount;
      if (desiredEliteCount > 6)
      {
         desiredEliteCount = 6;
      }
   }
   else if (eliteCount > 1)
   {
      desiredEliteCount = 2;
   }

   vector elitePoint = llGetAssaultOffsetPoint(gatherPoint, targetPoint, eliteOffset);
   vector explorerPoint = llGetAssaultOffsetPoint(gatherPoint, targetPoint, explorerOffset);

   llPositionExplorerBehindArmy(explorerPoint);

   if ((nonEliteCount <= 0) || (eliteCount <= 0))
   {
      llDestroyEliteSupportPlan();
      return (true);
   }

   if ((gLLEliteSupportPlanID < 0) || (gLLEliteSupportAttackPlanID != attackPlanID) ||
       (xsGetTime() - gLLEliteSupportLastRefreshTime >= 15000))
   {
      llRebuildEliteSupportPlan(attackPlanID, gatherPoint, elitePoint, desiredEliteCount);
   }
   else
   {
      aiPlanSetVariableVector(gLLEliteSupportPlanID, cCombatPlanTargetPoint, 0, elitePoint);
      aiPlanSetVariableVector(gLLEliteSupportPlanID, cCombatPlanGatherPoint, 0, gatherPoint);
   }

   return (true);
}

rule legendaryEliteGuardMonitor
inactive
minInterval 5
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (aiGetFallenExplorerID() >= 0)
   {
      llDestroyEliteGuardPlan();
      llDestroyEliteSupportPlan();
      llRetreatAllEliteUnits();
      llTryRansomExplorer();
      return;
   }

   int attackPlanID = llGetPrimaryLandAttackPlanID();
   if (attackPlanID >= 0)
   {
      llDestroyEliteGuardPlan();
      if (llHandleEliteAssaultFormation(attackPlanID) == true)
      {
         return;
      }
   }
   else
   {
      llDestroyEliteSupportPlan();
      llResetExplorerControlToBase();
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