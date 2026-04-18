//==============================================================================
// kothManager
// Detects if KOTH is running and sends all available troops to the hill.
//==============================================================================
rule kothManager
inactive
maxInterval 20
{
   if (gIsKOTHRunning && gKOTHTeam != kbGetPlayerTeam(cMyID))
   {
      vector hillLocation = kbUnitGetPosition(getUnit(cUnitTypeypKingsHill, cPlayerRelationAny, cUnitStateAlive));
      vector mainBaseVec = kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID));
      int unitQuery = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
      int numberUnits = kbUnitQueryExecute(unitQuery);
      aiPlanDestroy(gKOTHGuardPlan);

      if (gDefenseReflexBaseID == kbBaseGetMainID(cMyID)) {
         aiPlanDestroy(gKOTHCombatPlan);
         aiPlanDestroy(gKOTHGuardPlan);
         return;
      }

      if (gKOTHCombatPlan == -1 || aiPlanGetActive(gKOTHCombatPlan) == false)
      {
         aiPlanDestroy(gKOTHCombatPlan);
         aiPlanDestroy(gKOTHGuardPlan);
         gKOTHCombatPlan = aiPlanCreate("KOTH Combat Plan", cPlanCombat);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanCombatType, 0, cCombatPlanCombatTypeAttack);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
         aiPlanSetVariableVector(gKOTHCombatPlan, cCombatPlanTargetPoint, 0, hillLocation);
         aiPlanSetVariableVector(gKOTHCombatPlan, cCombatPlanGatherPoint, 0, mainBaseVec);
         aiPlanSetVariableFloat(gKOTHCombatPlan, cCombatPlanGatherDistance, 0, 120.0);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanAttackRoutePattern, 0, cCombatPlanAttackRoutePatternBest);
         aiPlanSetVariableBool(gKOTHCombatPlan, cCombatPlanAllowMoreUnitsDuringAttack, 0, true);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanRefreshFrequency, 0, cDifficultyCurrent >= cDifficultyHard ? 300 : 1000);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanDoneMode, 0, cCombatPlanDoneModeRetreat | cCombatPlanDoneModeNoTarget);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeNone);
         aiPlanSetVariableInt(gKOTHCombatPlan, cCombatPlanNoTargetTimeout, 0, 30000);
         aiPlanSetInitialPosition(gKOTHCombatPlan, mainBaseVec);
         aiPlanSetDesiredPriority(gKOTHCombatPlan, 100);
         aiPlanSetActive(gKOTHCombatPlan);
      }
   }
}
//==============================================================================
// kothBaseManager
// Detects if KOTH is running and tries to defend the King's Hill if so.
//==============================================================================
rule kothBaseManager
inactive
maxInterval 20
{
   if (gIsKOTHRunning && gKOTHTeam == kbGetPlayerTeam(cMyID) || gIsKOTHRunning == false)
   {
      vector hillLocation = kbUnitGetPosition(getUnit(cUnitTypeypKingsHill, cPlayerRelationAny, cUnitStateAlive));
      vector mainBaseVec = kbBaseGetLocation(cMyID, kbBaseGetMainID(cMyID));
      vector baseLocation = hillLocation;
      int unitQuery = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cMyID, cUnitStateAlive);
      int numberUnits = kbUnitQueryExecute(unitQuery);
      kbBaseSetMilitaryGatherPoint(cMyID, kbBaseGetMainID(cMyID), hillLocation);
      aiPlanDestroy(gKOTHCombatPlan);

      if (gDefenseReflexBaseID == kbBaseGetMainID(cMyID)) {
         aiPlanDestroy(gKOTHCombatPlan);
         aiPlanDestroy(gKOTHGuardPlan);
         return;
      }

      if (gKOTHBasePlan == -1 || aiPlanGetActive(gKOTHBasePlan) == false)
      {
         aiPlanDestroy(gKOTHBasePlan);
         gKOTHBasePlan = aiPlanCreate("KOTH Base Plan", cPlanBuild);
         aiPlanSetVariableInt(gKOTHBasePlan, cBuildPlanBuildingTypeID, 0, cUnitTypeTownCenter);
         aiPlanSetVariableVector(gKOTHBasePlan, cBuildPlanCenterPosition, 0, baseLocation);
         aiPlanSetDesiredPriority(gKOTHBasePlan, 100);
         aiPlanSetActive(gKOTHBasePlan);
      }
      if ((gKOTHGuardPlan == -1 || aiPlanGetActive(gKOTHGuardPlan) == false) && gIsKOTHRunning == false) {
         aiPlanDestroy(gKOTHGuardPlan);

         gKOTHGuardPlan = aiPlanCreate("KOTH Combat Plan", cPlanCombat);
         aiPlanSetVariableInt(gKOTHGuardPlan, cCombatPlanCombatType, 0, cCombatPlanCombatTypeDefend);
         aiPlanSetVariableInt(gKOTHGuardPlan, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
         aiPlanSetVariableVector(gKOTHGuardPlan, cCombatPlanTargetPoint, 0, hillLocation);
         aiPlanSetVariableVector(gKOTHGuardPlan, cCombatPlanGatherPoint, 0, mainBaseVec);
         aiPlanSetVariableFloat(gKOTHGuardPlan, cCombatPlanGatherDistance, 0, 220.0);
         aiPlanSetVariableInt(gKOTHGuardPlan, cCombatPlanAttackRoutePattern, 0, cCombatPlanAttackRoutePatternBest);
         aiPlanSetVariableBool(gKOTHGuardPlan, cCombatPlanAllowMoreUnitsDuringAttack, 0, true);
         aiPlanSetVariableInt(gKOTHGuardPlan, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeNone);
         aiPlanSetVariableInt(gKOTHGuardPlan, cCombatPlanNoTargetTimeout, 0, 30000);
         aiPlanSetInitialPosition(gKOTHGuardPlan, mainBaseVec);
         aiPlanSetDesiredPriority(gKOTHGuardPlan, 100);
         aiPlanSetActive(gKOTHGuardPlan);
      } else if (gIsKOTHRunning == true && gKOTHTeam != kbGetPlayerTeam(cMyID)) {
         aiPlanDestroy(gKOTHGuardPlan);
      }
   }
}
//==============================================================================
// checkEnemyNearKOTH
// Checks if enemy units are within 50 distance units (meters?) of the KOTH unit.
//==============================================================================
// rule checkEnemyNearKOTH
// inactive
// maxInterval 20
// {
//    vector hillLocation = kbUnitGetPosition(getUnit(cUnitTypeypKingsHill, cPlayerRelationAny, cUnitStateAlive));

//    int enemyQuery = createSimpleUnitQuery(cUnitTypeLogicalTypeLandMilitary, cPlayerRelationEnemy, cUnitStateAlive);
//    kbUnitQuerySetPosition(enemyQuery, hillLocation);
//    kbUnitQuerySetMaximumDistance(enemyQuery, 50);
//    int numberEnemies = kbUnitQueryExecute(enemyQuery);

//    if (numberEnemies > 0)
//    {
//       //
//    } else {
//       //
//    }
// }