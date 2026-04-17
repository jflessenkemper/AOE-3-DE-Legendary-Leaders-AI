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
extern int gLLNavalPrisonBuildPlanID = -1;
extern int gLLNavalPrisonLastSeenTime = -1;
extern vector gLLPrisonLocation = cInvalidVector;
extern vector gLLEnemyPrisonLocation = cInvalidVector;
extern vector gLLNavalPrisonLocation = cInvalidVector;
extern int gLLSurrenderUnitIDs = -1;
extern int gLLSurrenderTimes = -1;
extern int gLLSurrenderStates = -1;
extern int gLLSurrenderCaptors = -1;
extern int gLLSurrenderOriginalOwners = -1;

int cLLMaxSurrenderUnits = 64;
int cLLMaxSurrenderLifetime = 90000;
float cLLSurrenderArrivalRadius = 18.0;
float cLLPrisonHoldRadius = 10.0;
float cLLPrisonReclaimRadius = 12.0;

int cLLSurrenderStateTransit = 0;
int cLLSurrenderStateImprisoned = 1;

string llGetPlayerCivName(int playerID = -1)
{
   if (playerID < 0)
   {
      return ("");
   }

   return (kbGetCivName(kbGetCivForPlayer(playerID)));
}

bool llIsEliteProtoForRevolution(int protoUnitID = -1, int playerID = -1)
{
   if ((protoUnitID < 0) || (playerID < 0))
   {
      return (false);
   }

   string rvltName = llGetPlayerCivName(playerID);
   if (rvltName == "")
   {
      return (false);
   }

   if (rvltName == "RvltModAmericans")
   {
         return ((protoUnitID == cUnitTypexpGatlingGun) || (protoUnitID == cUnitTypeRocket));
   }
   if (rvltName == "RvltModNapoleonicFrance" || rvltName == "RvltModRevolutionaryFrance" || rvltName == "RvltModFrenchCanadians")
   {
         return ((protoUnitID == cUnitTypeSkirmisher) || (protoUnitID == cUnitTypeCuirassier));
   }
   if (rvltName == "RvltModCanadians")
   {
         return ((protoUnitID == cUnitTypeMusketeer) || (protoUnitID == cUnitTypeHussar));
   }
   if (rvltName == "RvltModBrazil")
   {
         return ((protoUnitID == cUnitTypeMusketeer) || (protoUnitID == cUnitTypeDragoon) ||
            (protoUnitID == cUnitTypeCrossbowman) || (protoUnitID == cUnitTypePikeman));
   }
   if (rvltName == "RvltModArgentina" || rvltName == "RvltModArgentines" ||
       rvltName == "RvltModPeruvians")
   {
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypeRodelero) ||
            (protoUnitID == cUnitTypeLancer));
   }
   if (rvltName == "RvltModChileans")
   {
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypeRodelero) ||
            (protoUnitID == cUnitTypeLancer) || (protoUnitID == cUnitTypeHussar));
   }
   if (rvltName == "RvltModColumbians")
   {
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypeRodelero) ||
            (protoUnitID == cUnitTypeLancer));
   }
   if (rvltName == "RvltModMexicans")
   {
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypeRodelero) ||
            (protoUnitID == cUnitTypedeChinaco));
   }
   if (rvltName == "RvltModCalifornians" || rvltName == "RvltModCentralAmericans" ||
       rvltName == "RvltModBajaCalifornians" || rvltName == "RvltModYucatan" ||
       rvltName == "RvltModRioGrande")
   {
         return ((protoUnitID == cUnitTypedeChinaco) || (protoUnitID == cUnitTypedeSalteador));
   }
   if (rvltName == "RvltModTexians")
   {
         return ((protoUnitID == cUnitTypedeChinaco) || (protoUnitID == cUnitTypedeStateMilitia));
   }
   if (rvltName == "RvltModFinnish")
   {
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypedeFinnishRider) ||
            (protoUnitID == cUnitTypeGrenadier));
   }
   if (rvltName == "RvltModHungarians")
   {
         return (protoUnitID == cUnitTypeHussar);
   }
   if (rvltName == "RvltModIndonesians" || rvltName == "RvltModSouthAfricans")
   {
         return ((protoUnitID == cUnitTypeHalberdier) || (protoUnitID == cUnitTypeRuyter));
   }
   if (rvltName == "RvltModEgyptians")
   {
         return ((protoUnitID == cUnitTypeGrenadier) || (protoUnitID == cUnitTypeHussar));
   }
   if (rvltName == "RvltModBarbary")
   {
      return ((protoUnitID == cUnitTypedeREVBarbaryWarrior) || (protoUnitID == cUnitTypedeBarbaryCavalry) ||
            (protoUnitID == cUnitTypedeBedouinHorseArcher));
   }
   if (rvltName == "RvltModHaitians")
   {
      return (protoUnitID == cUnitTypexpColonialMilitia);
   }
   if (rvltName == "RvltModRomanians")
   {
      return ((protoUnitID == cUnitTypexpColonialMilitia) || (protoUnitID == cUnitTypeDragoon));
   }
   if (rvltName == "RvltModMayans")
   {
      return (protoUnitID == cUnitTypedeSalteador);
   }

   return (false);
}

bool llIsEliteProtoForPlayer(int protoUnitID = -1, int playerID = -1)
{
   if ((protoUnitID < 0) || (playerID < 0))
   {
      return (false);
   }

   if (llIsEliteProtoForRevolution(protoUnitID, playerID) == true)
   {
      return (true);
   }

   switch (kbGetCivForPlayer(playerID))
   {
      case cCivBritish:
         return (protoUnitID == cUnitTypeMusketeer);
      case cCivDutch:
         return ((protoUnitID == cUnitTypeHalberdier) || (protoUnitID == cUnitTypeRuyter));
      case cCivFrench:
         return ((protoUnitID == cUnitTypeSkirmisher) || (protoUnitID == cUnitTypeCuirassier));
      case cCivGermans:
         return ((protoUnitID == cUnitTypeSkirmisher) || (protoUnitID == cUnitTypeUhlan));
      case cCivOttomans:
         return ((protoUnitID == cUnitTypeGrenadier) || (protoUnitID == cUnitTypeHussar));
      case cCivPortuguese:
         return ((protoUnitID == cUnitTypeMusketeer) || (protoUnitID == cUnitTypeDragoon));
      case cCivRussians:
         return ((protoUnitID == cUnitTypeGrenadier) || (protoUnitID == cUnitTypeCavalryArcher));
      case cCivSpanish:
         return ((protoUnitID == cUnitTypeRodelero) || (protoUnitID == cUnitTypeLancer));
      case cCivDESwedish:
         return ((protoUnitID == cUnitTypePikeman) || (protoUnitID == cUnitTypedeFinnishRider));
      case cCivXPAztec:
         return ((protoUnitID == cUnitTypexpJaguarKnight) || (protoUnitID == cUnitTypexpArrowKnight));
      case cCivXPIroquois:
         return ((protoUnitID == cUnitTypexpTomahawk) || (protoUnitID == cUnitTypexpWarRifle));
      case cCivXPSioux:
         return ((protoUnitID == cUnitTypexpAxeRider) || (protoUnitID == cUnitTypexpRifleRider));
      case cCivChinese:
      case cCivSPCChinese:
         return ((protoUnitID == cUnitTypeypArquebusier) || (protoUnitID == cUnitTypeypMeteorHammer));
      case cCivIndians:
      case cCivSPCIndians:
         return ((protoUnitID == cUnitTypeypSepoy) || (protoUnitID == cUnitTypeypSowar));
      case cCivJapanese:
      case cCivSPCJapanese:
      case cCivSPCJapaneseEnemy:
         return ((protoUnitID == cUnitTypeypKensei) || (protoUnitID == cUnitTypeypAshigaru));
      case cCivDEEthiopians:
         return ((protoUnitID == cUnitTypedeOromoWarrior) || (protoUnitID == cUnitTypedeShotelWarrior));
      case cCivDEHausa:
         return ((protoUnitID == cUnitTypedeFulaWarrior) || (protoUnitID == cUnitTypedeRaider));
      case cCivDEInca:
         return ((protoUnitID == cUnitTypedeBolasWarrior) || (protoUnitID == cUnitTypedeJungleBowman));
      case cCivDEAmericans:
         return ((protoUnitID == cUnitTypedeRifleman) || (protoUnitID == cUnitTypedeUSCavalry));
      case cCivDEMexicans:
         return ((protoUnitID == cUnitTypedeSoldado) || (protoUnitID == cUnitTypedeChinaco));
      case cCivDEItalians:
         return ((protoUnitID == cUnitTypedeBersagliere) || (protoUnitID == cUnitTypedePavisier));
      case cCivDEMaltese:
         return ((protoUnitID == cUnitTypedeHospitaller) || (protoUnitID == cUnitTypedeHoopThrower));
   }

   return (false);
}

bool llIsEliteUnit(int unitID = -1)
{
   if (unitID < 0)
   {
      return (false);
   }

   if (kbUnitIsType(unitID, cUnitTypeHero) == true)
   {
      return (true);
   }

   return (llIsEliteProtoForPlayer(kbUnitGetProtoUnitID(unitID), kbUnitGetPlayerID(unitID)));
}

bool llHasNearbyEliteSupport(int unitID = -1, float radius = 24.0)
{
   if ((unitID < 0) || (radius <= 0.0))
   {
      return (false);
   }

   int ownerID = kbUnitGetPlayerID(unitID);
   int supportTypeID = cUnitTypeLogicalTypeLandMilitary;
   if (kbUnitIsType(unitID, cUnitTypeAbstractWarShip) == true)
   {
      supportTypeID = cUnitTypeAbstractWarShip;
   }

   int unitQueryID = createSimpleUnitQuery(supportTypeID, ownerID, cUnitStateAlive, kbUnitGetPosition(unitID), radius);
   int numberFound = kbUnitQueryExecute(unitQueryID);
   for (int i = 0; < numberFound)
   {
      int nearbyUnitID = kbUnitQueryGetResult(unitQueryID, i);
      if (nearbyUnitID == unitID)
      {
         continue;
      }

      if (llIsEliteUnit(nearbyUnitID) == true)
      {
         return (true);
      }
   }

   return (false);
}

float llGetSurrenderHealthThreshold(void)
{
   return (0.10);
}

float llGetSurrenderEliteSupportRadius(void)
{
   return (24.0);
}

bool llCanUnitSurrender(int unitID = -1, float healthThreshold = 0.50, float eliteSupportRadius = 24.0)
{
   if (unitID < 0)
   {
      return (false);
   }

   if (kbUnitGetHealth(unitID) > healthThreshold)
   {
      return (false);
   }

   if (llIsEliteUnit(unitID) == true)
   {
      debugLegendaryLeaders("unit " + unitID + " refused surrender because " + kbGetProtoUnitName(kbUnitGetProtoUnitID(unitID)) +
                            " is treated as elite for " + llGetPlayerCivName(kbUnitGetPlayerID(unitID)) + ".");
      return (false);
   }

   if (llHasNearbyEliteSupport(unitID, eliteSupportRadius) == true)
   {
      debugLegendaryLeaders("unit " + unitID + " refused surrender because nearby elite support is still present.");
      return (false);
   }

   return (true);
}

void llEnsureSurrenderArrays(void)
{
   if (gLLSurrenderUnitIDs < 0)
   {
      gLLSurrenderUnitIDs = xsArrayCreateInt(cLLMaxSurrenderUnits, -1, "Legendary surrender units");
   }

   if (gLLSurrenderTimes < 0)
   {
      gLLSurrenderTimes = xsArrayCreateInt(cLLMaxSurrenderUnits, -1, "Legendary surrender times");
   }

   if (gLLSurrenderStates < 0)
   {
      gLLSurrenderStates = xsArrayCreateInt(cLLMaxSurrenderUnits, cLLSurrenderStateTransit, "Legendary surrender states");
   }

   if (gLLSurrenderCaptors < 0)
   {
      gLLSurrenderCaptors = xsArrayCreateInt(cLLMaxSurrenderUnits, -1, "Legendary surrender captors");
   }

   if (gLLSurrenderOriginalOwners < 0)
   {
      gLLSurrenderOriginalOwners = xsArrayCreateInt(cLLMaxSurrenderUnits, -1, "Legendary surrender owners");
   }
}

int llGetTrackedSurrenderIndex(int unitID = -1)
{
   if ((unitID < 0) || (gLLSurrenderUnitIDs < 0))
   {
      return (-1);
   }

   for (int i = 0; < cLLMaxSurrenderUnits)
   {
      if (xsArrayGetInt(gLLSurrenderUnitIDs, i) == unitID)
      {
         return (i);
      }
   }

   return (-1);
}

void llClearTrackedSurrenderIndex(int index = -1)
{
   if ((index < 0) || (gLLSurrenderUnitIDs < 0) || (gLLSurrenderTimes < 0))
   {
      return;
   }

   xsArraySetInt(gLLSurrenderUnitIDs, index, -1);
   xsArraySetInt(gLLSurrenderTimes, index, -1);
   if (gLLSurrenderStates >= 0)
   {
      xsArraySetInt(gLLSurrenderStates, index, cLLSurrenderStateTransit);
   }
   if (gLLSurrenderCaptors >= 0)
   {
      xsArraySetInt(gLLSurrenderCaptors, index, -1);
   }
   if (gLLSurrenderOriginalOwners >= 0)
   {
      xsArraySetInt(gLLSurrenderOriginalOwners, index, -1);
   }
}

int llGetCapturingPlayerForUnit(int unitID = -1)
{
   if (unitID < 0)
   {
      return (-1);
   }

   vector unitLocation = kbUnitGetPosition(unitID);
   int threatTypeID = cUnitTypeLogicalTypeLandMilitary;
   float threatRadius = 28.0;
   if (kbUnitIsType(unitID, cUnitTypeAbstractWarShip) == true)
   {
      threatTypeID = cUnitTypeAbstractWarShip;
      threatRadius = 36.0;
   }

   int closestPlayer = -1;
   float closestDistance = 100000.0;
   for (int player = 1; player < cNumberPlayers; player++)
   {
      if (kbIsPlayerEnemy(player) == false)
      {
         continue;
      }

      int enemyUnitID = getClosestUnitByLocation(threatTypeID, player, cUnitStateAlive, unitLocation, threatRadius);
      if (enemyUnitID < 0)
      {
         continue;
      }

      float enemyDistance = distance(unitLocation, kbUnitGetPosition(enemyUnitID));
      if (enemyDistance < closestDistance)
      {
         closestDistance = enemyDistance;
         closestPlayer = player;
      }
   }

   if (closestPlayer >= 0)
   {
      return (closestPlayer);
   }

   int hatedPlayerID = aiGetMostHatedPlayerID();
   if (hatedPlayerID >= 0)
   {
      return (hatedPlayerID);
   }

   return (-1);
}

int llFindBestHCGatherUnitForPlayer(int playerID = -1)
{
   if (playerID < 0)
   {
      return (-1);
   }

   int baseID = kbBaseGetMainID(playerID);
   if (baseID < 0)
   {
      return (getUnit(cUnitTypeTownCenter, playerID, cUnitStateAlive));
   }

   vector loc = kbBaseGetLocation(playerID, baseID);
   float dist = kbBaseGetDistance(playerID, baseID);
   int unitID = getUnitByLocation(cUnitTypeAbstractTownCenter, playerID, cUnitStateAlive, loc, dist);
   if (unitID < 0)
   {
      unitID = getUnitByLocation(cUnitTypeHCGatherPointPri1, playerID, cUnitStateAlive, loc, dist);
   }
   if (unitID < 0)
   {
      unitID = getUnitByLocation(cUnitTypeHCGatherPointPri2, playerID, cUnitStateAlive, loc, dist);
   }
   if (unitID < 0)
   {
      unitID = getUnitByLocation(cUnitTypeHCGatherPointPri3, playerID, cUnitStateAlive, loc, dist);
   }
   if (unitID < 0)
   {
      unitID = getUnit(cUnitTypeTownCenter, playerID, cUnitStateAlive);
   }

   return (unitID);
}

vector llGetShipmentGatherLocationForPlayer(int playerID = -1)
{
   int gatherUnitID = llFindBestHCGatherUnitForPlayer(playerID);
   if (gatherUnitID >= 0)
   {
      return (kbUnitGetPosition(gatherUnitID));
   }

   return (cInvalidVector);
}

vector llGetPrisonAnchorLocationForPlayer(int playerID = -1)
{
   if (playerID < 0)
   {
      return (cInvalidVector);
   }

   vector prisonAnchor = llGetShipmentGatherLocationForPlayer(playerID);
   if (prisonAnchor == cInvalidVector)
   {
      int mainBaseID = kbBaseGetMainID(playerID);
      prisonAnchor = kbBaseGetLocation(playerID, mainBaseID);
   }

   return (prisonAnchor);
}

vector llGetPrisonHoldingPoint(int captorPlayerID = -1, int slot = 0)
{
   vector prisonAnchor = llGetPrisonAnchorLocationForPlayer(captorPlayerID);
   if (prisonAnchor == cInvalidVector)
   {
      return (cInvalidVector);
   }

   int ringIndex = slot % 6;
   float offsetX = 0.0;
   float offsetZ = 0.0;
   switch (ringIndex)
   {
      case 0: offsetX = 4.0; break;
      case 1: offsetX = -4.0; break;
      case 2: offsetZ = 4.0; break;
      case 3: offsetZ = -4.0; break;
      case 4: offsetX = 3.0; offsetZ = 3.0; break;
      case 5: offsetX = -3.0; offsetZ = -3.0; break;
   }

   return (xsVectorSet(xsVectorGetX(prisonAnchor) + offsetX, 0.0, xsVectorGetZ(prisonAnchor) + offsetZ));
}

vector llGetReturnLocationForPlayer(int playerID = -1)
{
   if (playerID < 0)
   {
      return (cInvalidVector);
   }

   int mainBaseID = kbBaseGetMainID(playerID);
   if (mainBaseID >= 0)
   {
      vector gatherPoint = kbBaseGetMilitaryGatherPoint(playerID, mainBaseID);
      if (gatherPoint != cInvalidVector)
      {
         return (gatherPoint);
      }

      return (kbBaseGetLocation(playerID, mainBaseID));
   }

   int townCenterID = getUnit(cUnitTypeTownCenter, playerID, cUnitStateAlive);
   if (townCenterID >= 0)
   {
      return (kbUnitGetPosition(townCenterID));
   }

   return (cInvalidVector);
}

bool llHasFriendlyExplorerNearby(int playerID = -1, vector location = cInvalidVector, float radius = 12.0)
{
   if ((playerID < 0) || (location == cInvalidVector))
   {
      return (false);
   }

   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, playerID, cUnitStateAlive, location, radius);
   return (kbUnitQueryExecute(heroQueryID) > 0);
}

bool llTrackSurrenderingUnit(int unitID = -1)
{
   llEnsureSurrenderArrays();

   if (llGetTrackedSurrenderIndex(unitID) >= 0)
   {
      return (true);
   }

   for (int i = 0; < cLLMaxSurrenderUnits)
   {
      if (xsArrayGetInt(gLLSurrenderUnitIDs, i) >= 0)
      {
         continue;
      }

      xsArraySetInt(gLLSurrenderUnitIDs, i, unitID);
      xsArraySetInt(gLLSurrenderTimes, i, xsGetTime());
      xsArraySetInt(gLLSurrenderStates, i, cLLSurrenderStateTransit);
      xsArraySetInt(gLLSurrenderCaptors, i, llGetCapturingPlayerForUnit(unitID));
      xsArraySetInt(gLLSurrenderOriginalOwners, i, kbUnitGetPlayerID(unitID));
      return (true);
   }

   return (false);
}

void llReleaseSurrenderingUnit(int unitID = -1)
{
   if (unitID < 0)
   {
      return;
   }

   int currentPlanID = kbUnitGetPlanID(unitID);
   if (currentPlanID >= 0)
   {
      aiPlanRemoveUnit(currentPlanID, unitID);
   }
}

bool llHasEnemyPressureForSurrender(int unitID = -1)
{
   if (unitID < 0)
   {
      return (false);
   }

   int threatTypeID = cUnitTypeLogicalTypeLandMilitary;
   float threatRadius = 20.0;
   if (kbUnitIsType(unitID, cUnitTypeAbstractWarShip) == true)
   {
      threatTypeID = cUnitTypeAbstractWarShip;
      threatRadius = 28.0;
   }

   int enemyQueryID = createSimpleUnitQuery(threatTypeID, cPlayerRelationEnemyNotGaia, cUnitStateAlive,
      kbUnitGetPosition(unitID), threatRadius);
   return (kbUnitQueryExecute(enemyQueryID) > 0);
}

int llGetNearestEnemySurrenderBuildingID(int enemyPlayerID = -1, vector unitLocation = cInvalidVector)
{
   if ((enemyPlayerID < 0) || (unitLocation == cInvalidVector))
   {
      return (-1);
   }

   int closestBuildingID = -1;
   float closestDistance = 100000.0;
   int candidateBuildingID = -1;
   float candidateDistance = -1.0;

   candidateBuildingID = getClosestUnitByLocation(cUnitTypeFortFrontier, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   candidateBuildingID = getClosestUnitByLocation(cUnitTypeOutpost, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   candidateBuildingID = getClosestUnitByLocation(cUnitTypeBlockhouse, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   candidateBuildingID = getClosestUnitByLocation(cUnitTypeYPOutpostAsian, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   candidateBuildingID = getClosestUnitByLocation(cUnitTypedeTower, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   candidateBuildingID = getClosestUnitByLocation(cUnitTypeypCastle, enemyPlayerID, cUnitStateAlive, unitLocation, 300.0);
   if (candidateBuildingID >= 0)
   {
      candidateDistance = distance(unitLocation, kbUnitGetPosition(candidateBuildingID));
      if (candidateDistance < closestDistance)
      {
         closestBuildingID = candidateBuildingID;
         closestDistance = candidateDistance;
      }
   }

   return (closestBuildingID);
}

vector llGetSurrenderDestination(int unitID = -1)
{
   int enemyPlayerID = aiGetMostHatedPlayerID();
   if (enemyPlayerID < 0)
   {
      return (cInvalidVector);
   }

   if (kbUnitIsType(unitID, cUnitTypeAbstractWarShip) == true)
   {
      int enemyDockID = getUnit(gDockUnit, enemyPlayerID, cUnitStateAlive);
      if (enemyDockID >= 0)
      {
         return (kbUnitGetPosition(enemyDockID));
      }
   }

   vector enemyShipmentLocation = llGetShipmentGatherLocationForPlayer(enemyPlayerID);
   if (enemyShipmentLocation != cInvalidVector)
   {
      return (enemyShipmentLocation);
   }

   int enemyBaseID = kbBaseGetMainID(enemyPlayerID);
   if (enemyBaseID >= 0)
   {
      vector enemyGatherPoint = kbBaseGetMilitaryGatherPoint(enemyPlayerID, enemyBaseID);
      if (enemyGatherPoint != cInvalidVector)
      {
         return (enemyGatherPoint);
      }
   }

   int enemyPrisonBuildingID = llGetNearestEnemySurrenderBuildingID(enemyPlayerID, kbUnitGetPosition(unitID));
   if (enemyPrisonBuildingID >= 0)
   {
      return (kbUnitGetPosition(enemyPrisonBuildingID));
   }

   if (enemyBaseID >= 0)
   {
      return (kbBaseGetLocation(enemyPlayerID, enemyBaseID));
   }

   int enemyTownCenterID = getUnit(cUnitTypeTownCenter, enemyPlayerID, cUnitStateAlive);
   if (enemyTownCenterID >= 0)
   {
      return (kbUnitGetPosition(enemyTownCenterID));
   }

   return (cInvalidVector);
}

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

   prisonerCount = prisonerCount + getUnitCountByLocation(cUnitTypeLogicalTypeLandMilitary, cPlayerRelationEnemy, cUnitStateAlive, location, radius);
   prisonerCount = prisonerCount + getUnitCountByLocation(cUnitTypeAbstractVillager, cPlayerRelationEnemy, cUnitStateAlive, location, radius);

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

   if ((gLLSurrenderUnitIDs >= 0) && (gLLSurrenderStates >= 0) && (gLLSurrenderCaptors >= 0))
   {
      for (int i = 0; < cLLMaxSurrenderUnits)
      {
         if (xsArrayGetInt(gLLSurrenderStates, i) != cLLSurrenderStateImprisoned)
         {
            continue;
         }

         int captorPlayerID = xsArrayGetInt(gLLSurrenderCaptors, i);
         if (captorPlayerID < 0)
         {
            continue;
         }

         gLLEnemyPrisonPlayerID = captorPlayerID;
         return (llGetPrisonAnchorLocationForPlayer(captorPlayerID));
      }
   }

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
   debugLegendaryLeaders("prison proxy type set to " + unitTypeID);
}

void llConfigurePrisonSite(int buildingTypeID = -1, float buildDistance = 22.0)
{
   gLLPrisonStructureType = buildingTypeID;
   gLLPrisonBuildDistance = buildDistance;
   debugLegendaryLeaders("prison site configured with structure " + buildingTypeID + " at distance " + buildDistance);
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
   debugLegendaryLeaders("prison doctrine set to " + llGetPrisonerDoctrineName(doctrine) + ", escortFraction=" + escortFraction + ", detectionRadius=" + detectionRadius);
}

vector llGetPrisonAnchorLocation(void)
{
   return (llGetPrisonAnchorLocationForPlayer(cMyID));
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

vector llGetMainDockGuardLocation(void)
{
   int dockID = getUnit(gDockUnit, cMyID, cUnitStateAlive);
   if (dockID < 0)
   {
      return (cInvalidVector);
   }

   return (kbUnitGetPosition(dockID));
}

int llGetNavalPrisonShipCount(vector location = cInvalidVector)
{
   if (location == cInvalidVector)
   {
      return (0);
   }

   return (getUnitCountByLocation(cUnitTypeAbstractWarShip, cMyID, cUnitStateAlive, location, 35.0));
}

void llEnablePrisonerSystem(void)
{
   gLLPrisonSystemEnabled = true;
   llEnsureSurrenderArrays();

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
   xsEnableRule("legendaryNavalPrisonGuard");
   xsEnableRule("legendaryAISurrenderMonitor");
   xsEnableRule("legendaryAISurrenderMove");
   xsEnableRule("legendaryEliteGuardMonitor");
   debugLegendaryLeaders("prisoner system enabled with doctrine " + llGetPrisonerDoctrineName());
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

   if (gLLPrisonLocation == cInvalidVector)
   {
      gLLPrisonLocation = llGetPrisonAnchorLocation();
      debugMilitary("Legendary Prison: established " + llGetPrisonerDoctrineName() + " prison anchor.");
   }

   int prisonerCount = llGetPrisonerCount(gLLPrisonLocation, cLLPrisonHoldRadius);

   if (prisonerCount <= 0)
   {
      if ((gLLPrisonGuardPlanID >= 0) && (gLLPrisonLastSeenTime >= 0) && (xsGetTime() > gLLPrisonLastSeenTime + 45000))
      {
         debugLegendaryLeaders("destroying prison guard plan after prisoners were no longer detected.");
         aiPlanDestroy(gLLPrisonGuardPlanID);
         gLLPrisonGuardPlanID = -1;
      }
      return;
   }

   gLLPrisonLastSeenTime = xsGetTime();

   if ((gLLPrisonStructureType >= 0) &&
       (getUnitCountByLocation(gLLPrisonStructureType, cMyID, cUnitStateABQ, gLLPrisonLocation, 30.0) < 1) &&
       (aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, gLLPrisonStructureType) < 0))
   {
      gLLPrisonBuildPlanID = createLocationBuildPlan(gLLPrisonStructureType, 1, 68, false, cMilitaryEscrowID, gLLPrisonLocation, 1);
      debugLegendaryLeaders("creating prison structure build plan " + gLLPrisonBuildPlanID + " at " + gLLPrisonLocation);
   }

   if ((cvOkToTaunt == true) && (xsGetTime() > gLLPrisonLastTauntTime + 60000))
   {
      sendStatement(cPlayerRelationEnemyNotGaia, cAICommPromptToEnemyLull, gLLPrisonLocation);
      sendChatLine(cPlayerRelationEnemyNotGaia, llGetEnemyPrisonTaunt());
      gLLPrisonLastTauntTime = xsGetTime();
      debugLegendaryLeaders("enemy prison taunt fired at location " + gLLPrisonLocation);
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
      debugLegendaryLeaders("created prison guard plan " + gLLPrisonGuardPlanID + " with guard cap " + guardCap + " for " + prisonerCount + " prisoners.");
   }
   else
   {
      aiPlanSetVariableVector(gLLPrisonGuardPlanID, cCombatPlanTargetPoint, 0, gLLPrisonLocation);
      debugLegendaryLeaders("updated prison guard plan " + gLLPrisonGuardPlanID + " to location " + gLLPrisonLocation);
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

   debugLegendaryLeaders("enemy prison detected for player " + gLLEnemyPrisonPlayerID + " at " + gLLEnemyPrisonLocation);

   if (xsGetTime() < gLLPrisonLastAllyAlertTime + 70000)
   {
      return;
   }

   sendStatement(cPlayerRelationAllyExcludingSelf, cAICommPromptToAllyIWillAttackEnemyBase, gLLEnemyPrisonLocation);
   sendChatLine(cPlayerRelationAllyExcludingSelf, llGetAllyPrisonAlert());
   gLLPrisonLastAllyAlertTime = xsGetTime();
   debugLegendaryLeaders("ally prison rescue alert sent for location " + gLLEnemyPrisonLocation);
}

rule legendaryNavalPrisonGuard
inactive
minInterval 20
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (gHaveWaterSpawnFlag == false)
   {
      return;
   }

   vector dockLocation = llGetMainDockGuardLocation();
   if (dockLocation == cInvalidVector)
   {
      return;
   }

   int guardedShipCount = llGetNavalPrisonShipCount(dockLocation);
   if (guardedShipCount < 1)
   {
      return;
   }

   gLLNavalPrisonLastSeenTime = xsGetTime();
   gLLNavalPrisonLocation = dockLocation;

   int dockGuardType = gTowerUnit;
   float dockGuardRadius = 32.0;

   if ((gFortUnit >= 0) && (getUnitCountByLocation(gFortUnit, cMyID, cUnitStateABQ, dockLocation, 45.0) < 1) &&
       (kbGetBuildLimit(cMyID, gFortUnit) > kbUnitCount(cMyID, gFortUnit, cUnitStateABQ)) &&
       (aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, gFortUnit) < 0))
   {
      dockGuardType = gFortUnit;
      dockGuardRadius = 45.0;
   }

   if (getUnitCountByLocation(dockGuardType, cMyID, cUnitStateABQ, dockLocation, dockGuardRadius) > 0)
   {
      return;
   }

   if (dockGuardType == gTowerUnit)
   {
      if (getUnitCountByLocation(gFortUnit, cMyID, cUnitStateABQ, dockLocation, 45.0) > 0)
      {
         return;
      }

      if (kbGetBuildLimit(cMyID, gTowerUnit) <= kbUnitCount(cMyID, gTowerUnit, cUnitStateABQ))
      {
         debugLegendaryLeaders("dock guard skipped because the tower build limit is reached.");
         return;
      }
   }

   if (aiPlanGetIDByTypeAndVariableType(cPlanBuild, cBuildPlanBuildingTypeID, dockGuardType) >= 0)
   {
      return;
   }

   gLLNavalPrisonBuildPlanID = createLocationBuildPlan(dockGuardType, 1, 76, false, cMilitaryEscrowID, dockLocation, 1);
   debugLegendaryLeaders("creating dock guard build plan " + gLLNavalPrisonBuildPlanID + " using " + kbGetProtoUnitName(dockGuardType) + " near main dock for " + guardedShipCount + " warships at " + dockLocation);
}

rule legendaryAISurrenderMonitor
inactive
minInterval 8
{
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   float healthThreshold = llGetSurrenderHealthThreshold();
   float eliteSupportRadius = llGetSurrenderEliteSupportRadius();

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

      if (llTrackSurrenderingUnit(unitID) == true)
      {
         debugLegendaryLeaders("AI land unit " + unitID + " marked as surrendering.");
      }
   }

   if (gHaveWaterSpawnFlag == false)
   {
      return;
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

      if (llTrackSurrenderingUnit(unitID) == true)
      {
         debugLegendaryLeaders("AI warship " + unitID + " marked as surrendering.");
      }
   }
}

rule legendaryAISurrenderMove
inactive
minInterval 2
{
   if ((gLLPrisonSystemEnabled == false) || (gLLSurrenderUnitIDs < 0))
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
         debugLegendaryLeaders("AI surrendering unit " + unitID + " timed out and returned to normal control.");
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
         destination = llGetSurrenderDestination(unitID);
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
            debugLegendaryLeaders("AI prisoner " + unitID + " reclaimed by explorer for player " + originalOwnerID + ".");
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
         debugLegendaryLeaders("AI surrendering unit " + unitID + " reached prison custody for player " + captorPlayerID + ".");
         xsArraySetInt(gLLSurrenderStates, i, cLLSurrenderStateImprisoned);
         if ((originalOwnerID >= 0) && (kbIsPlayerEnemy(originalOwnerID) == true))
         {
            llSendLegendaryLeaderPrisonerLine(originalOwnerID, 120000);
         }
         llReleaseSurrenderingUnit(unitID);
         aiTaskUnitMove(unitID, destination);
         continue;
      }

      llReleaseSurrenderingUnit(unitID);
      aiTaskUnitMove(unitID, destination);
   }
}