//==============================================================================
/* aiPrisoners.xs

   Legendary Leaders prisoner-handling scaffolding.
   This file handles doctrine setup, prison-site planning, and a dedicated
   guard plan once surrendered-unit proxies are available.
*/
//==============================================================================

// Doctrine identifiers live in aiHeader.xs so leader includes can resolve them during parse.

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
         return ((protoUnitID == cUnitTypedeChinaco) || (protoUnitID == cUnitTypedeEmboscador));
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
      return (protoUnitID == cUnitTypedeEmboscador);
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
   int i = 0;
   for (i = 0; < numberFound)
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

bool llHasNearbyExplorerSupport(int unitID = -1, float radius = 24.0)
{
   if ((unitID < 0) || (radius <= 0.0))
   {
      return (false);
   }

   if (kbUnitIsType(unitID, cUnitTypeLogicalTypeLandMilitary) == false)
   {
      return (false);
   }

   int ownerID = kbUnitGetPlayerID(unitID);
   int heroQueryID = createSimpleUnitQuery(cUnitTypeHero, ownerID, cUnitStateAlive, kbUnitGetPosition(unitID), radius);
   int numberFound = kbUnitQueryExecute(heroQueryID);
   int i = 0;
   for (i = 0; < numberFound)
   {
      int nearbyUnitID = kbUnitQueryGetResult(heroQueryID, i);
      if (nearbyUnitID == unitID)
      {
         continue;
      }

      return (true);
   }

   return (false);
}

float llGetSurrenderHealthThreshold(void)
{
   return (0.25);
}

float llGetSurrenderEliteSupportRadius(void)
{
   return (24.0);
}

string llGetUnitSurrenderBlockReason(int unitID = -1, float healthThreshold = 0.50, float eliteSupportRadius = 24.0)
{
   if (unitID < 0)
   {
      return ("invalid");
   }

   if (kbUnitGetHealth(unitID) > healthThreshold)
   {
      return ("healthy");
   }

   if (llIsEliteUnit(unitID) == true)
   {
      debugLegendaryLeaders("unit " + unitID + " refused surrender because " + kbGetProtoUnitName(kbUnitGetProtoUnitID(unitID)) +
                            " is treated as elite for " + llGetPlayerCivName(kbUnitGetPlayerID(unitID)) + ".");
      return ("elite");
   }

   if (llHasNearbyEliteSupport(unitID, eliteSupportRadius) == true)
   {
      debugLegendaryLeaders("unit " + unitID + " refused surrender because nearby elite support is still present.");
      return ("elite-support");
   }

   return ("");
}

bool llCanUnitSurrender(int unitID = -1, float healthThreshold = 0.50, float eliteSupportRadius = 24.0)
{
   return (llGetUnitSurrenderBlockReason(unitID, healthThreshold, eliteSupportRadius) == "");
}

vector llGetAIRoutDestination(int playerID = -1)
{
   if (playerID < 0)
   {
      playerID = cMyID;
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

void llLogSurrenderBlock(string context = "", int unitID = -1, string reason = "")
{
   if ((unitID < 0) || (reason == "") || (reason == "healthy") || (reason == "elite") || (reason == "invalid"))
   {
      return;
   }

   llLogUnitAction(context + "-rout-blocked", unitID,
      "reason=" + reason + " proto=" + kbGetProtoUnitName(kbUnitGetProtoUnitID(unitID)));
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

   int i = 0;
   for (i = 0; < cLLMaxSurrenderUnits)
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
      case 0:
      {
         offsetX = 4.0;
         break;
      }
      case 1:
      {
         offsetX = -4.0;
         break;
      }
      case 2:
      {
         offsetZ = 4.0;
         break;
      }
      case 3:
      {
         offsetZ = -4.0;
         break;
      }
      case 4:
      {
         offsetX = 3.0;
         offsetZ = 3.0;
         break;
      }
      case 5:
      {
         offsetX = -3.0;
         offsetZ = -3.0;
         break;
      }
      default:
      {
         break;
      }
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

   int i = 0;
   for (i = 0; < cLLMaxSurrenderUnits)
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

void llAlertAlliesToEnemyPrison(vector prisonLocation = cInvalidVector)
{
   if (prisonLocation == cInvalidVector)
   {
      return;
   }

   string alertMessage = llGetAllyPrisonAlert();
   for (int player = 1; player < cNumberPlayers; player++)
   {
      if ((player == cMyID) || (kbIsPlayerAlly(player) == false) || (kbHasPlayerLost(player) == true))
      {
         continue;
      }

      llSendPrisonAlertToPlayer(player, prisonLocation, alertMessage);
   }
}

vector llFindEnemyPrisonLocation(void)
{
   gLLEnemyPrisonPlayerID = -1;

   if ((gLLSurrenderUnitIDs >= 0) && (gLLSurrenderStates >= 0) && (gLLSurrenderCaptors >= 0))
   {
      int i = 0;
      for (i = 0; < cLLMaxSurrenderUnits)
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
   gLLPrisonSystemEnabled = false;
   gLLAIRoutEnabled = true;
   llEnsureSurrenderArrays();
   xsEnableRule("legendaryAISurrenderMonitor");
   xsEnableRule("legendaryAISurrenderMove");
   llLogEvent("RULE", "AI non-elite rout enabled at 25% health; elite units hold and human-controlled units keep manual control");
   debugLegendaryLeaders("prison hook remapped to AI-only rout; non-elite AI units fall back to their return point once pressure breaks them.");
}

bool llHasPrisonStructure(void)
{
   if ((gLLPrisonStructureType < 0) || (gLLPrisonLocation == cInvalidVector))
   {
      return (false);
   }

   return (getUnitCountByLocation(gLLPrisonStructureType, cMyID, cUnitStateABQ, gLLPrisonLocation, 30.0) > 0);
}

int llGetPrisonWallCount(void)
{
   if (gLLPrisonLocation == cInvalidVector)
   {
      return (0);
   }

   return (getUnitCountByLocation(cUnitTypeAbstractWall, cMyID, cUnitStateABQ, gLLPrisonLocation, 20.0));
}

bool llHasPrisonWalls(void)
{
   return (llGetPrisonWallCount() > 0);
}

bool llHasCompletedPrisonWallRing(int minimumWallPieces = 6)
{
   if (llGetPrisonWallCount() < minimumWallPieces)
   {
      return (false);
   }

   if ((gLLPrisonWallPlanID >= 0) && (aiPlanGetActive(gLLPrisonWallPlanID) == true))
   {
      return (false);
   }

   return (true);
}

void llEnsurePrisonCompound(void)
{
   if ((gLLPrisonSystemEnabled == false) || (gLLPrisonerProxyType < 0))
   {
      return;
   }

   if (gLLPrisonLocation == cInvalidVector)
   {
      gLLPrisonLocation = llGetPrisonAnchorLocation();
      debugMilitary("Legendary Prison: established " + llGetPrisonerDoctrineName() + " prison anchor.");
   }

   if (gLLPrisonLocation == cInvalidVector)
   {
      return;
   }

   if ((gLLPrisonStructureType >= 0) && (llHasPrisonStructure() == false))
   {
      if ((gLLPrisonBuildPlanID < 0) || (aiPlanGetState(gLLPrisonBuildPlanID) < 0))
      {
         gLLPrisonBuildPlanID = createLocationBuildPlan(gLLPrisonStructureType, 1, 68, false, cMilitaryEscrowID, gLLPrisonLocation, 1);
         debugLegendaryLeaders("creating prison structure build plan " + gLLPrisonBuildPlanID + " at " + gLLPrisonLocation);
      }
      return;
   }

   if (llHasCompletedPrisonWallRing() == false)
   {
      if ((gLLPrisonWallPlanID < 0) || (aiPlanGetState(gLLPrisonWallPlanID) < 0))
      {
         int mainBaseID = kbBaseGetMainID(cMyID);
         gLLPrisonWallPlanID = aiPlanCreate("Legendary Prison Wall", cPlanBuildWall);
         if (gLLPrisonWallPlanID >= 0)
         {
            aiPlanSetVariableInt(gLLPrisonWallPlanID, cBuildWallPlanWallType, 0, cBuildWallPlanWallTypeRing);
            aiPlanAddUnitType(gLLPrisonWallPlanID, gEconUnit, 0, 1, 2);
            aiPlanSetVariableVector(gLLPrisonWallPlanID, cBuildWallPlanWallRingCenterPoint, 0, gLLPrisonLocation);
            aiPlanSetVariableFloat(gLLPrisonWallPlanID, cBuildWallPlanWallRingRadius, 0.0, 14.0);
            aiPlanSetVariableInt(gLLPrisonWallPlanID, cBuildWallPlanNumberOfGates, 0, 1);
            aiPlanSetBaseID(gLLPrisonWallPlanID, mainBaseID);
            aiPlanSetEscrowID(gLLPrisonWallPlanID, cEconomyEscrowID);
            aiPlanSetDesiredPriority(gLLPrisonWallPlanID, 69);
            aiPlanSetActive(gLLPrisonWallPlanID, true);
            debugLegendaryLeaders("creating prison wall plan " + gLLPrisonWallPlanID + " at " + gLLPrisonLocation);
         }
      }
   }
}

rule legendaryPrisonerMonitor
inactive
minInterval 10
{
   llLogRuleTick("legendaryPrisonerMonitor");
   if (gLLPrisonSystemEnabled == false)
   {
      return;
   }

   if (gLLPrisonerProxyType < 0)
   {
      return;
   }

   llEnsurePrisonCompound();

   if (gLLPrisonLocation == cInvalidVector)
   {
      return;
   }

   int prisonerCount = llGetPrisonerCount(gLLPrisonLocation, cLLPrisonHoldRadius);

   if (prisonerCount <= 0)
   {
      if ((gLLPrisonGuardPlanID >= 0) && (gLLPrisonLastSeenTime >= 0) && (xsGetTime() > gLLPrisonLastSeenTime + 45000))
      {
         debugLegendaryLeaders("destroying prison guard plan after prisoners were no longer detected.");
         llLogPlanEvent("destroy", gLLPrisonGuardPlanID, "reason=no prisoners detected");
         aiPlanDestroy(gLLPrisonGuardPlanID);
         gLLPrisonGuardPlanID = -1;
      }
      return;
   }

   gLLPrisonLastSeenTime = xsGetTime();

   if ((cvOkToTaunt == true) && (xsGetTime() > gLLPrisonLastTauntTime + 60000))
   {
      llSendEnemyPrisonTaunt(gLLPrisonLocation);
      gLLPrisonLastTauntTime = xsGetTime();
      debugLegendaryLeaders("enemy prison taunt fired at location " + gLLPrisonLocation);
   }
}

rule legendaryPrisonGuard
inactive
minInterval 15
{
   llLogRuleTick("legendaryPrisonGuard");
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
      llLogPlanEvent("create", gLLPrisonGuardPlanID, "name=Legendary Prison Guard");
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
   llLogRuleTick("legendaryPrisonRescueMonitor");
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

   llAlertAlliesToEnemyPrison(gLLEnemyPrisonLocation);
   gLLPrisonLastAllyAlertTime = xsGetTime();
   debugLegendaryLeaders("ally prison rescue alert sent for location " + gLLEnemyPrisonLocation);
}

rule legendaryNavalPrisonGuard
inactive
minInterval 20
{
   llLogRuleTick("legendaryNavalPrisonGuard");
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
   llLogRuleTick("legendaryAISurrenderMonitor");
   if (gLLAIRoutEnabled == false)
   {
      return;
   }

   float healthThreshold = llGetSurrenderHealthThreshold();
   float eliteSupportRadius = llGetSurrenderEliteSupportRadius();
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
         llLogSurrenderBlock("ai", unitID, surrenderBlockReason);
         continue;
      }

      if (llTrackSurrenderingUnit(unitID) == true)
      {
         vector routDestination = llGetAIRoutDestination(cMyID);
         if (routDestination != cInvalidVector)
         {
            llLogUnitAction("ai-rout-start", unitID, "destination=" + routDestination);
         }
         debugLegendaryLeaders("AI land unit " + unitID + " marked as routing.");
      }
   }
}

rule legendaryAISurrenderMove
inactive
minInterval 2
{
   llLogRuleTick("legendaryAISurrenderMove");
   if ((gLLAIRoutEnabled == false) || (gLLSurrenderUnitIDs < 0))
   {
      return;
   }

   float healthThreshold = llGetSurrenderHealthThreshold();

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
      int originalOwnerID = xsArrayGetInt(gLLSurrenderOriginalOwners, i);

      if (trackedDuration > cLLMaxSurrenderLifetime)
      {
         debugLegendaryLeaders("AI routed unit " + unitID + " timed out and returned to normal control.");
         llClearTrackedSurrenderIndex(i);
         continue;
      }

      if (kbUnitGetHealth(unitID) > healthThreshold)
      {
         llClearTrackedSurrenderIndex(i);
         continue;
      }

      vector destination = llGetAIRoutDestination(originalOwnerID);
      if (destination == cInvalidVector)
      {
         continue;
      }

      if (distance(kbUnitGetPosition(unitID), destination) < cLLSurrenderArrivalRadius)
      {
         llClearTrackedSurrenderIndex(i);
         llLogUnitAction("ai-rout-arrival", unitID, "destination=" + destination);
         continue;
      }

      if (llHasEnemyPressureForSurrender(unitID) == false)
      {
         debugLegendaryLeaders("AI routed unit " + unitID + " is falling back without immediate enemy pressure.");
      }

      llReleaseSurrenderingUnit(unitID);
      llLogUnitAction("ai-rout-move", unitID, "destination=" + destination);
      aiTaskUnitMove(unitID, destination);
   }
}