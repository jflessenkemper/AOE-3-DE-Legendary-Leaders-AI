//==============================================================================
/* aiPrisoners.xs

   Legendary Leaders prisoner-handling scaffolding.
   This file handles doctrine setup, prison-site planning, and a dedicated
   guard plan once surrendered-unit proxies are available.
*/
//==============================================================================

int cLLPrisonerDoctrineStrictImprisonment = 0;
int cLLPrisonerDoctrineForcedLabor = 1;
int cLLPrisonerDoctrineExecution = 2;
int cLLPrisonerDoctrineIntegration = 3;
int cLLPrisonerDoctrineExchange = 4;

extern int gLLPrisonerDoctrine = 0;
extern int gLLPrisonerProxyType = -1;
extern int gLLPrisonStructureType = -1;
extern int gLLPrisonBuildPlanID = -1;
extern int gLLPrisonGuardPlanID = -1;
extern int gLLPrisonLastSeenTime = -1;
extern int gLLPrisonLastTauntTime = -60000;
extern int gLLPrisonLastAllyAlertTime = -60000;
extern int gLLPrisonLastRescueScanTime = -60000;
extern int gLLEnemyPrisonPlayerID = -1;
extern bool gLLPrisonSystemEnabled = false;
extern float gLLPrisonEscortFraction = 0.30;
extern float gLLPrisonDetectionRadius = 60.0;
extern float gLLPrisonBuildDistance = 22.0;
extern vector gLLPrisonLocation = cInvalidVector;
extern vector gLLEnemyPrisonLocation = cInvalidVector;

int llGetPrisonerCount(vector location = cInvalidVector, float radius = 60.0)
{
   int prisonerCount = 0;

   if (gLLPrisonerProxyType >= 0)
   {
      prisonerCount = prisonerCount + getUnitCountByLocation(gLLPrisonerProxyType, 0, cUnitStateAlive, location, radius);
   }

   if (gLLPrisonerProxyType != cUnitTypeAbstractVillager)
   {
      prisonerCount = prisonerCount + getUnitCountByLocation(cUnitTypeAbstractVillager, 0, cUnitStateAlive, location, radius);
   }

   return (prisonerCount);
}

string llGetPrisonerDoctrineName(int doctrine = -1)
{
   if (doctrine < 0)
   {
      doctrine = gLLPrisonerDoctrine;
   }

   switch (doctrine)
   {
      case cLLPrisonerDoctrineForcedLabor:
         return ("forced labor");
      case cLLPrisonerDoctrineExecution:
         return ("execution");
      case cLLPrisonerDoctrineIntegration:
         return ("integration");
      case cLLPrisonerDoctrineExchange:
         return ("exchange");
   }

   return ("strict imprisonment");
}

string llGetEnemyPrisonTaunt(int doctrine = -1)
{
   if (doctrine < 0)
   {
      doctrine = gLLPrisonerDoctrine;
   }

   switch (doctrine)
   {
      case cLLPrisonerDoctrineForcedLabor:
         return ("Your surrendered soldiers build my works now.");
      case cLLPrisonerDoctrineExecution:
         return ("Your prisoners will not trouble my rear again.");
      case cLLPrisonerDoctrineIntegration:
         return ("Some of your prisoners already prefer my banner.");
      case cLLPrisonerDoctrineExchange:
         return ("Your prisoners live, but they return only on my terms.");
   }

   return ("Your prisoners wait behind my lines under heavy guard.");
}

string llGetAllyPrisonAlert(int doctrine = -1)
{
   if (doctrine < 0)
   {
      doctrine = gLLPrisonerDoctrine;
   }

   switch (doctrine)
   {
      case cLLPrisonerDoctrineForcedLabor:
         return ("Enemy prison camp spotted. Strike their works and free the captives.");
      case cLLPrisonerDoctrineExecution:
         return ("Enemy prison camp spotted. Hit it quickly before they butcher the captives.");
      case cLLPrisonerDoctrineIntegration:
         return ("Enemy prison camp spotted. Break it before the captives are turned against us.");
      case cLLPrisonerDoctrineExchange:
         return ("Enemy prison camp spotted. Attack now and force a release.");
   }

   return ("Enemy prison camp spotted. Attack here and free the captives.");
}

vector llFindEnemyPrisonLocation(void)
{
   gLLEnemyPrisonPlayerID = -1;

   for (int player = 1; player < cNumberPlayers; player++)
   {
      if (kbIsPlayerEnemy(player) == false)
      {
         continue;
      }

      int enemyBaseID = kbBaseGetMainID(player);
      if (enemyBaseID < 0)
      {
         continue;
      }

      vector enemyBaseLocation = kbBaseGetLocation(player, enemyBaseID);
      if (enemyBaseLocation == cInvalidVector)
      {
         continue;
      }

      if (llGetPrisonerCount(enemyBaseLocation, gLLPrisonDetectionRadius) > 0)
      {
         gLLEnemyPrisonPlayerID = player;
         return (enemyBaseLocation);
      }
   }

   return (cInvalidVector);
}

void llSetPrisonerProxyType(int unitTypeID = -1)
{
   gLLPrisonerProxyType = unitTypeID;
}

void llConfigurePrisonSite(int buildingTypeID = -1, float buildDistance = 22.0)
{
   gLLPrisonStructureType = buildingTypeID;
   gLLPrisonBuildDistance = buildDistance;
}

void llSetPrisonerDoctrine(int doctrine = 0, float escortFraction = 0.30, float detectionRadius = 60.0)
{
   gLLPrisonerDoctrine = doctrine;

   if (escortFraction < 0.20)
   {
      escortFraction = 0.20;
   }
   else if (escortFraction > 0.40)
   {
      escortFraction = 0.40;
   }
   gLLPrisonEscortFraction = escortFraction;

   if (detectionRadius < 30.0)
   {
      detectionRadius = 30.0;
   }
   gLLPrisonDetectionRadius = detectionRadius;
}

vector llGetPrisonAnchorLocation(void)
{
   int mainBaseID = kbBaseGetMainID(cMyID);
   vector prisonAnchor = kbBaseGetLocation(cMyID, mainBaseID);
   int townCenterID = getClosestUnitByLocation(cUnitTypeTownCenter, cMyID, cUnitStateAlive, prisonAnchor, 45.0);

   if (townCenterID >= 0)
   {
      prisonAnchor = kbUnitGetPosition(townCenterID);
   }

   prisonAnchor = xsVectorSet(xsVectorGetX(prisonAnchor) + gLLPrisonBuildDistance, 0.0,
      xsVectorGetZ(prisonAnchor) + gLLPrisonBuildDistance);

   return (prisonAnchor);
}

int llGetPrisonGuardCap(void)
{
   int militaryPop = aiGetMilitaryPop();
   int guardCap = 6;

   if (gLLPrisonEscortFraction >= 0.35)
   {
      guardCap = 10;
   }
   else if (gLLPrisonEscortFraction >= 0.25)
   {
      guardCap = 8;
   }

   if (militaryPop >= 100)
   {
      guardCap = guardCap + 2;
   }
   else if (militaryPop < 30)
   {
      guardCap = 4;
   }

   return (guardCap);
}

void llEnablePrisonerSystem(void)
{
   gLLPrisonSystemEnabled = true;

   if (gLLPrisonerProxyType < 0)
   {
      gLLPrisonerProxyType = cUnitTypeLogicalTypeLandMilitary;
   }

   if (gLLPrisonStructureType < 0)
   {
      gLLPrisonStructureType = gTowerUnit;
   }

   xsEnableRule("legendaryPrisonerMonitor");
   xsEnableRule("legendaryPrisonGuard");
   xsEnableRule("legendaryPrisonRescueMonitor");
}

rule legendaryPrisonerMonitor
inactive
minInterval 10
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (gLLPrisonerProxyType < 0)
   {
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   vector mainBaseLocation = kbBaseGetLocation(cMyID, mainBaseID);
   int prisonerCount = llGetPrisonerCount(mainBaseLocation, gLLPrisonDetectionRadius);

   if (prisonerCount <= 0)
   {
      if ((gLLPrisonGuardPlanID >= 0) && (gLLPrisonLastSeenTime >= 0) && (xsGetTime() > gLLPrisonLastSeenTime + 45000))
      {
         aiPlanDestroy(gLLPrisonGuardPlanID);
         gLLPrisonGuardPlanID = -1;
      }
      return;
   }

   gLLPrisonLastSeenTime = xsGetTime();

   if (gLLPrisonLocation == cInvalidVector)
   {
      gLLPrisonLocation = llGetPrisonAnchorLocation();
      debugMilitary("Legendary Prison: established " + llGetPrisonerDoctrineName() + " prison anchor.");
   }

   if ((gLLPrisonStructureType >= 0) &&
       (getUnitCountByLocation(gLLPrisonStructureType, cMyID, cUnitStateABQ, gLLPrisonLocation, 30.0) < 1) &&
       (aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, gLLPrisonStructureType) < 0))
   {
      gLLPrisonBuildPlanID = createLocationBuildPlan(gLLPrisonStructureType, 1, 68, false, cMilitaryEscrowID, gLLPrisonLocation, 1);
   }

   if ((cvOkToTaunt == true) && (xsGetTime() > gLLPrisonLastTauntTime + 60000))
   {
      sendStatement(cPlayerRelationEnemyNotGaia, cAICommPromptToEnemyLull, gLLPrisonLocation);
      sendChatLine(cPlayerRelationEnemyNotGaia, llGetEnemyPrisonTaunt());
      gLLPrisonLastTauntTime = xsGetTime();
   }
}

rule legendaryPrisonGuard
inactive
minInterval 15
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if ((gLLPrisonerProxyType < 0) || (gLLPrisonLocation == cInvalidVector))
   {
      return;
   }

   int prisonerCount = llGetPrisonerCount(gLLPrisonLocation, gLLPrisonDetectionRadius);
   if (prisonerCount <= 0)
   {
      return;
   }

   int mainBaseID = kbBaseGetMainID(cMyID);
   vector mainBaseLocation = kbBaseGetLocation(cMyID, mainBaseID);
   int guardCap = llGetPrisonGuardCap();

   if ((gLLPrisonGuardPlanID < 0) || (aiPlanGetActive(gLLPrisonGuardPlanID) == false))
   {
      gLLPrisonGuardPlanID = aiPlanCreate("Legendary Prison Guard", cPlanCombat);
      aiPlanAddUnitType(gLLPrisonGuardPlanID, cUnitTypeLogicalTypeLandMilitary, 0, 1, guardCap);
      aiPlanSetVariableInt(gLLPrisonGuardPlanID, cCombatPlanCombatType, 0, cCombatPlanCombatTypeDefend);
      aiPlanSetVariableInt(gLLPrisonGuardPlanID, cCombatPlanTargetMode, 0, cCombatPlanTargetModePoint);
      aiPlanSetVariableVector(gLLPrisonGuardPlanID, cCombatPlanTargetPoint, 0, gLLPrisonLocation);
      aiPlanSetVariableVector(gLLPrisonGuardPlanID, cCombatPlanGatherPoint, 0, kbBaseGetMilitaryGatherPoint(cMyID, mainBaseID));
      aiPlanSetVariableFloat(gLLPrisonGuardPlanID, cCombatPlanTargetEngageRange, 0, 35.0);
      aiPlanSetVariableFloat(gLLPrisonGuardPlanID, cCombatPlanGatherDistance, 0, 18.0);
      aiPlanSetVariableInt(gLLPrisonGuardPlanID, cCombatPlanRefreshFrequency, 0, 300);
      aiPlanSetVariableInt(gLLPrisonGuardPlanID, cCombatPlanRetreatMode, 0, cCombatPlanRetreatModeOutnumbered);
      aiPlanSetInitialPosition(gLLPrisonGuardPlanID, mainBaseLocation);
      aiPlanSetDesiredPriority(gLLPrisonGuardPlanID, 24);
      aiPlanSetActive(gLLPrisonGuardPlanID);
   }
   else
   {
      aiPlanSetVariableVector(gLLPrisonGuardPlanID, cCombatPlanTargetPoint, 0, gLLPrisonLocation);
   }
}

rule legendaryPrisonRescueMonitor
inactive
minInterval 25
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (xsGetTime() < gLLPrisonLastRescueScanTime + 25000)
   {
      return;
   }
   gLLPrisonLastRescueScanTime = xsGetTime();

   gLLEnemyPrisonLocation = llFindEnemyPrisonLocation();
   if (gLLEnemyPrisonLocation == cInvalidVector)
   {
      return;
   }

   if (xsGetTime() < gLLPrisonLastAllyAlertTime + 70000)
   {
      return;
   }

   sendStatement(cPlayerRelationAllyExcludingSelf, cAICommPromptToAllyIWillAttackEnemyBase, gLLEnemyPrisonLocation);
   sendChatLine(cPlayerRelationAllyExcludingSelf, llGetAllyPrisonAlert());
   gLLPrisonLastAllyAlertTime = xsGetTime();
}