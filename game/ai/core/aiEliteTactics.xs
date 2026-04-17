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
extern int gLLExplorerEscortPlanID = -1;
extern int gLLExplorerEscortAttackPlanID = -1;
extern int gLLExplorerEscortLastRefreshTime = -1;
float gLLExplorerProtectionOverride = -1.0;
float gLLDecapitationOverride = -1.0;
int gLLExplorerEscortBonus = 0;
float gLLExplorerRearOffsetBonus = 0.0;

float llClamp01(float value = 0.0)
{
   if (value < 0.0)
   {
      return (0.0);
   }

   if (value > 1.0)
   {
      return (1.0);
   }

   return (value);
}

void llSetLeaderTacticalDoctrine(float protectionOverride = -1.0, float decapitationOverride = -1.0,
   int escortBonus = 0, float rearOffsetBonus = 0.0)
{
   gLLExplorerProtectionOverride = protectionOverride;
   gLLDecapitationOverride = decapitationOverride;
   gLLExplorerEscortBonus = escortBonus;
   gLLExplorerRearOffsetBonus = rearOffsetBonus;
}

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

float llGetExplorerProtectionBias(void)
{
   if (gLLExplorerProtectionOverride >= 0.0)
   {
      return (llClamp01(gLLExplorerProtectionOverride));
   }

   float protectionBias = 0.55 - (btOffenseDefense * 0.35) + (btBiasInf * 0.12) + (btBiasArt * 0.10) -
      (btBiasCav * 0.14) - (btBiasNative * 0.06);

   if (llGetPlaystyleBucket() == 0)
   {
      protectionBias = protectionBias + 0.12;
   }
   else if (llGetPlaystyleBucket() == 2)
   {
      protectionBias = protectionBias - 0.08;
   }

   return (llClamp01(protectionBias));
}

float llGetDecapitationBias(void)
{
   if (gLLDecapitationOverride >= 0.0)
   {
      return (llClamp01(gLLDecapitationOverride));
   }

   float decapitationBias = 0.20 + (btOffenseDefense * 0.38) + (btBiasCav * 0.24) + (btBiasNative * 0.10) -
      (btBiasArt * 0.12) - (btBiasInf * 0.08);

   if (llGetPlaystyleBucket() == 2)
   {
      decapitationBias = decapitationBias + 0.10;
   }
   else if (llGetPlaystyleBucket() == 0)
   {
      decapitationBias = decapitationBias - 0.14;
   }

   return (llClamp01(decapitationBias));
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
   int i = 0;
   for (i = 0; < numberFound)
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
   int i = 0;
   for (i = 0; < numberFound)
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
   int i = 0;
   for (i = 0; < numberFound)
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
   int i = 0;
   for (i = 0; < numberFound)
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
   int i = 0;
   for (i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      if (llGetNearbyEnemyPressureCount(kbUnitGetPosition(heroID), 28.0) > 0)
      {
         return (heroID);
      }
   }

   int eliteQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int eliteCount = kbUnitQueryExecute(eliteQueryID);
   i = 0;
   for (i = 0; < eliteCount)
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
   int i = 0;
   for (i = 0; < numPlans)
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

vector llGetAttackPlanStrategicPoint(int attackPlanID = -1)
{
   if (attackPlanID < 0)
   {
      return (cInvalidVector);
   }

   int targetPlayer = aiPlanGetVariableInt(attackPlanID, cCombatPlanTargetPlayerID, 0);
   int targetBaseID = aiPlanGetVariableInt(attackPlanID, cCombatPlanTargetBaseID, 0);
   if ((targetPlayer >= 0) && (targetBaseID >= 0))
   {
      vector basePoint = kbBaseGetLocation(targetPlayer, targetBaseID);
      if (basePoint != cInvalidVector)
      {
         return (basePoint);
      }
   }

   return (llGetAttackPlanTargetPoint(attackPlanID));
}

int llGetPrimaryExplorerID(void)
{
   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, cMyID, cUnitStateAlive);
   if (kbUnitQueryExecute(heroQueryID) <= 0)
   {
      return (-1);
   }

   return (kbUnitQueryGetResult(heroQueryID, 0));
}

vector llGetEnemyArmyMassPoint(int targetPlayer = -1, vector nearPoint = cInvalidVector, float radius = 42.0)
{
   if (nearPoint == cInvalidVector)
   {
      return (cInvalidVector);
   }

   int playerRelation = targetPlayer >= 0 ? targetPlayer : cPlayerRelationEnemyNotGaia;
   int enemyQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, playerRelation, cUnitStateAlive, nearPoint, radius);
   int enemyCount = kbUnitQueryExecute(enemyQueryID);
   if (enemyCount <= 0)
   {
      return (cInvalidVector);
   }

   float xTotal = 0.0;
   float zTotal = 0.0;
   int i = 0;
   for (i = 0; < enemyCount)
   {
      vector unitPosition = kbUnitGetPosition(kbUnitQueryGetResult(enemyQueryID, i));
      xTotal = xTotal + xsVectorGetX(unitPosition);
      zTotal = zTotal + xsVectorGetZ(unitPosition);
   }

   return (xsVectorSet(xTotal / enemyCount, 0.0, zTotal / enemyCount));
}

int llGetBestEnemyExplorerStrikeID(int targetPlayer = -1, vector referencePoint = cInvalidVector, float searchRadius = 70.0,
   int maxEscortCount = 4)
{
   int playerRelation = targetPlayer >= 0 ? targetPlayer : cPlayerRelationEnemyNotGaia;
   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, playerRelation, cUnitStateAlive);
   int heroCount = kbUnitQueryExecute(heroQueryID);
   int bestHeroID = -1;
   float bestScore = 99999.0;

   int i = 0;
   for (i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      vector heroPosition = kbUnitGetPosition(heroID);
      if ((referencePoint != cInvalidVector) && (distance(referencePoint, heroPosition) > searchRadius))
      {
         continue;
      }

      int escortQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, kbUnitGetPlayerID(heroID), cUnitStateAlive,
         heroPosition, 18.0);
      int escortCount = kbUnitQueryExecute(escortQueryID);
      if (escortCount > maxEscortCount)
      {
         continue;
      }

      float score = escortCount * 8.0;
      if (referencePoint != cInvalidVector)
      {
         score = score + distance(referencePoint, heroPosition);
      }

      if (score < bestScore)
      {
         bestScore = score;
         bestHeroID = heroID;
      }
   }

   return (bestHeroID);
}

bool llIsEnemyExplorerInBattle(int heroID = -1, vector enemyArmyPoint = cInvalidVector, float battleRadius = 24.0)
{
   if (heroID < 0)
   {
      return (false);
   }

   vector heroPosition = kbUnitGetPosition(heroID);
   if (enemyArmyPoint == cInvalidVector)
   {
      return (llGetNearbyEnemyPressureCount(heroPosition, battleRadius) > 4);
   }

   if (distance(heroPosition, enemyArmyPoint) > battleRadius)
   {
      return (false);
   }

   return (llGetNearbyEnemyPressureCount(heroPosition, battleRadius) > 4);
}

void llDestroyEliteGuardPlan(void)
{
   if (gLLEliteGuardPlanID >= 0)
   {
      llLogPlanEvent("destroy", gLLEliteGuardPlanID, "name=Legendary Elite Guard");
      aiPlanDestroy(gLLEliteGuardPlanID);
   }

   gLLEliteGuardPlanID = -1;
   gLLEliteGuardAnchorUnitID = -1;
}

void llDestroyEliteSupportPlan(void)
{
   if (gLLEliteSupportPlanID >= 0)
   {
      llLogPlanEvent("destroy", gLLEliteSupportPlanID, "name=Legendary Elite Support");
      aiPlanDestroy(gLLEliteSupportPlanID);
   }

   gLLEliteSupportPlanID = -1;
   gLLEliteSupportAttackPlanID = -1;
   gLLEliteSupportLastRefreshTime = -1;
}

void llDestroyExplorerEscortPlan(void)
{
   if (gLLExplorerEscortPlanID >= 0)
   {
      llLogPlanEvent("destroy", gLLExplorerEscortPlanID, "name=Legendary Explorer Escort");
      aiPlanDestroy(gLLExplorerEscortPlanID);
   }

   gLLExplorerEscortPlanID = -1;
   gLLExplorerEscortAttackPlanID = -1;
   gLLExplorerEscortLastRefreshTime = -1;
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
   int i = 0;
   for (i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      int currentPlanID = kbUnitGetPlanID(heroID);
      if ((currentPlanID >= 0) && (currentPlanID != gExplorerControlPlan))
      {
         aiPlanRemoveUnit(currentPlanID, heroID);
      }
      llLogUnitAction("explorer-reposition", heroID, "destination=" + rearPoint);
      aiTaskUnitMove(heroID, rearPoint);
   }
}

void llRebuildExplorerEscortPlan(int attackPlanID = -1, vector gatherPoint = cInvalidVector, vector escortPoint = cInvalidVector,
   int desiredEscortCount = 0)
{
   if ((attackPlanID < 0) || (gatherPoint == cInvalidVector) || (escortPoint == cInvalidVector) || (desiredEscortCount <= 0))
   {
      llDestroyExplorerEscortPlan();
      return;
   }

   llDestroyExplorerEscortPlan();

   int mainBaseID = kbBaseGetMainID(cMyID);
   int planID = aiPlanCreate("Legendary Explorer Escort", cPlanCombat);
   llLogPlanEvent("create", planID, "name=Legendary Explorer Escort attackPlan=" + attackPlanID);
   aiPlanSetVariableInt(planID, cCombatPlanCombatType, 0, cCombatPlanCombatTypeDefend);
   aiPlanSetVariableInt(planID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
   aiPlanSetVariableVector(planID, cCombatPlanTargetPoint, 0, escortPoint);
   aiPlanSetVariableVector(planID, cCombatPlanGatherPoint, 0, gatherPoint);
   aiPlanSetVariableFloat(planID, cCombatPlanTargetEngageRange, 0, 16.0);
   aiPlanSetVariableFloat(planID, cCombatPlanGatherDistance, 0, 8.0);
   aiPlanSetVariableInt(planID, cCombatPlanRefreshFrequency, 0, 200);
   aiPlanSetVariableInt(planID, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeNone);
   aiPlanSetDesiredPriority(planID, 88);
   aiPlanSetBaseID(planID, mainBaseID);
   aiPlanSetInitialPosition(planID, gatherPoint);

   int addedUnits = 0;
   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   int i = 0;
   for (i = 0; < numberFound)
   {
      int unitID = kbUnitQueryGetResult(unitQueryID, i);
      if (llIsEliteUnit(unitID) == true)
      {
         continue;
      }

      int currentPlanID = kbUnitGetPlanID(unitID);
      if ((currentPlanID != attackPlanID) && (currentPlanID != gLLExplorerEscortPlanID))
      {
         continue;
      }

      vector unitLocation = kbUnitGetPosition(unitID);
      if ((distance(unitLocation, escortPoint) > 46.0) && (distance(unitLocation, gatherPoint) > 42.0))
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

      if (addedUnits >= desiredEscortCount)
      {
         break;
      }
   }

   if (addedUnits <= 0)
   {
      llLogPlanEvent("destroy", planID, "reason=no escort units added");
      aiPlanDestroy(planID);
      return;
   }

   aiPlanSetActive(planID);
   gLLExplorerEscortPlanID = planID;
   gLLExplorerEscortAttackPlanID = attackPlanID;
   gLLExplorerEscortLastRefreshTime = xsGetTime();
   debugLegendaryLeaders("created explorer escort plan " + planID + " for attack plan " + attackPlanID +
      " using " + addedUnits + " non-elite troops.");
}

vector llChooseAssaultObjectivePoint(int attackPlanID = -1, vector gatherPoint = cInvalidVector)
{
   vector strategicPoint = llGetAttackPlanStrategicPoint(attackPlanID);
   if (strategicPoint == cInvalidVector)
   {
      return (cInvalidVector);
   }

   int targetPlayer = aiPlanGetVariableInt(attackPlanID, cCombatPlanTargetPlayerID, 0);
   float decapitationBias = llGetDecapitationBias();
   float protectionBias = llGetExplorerProtectionBias();
   vector bulkPoint = llGetEnemyArmyMassPoint(targetPlayer, strategicPoint, 44.0);
   if (bulkPoint == cInvalidVector)
   {
      aiPlanSetVariableInt(attackPlanID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
      aiPlanSetVariableVector(attackPlanID, cCombatPlanTargetPoint, 0, strategicPoint);
      return (strategicPoint);
   }

   int enemyExplorerID = llGetBestEnemyExplorerStrikeID(targetPlayer, strategicPoint, 72.0,
      2 + xsFloor((1.0 - decapitationBias) * 4.0));
   if ((enemyExplorerID >= 0) && (decapitationBias >= 0.55) &&
       (llIsEnemyExplorerInBattle(enemyExplorerID, bulkPoint, 26.0) == true))
   {
      vector strikePoint = kbUnitGetPosition(enemyExplorerID);
      if ((distance(strikePoint, bulkPoint) <= 26.0) || (decapitationBias >= 0.80))
      {
         aiPlanSetVariableInt(attackPlanID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
         aiPlanSetVariableVector(attackPlanID, cCombatPlanTargetPoint, 0, strikePoint);
         debugLegendaryLeaders("assault objective shifted toward enemy explorer at " + strikePoint +
            " because leader doctrine favors decapitation strikes.");
         llSendLegendaryLeaderDecapitationLine(targetPlayer, 150000);
         return (strikePoint);
      }
   }

   aiPlanSetVariableInt(attackPlanID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
   aiPlanSetVariableVector(attackPlanID, cCombatPlanTargetPoint, 0, bulkPoint);
   if (protectionBias >= 0.45)
   {
      debugLegendaryLeaders("assault objective shifted onto the bulk enemy force to preserve leader escort integrity.");
   }
   llSendLegendaryLeaderBulkAssaultLine(targetPlayer, 150000);
   return (bulkPoint);
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
   llLogPlanEvent("create", planID, "name=Legendary Elite Guard anchorUnit=" + anchorUnitID);
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
   int i = 0;
   for (i = 0; < numberFound)
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
      llLogPlanEvent("destroy", planID, "reason=no guard units added");
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
   int i = 0;
   for (i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      int currentPlanID = kbUnitGetPlanID(heroID);
      if (currentPlanID >= 0)
      {
         aiPlanRemoveUnit(currentPlanID, heroID);
      }
      llLogUnitAction("elite-retreat-hero", heroID, "destination=" + retreatPoint);
      aiTaskUnitMove(heroID, retreatPoint);
   }

   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive, anchorLocation, radius);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   i = 0;
   for (i = 0; < numberFound)
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
      llLogUnitAction("elite-retreat-core", unitID, "destination=" + retreatPoint);
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
   int i = 0;
   for (i = 0; < heroCount)
   {
      int heroID = kbUnitQueryGetResult(heroQueryID, i);
      int currentPlanID = kbUnitGetPlanID(heroID);
      if (currentPlanID >= 0)
      {
         aiPlanRemoveUnit(currentPlanID, heroID);
      }
      llLogUnitAction("elite-global-retreat-hero", heroID, "destination=" + retreatPoint);
      aiTaskUnitMove(heroID, retreatPoint);
   }

   int unitQueryID = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   i = 0;
   for (i = 0; < numberFound)
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
      llLogUnitAction("elite-global-retreat-core", unitID, "destination=" + retreatPoint);
      aiTaskUnitMove(unitID, retreatPoint);
   }

   llResetExplorerControlToBase();
   debugLegendaryLeaders("all elite units were ordered to retreat after the explorer fell.");
   llSendLegendaryLeaderRetreatLine(cPlayerRelationEnemyNotGaia, 180000);
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
   llLogPlanEvent("create", planID, "name=Legendary Elite Support attackPlan=" + attackPlanID);
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
   int i = 0;
   for (i = 0; < numberFound)
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
      llLogPlanEvent("destroy", planID, "reason=no elite support units added");
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
   vector targetPoint = llChooseAssaultObjectivePoint(attackPlanID, gatherPoint);
   if ((gatherPoint == cInvalidVector) || (targetPoint == cInvalidVector))
   {
      llDestroyExplorerEscortPlan();
      llDestroyEliteSupportPlan();
      return (false);
   }

   int nonEliteCount = llGetTotalNonEliteTroopCount();
   int eliteCount = llGetTotalEliteTroopCount();
   int totalArmyCount = nonEliteCount + eliteCount;
   bool largeArmy = ((nonEliteCount >= 12) && (totalArmyCount >= 18));
   float protectionBias = llGetExplorerProtectionBias();
   float decapitationBias = llGetDecapitationBias();

   float eliteOffset = 7.0;
   float explorerOffset = 14.0 + (protectionBias * 10.0) - (decapitationBias * 4.0) + gLLExplorerRearOffsetBonus;
   int desiredEliteCount = 1;
   int desiredEscortCount = 2 + xsFloor(protectionBias * 5.0) + gLLExplorerEscortBonus;
   if (largeArmy == true)
   {
      eliteOffset = 13.0;
      explorerOffset = explorerOffset + 6.0;
      desiredEliteCount = eliteCount;
      desiredEscortCount = desiredEscortCount + 2;
      if (desiredEliteCount > 6)
      {
         desiredEliteCount = 6;
      }
   }
   else if (eliteCount > 1)
   {
      desiredEliteCount = 2;
   }

   if (decapitationBias >= 0.70)
   {
      desiredEscortCount = desiredEscortCount - 1;
   }

   if (desiredEscortCount < 2)
   {
      desiredEscortCount = 2;
   }

   int escortCap = nonEliteCount / 3;
   if (escortCap < 2)
   {
      escortCap = 2;
   }
   if (desiredEscortCount > escortCap)
   {
      desiredEscortCount = escortCap;
   }

   vector elitePoint = llGetAssaultOffsetPoint(gatherPoint, targetPoint, eliteOffset);
   vector explorerPoint = llGetAssaultOffsetPoint(gatherPoint, targetPoint, explorerOffset);

   llPositionExplorerBehindArmy(explorerPoint);

   if ((nonEliteCount <= 0) || (eliteCount <= 0))
   {
      llDestroyExplorerEscortPlan();
      llDestroyEliteSupportPlan();
      return (true);
   }

    if ((gLLExplorerEscortPlanID < 0) || (gLLExplorerEscortAttackPlanID != attackPlanID) ||
        (xsGetTime() - gLLExplorerEscortLastRefreshTime >= 12000))
    {
       llRebuildExplorerEscortPlan(attackPlanID, gatherPoint, explorerPoint, desiredEscortCount);
    }
    else
    {
       aiPlanSetVariableVector(gLLExplorerEscortPlanID, cCombatPlanTargetPoint, 0, explorerPoint);
       aiPlanSetVariableVector(gLLExplorerEscortPlanID, cCombatPlanGatherPoint, 0, gatherPoint);
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
   llLogRuleTick("legendaryEliteGuardMonitor");
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (aiGetFallenExplorerID() >= 0)
   {
      llDestroyEliteGuardPlan();
      llDestroyExplorerEscortPlan();
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
      llDestroyExplorerEscortPlan();
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