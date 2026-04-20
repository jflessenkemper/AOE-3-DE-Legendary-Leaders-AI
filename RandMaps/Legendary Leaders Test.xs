// Legendary Leaders Test
// Minimal stable 2v2 land arena for observing AI behavior.

int TeamNum = cNumberTeams;
int PlayerNum = cNumberNonGaiaPlayers;
int numPlayer = cNumberPlayers;

void main(void)
{
    rmSetStatusText("", 0.01);

    int effectivePlayers = PlayerNum;
    if (effectivePlayers < 4)
    {
        effectivePlayers = 4;
    }

    int playerTiles = 13500;
    int size = 2.0 * sqrt(effectivePlayers * playerTiles);
    rmSetMapSize(size, size);
    rmSetSeaLevel(0.0);
    rmSetLightingSet("Texas_Skirmish");
    rmSetBaseTerrainMix("texas_dirt_Skirmish");
    rmTerrainInitialize("grass", 0.0);
    rmSetMapType("texas");
    rmSetMapType("land");
    rmSetMapType("grass");
    rmSetWorldCircleConstraint(true);

    if ((PlayerNum == 4) && (TeamNum == 2) && (rmGetNumberPlayersOnTeam(0) == 2) && (rmGetNumberPlayersOnTeam(1) == 2))
    {
        rmPlacePlayer(1, 0.18, 0.33);
        rmPlacePlayer(2, 0.18, 0.67);
        rmPlacePlayer(3, 0.82, 0.33);
        rmPlacePlayer(4, 0.82, 0.67);
    }
    else if (PlayerNum == 2)
    {
        rmPlacePlayer(1, 0.18, 0.50);
        rmPlacePlayer(2, 0.82, 0.50);
    }
    else
    {
        rmSetPlacementSection(0.0, 0.999);
        rmSetTeamSpacingModifier(0.75);
        rmPlacePlayersCircular(0.34, 0.34, 0.0);
    }

    int classStartingResource = rmDefineClass("ll starting resource");
    int classForest = rmDefineClass("ll forest");
    int classGold = rmDefineClass("ll gold");

    int avoidStartingResources = rmCreateClassDistanceConstraint("ll avoid starting resources", classStartingResource, 8.0);
    int avoidForest = rmCreateClassDistanceConstraint("ll avoid forest", classForest, 20.0);
    int avoidGold = rmCreateClassDistanceConstraint("ll avoid gold", classGold, 18.0);
    int avoidTownCenter = rmCreateTypeDistanceConstraint("ll avoid town center", "townCenter", 26.0);
    int avoidTownCenterFar = rmCreateTypeDistanceConstraint("ll avoid town center far", "townCenter", 40.0);
    int avoidAll = rmCreateTypeDistanceConstraint("ll avoid all", "all", 6.0);
    int avoidImpassableLand = rmCreateTerrainDistanceConstraint("ll avoid impassable land", "land", false, 6.0);

    int centerLaneID = rmCreateArea("ll center lane");
    rmSetAreaSize(centerLaneID, 0.030, 0.030);
    rmSetAreaLocation(centerLaneID, 0.50, 0.50);
    rmSetAreaMix(centerLaneID, "texas_dirt_Skirmish");
    rmSetAreaCoherence(centerLaneID, 1.0);
    rmBuildArea(centerLaneID);

    int northLaneID = rmCreateArea("ll north lane");
    rmSetAreaSize(northLaneID, 0.020, 0.020);
    rmSetAreaLocation(northLaneID, 0.50, 0.72);
    rmSetAreaMix(northLaneID, "texas_grass_Skrimish");
    rmSetAreaCoherence(northLaneID, 0.9);
    rmBuildArea(northLaneID);

    int southLaneID = rmCreateArea("ll south lane");
    rmSetAreaSize(southLaneID, 0.020, 0.020);
    rmSetAreaLocation(southLaneID, 0.50, 0.28);
    rmSetAreaMix(southLaneID, "texas_grass_Skrimish");
    rmSetAreaCoherence(southLaneID, 0.9);
    rmBuildArea(southLaneID);

    rmSetStatusText("", 0.20);

    int TCID = rmCreateObjectDef("ll player tc");
    if (rmGetNomadStart())
    {
        rmAddObjectDefItem(TCID, "CoveredWagon", 1, 0.0);
    }
    else
    {
        rmAddObjectDefItem(TCID, "TownCenter", 1, 0.0);
    }
    rmAddObjectDefToClass(TCID, classStartingResource);
    rmSetObjectDefMinDistance(TCID, 0.0);
    rmSetObjectDefMaxDistance(TCID, 0.0);

    int startingUnits = rmCreateStartingUnitsObjectDef(5.0);

    int playerGoldID = rmCreateObjectDef("ll starting mine");
    rmAddObjectDefItem(playerGoldID, "MineCopper", 1, 0.0);
    rmSetObjectDefMinDistance(playerGoldID, 16.0);
    rmSetObjectDefMaxDistance(playerGoldID, 18.0);
    rmAddObjectDefToClass(playerGoldID, classStartingResource);
    rmAddObjectDefToClass(playerGoldID, classGold);
    rmAddObjectDefConstraint(playerGoldID, avoidStartingResources);

    int playerGold2ID = rmCreateObjectDef("ll second mine");
    rmAddObjectDefItem(playerGold2ID, "MineCopper", 1, 0.0);
    rmSetObjectDefMinDistance(playerGold2ID, 26.0);
    rmSetObjectDefMaxDistance(playerGold2ID, 30.0);
    rmAddObjectDefToClass(playerGold2ID, classStartingResource);
    rmAddObjectDefToClass(playerGold2ID, classGold);
    rmAddObjectDefConstraint(playerGold2ID, avoidStartingResources);
    rmAddObjectDefConstraint(playerGold2ID, avoidGold);

    int playerTreeID = rmCreateObjectDef("ll starting trees");
    rmAddObjectDefItem(playerTreeID, "TreeTexas", 8, 5.0);
    rmSetObjectDefMinDistance(playerTreeID, 12.0);
    rmSetObjectDefMaxDistance(playerTreeID, 18.0);
    rmAddObjectDefToClass(playerTreeID, classStartingResource);
    rmAddObjectDefToClass(playerTreeID, classForest);
    rmAddObjectDefConstraint(playerTreeID, avoidStartingResources);
    rmAddObjectDefConstraint(playerTreeID, avoidForest);
    rmAddObjectDefConstraint(playerTreeID, avoidGold);

    int playerHuntID = rmCreateObjectDef("ll starting hunt");
    rmAddObjectDefItem(playerHuntID, "bison", 8, 6.0);
    rmSetObjectDefCreateHerd(playerHuntID, true);
    rmSetObjectDefMinDistance(playerHuntID, 12.0);
    rmSetObjectDefMaxDistance(playerHuntID, 16.0);
    rmAddObjectDefToClass(playerHuntID, classStartingResource);
    rmAddObjectDefConstraint(playerHuntID, avoidStartingResources);

    int playerHunt2ID = rmCreateObjectDef("ll second hunt");
    rmAddObjectDefItem(playerHunt2ID, "deer", 9, 6.0);
    rmSetObjectDefCreateHerd(playerHunt2ID, true);
    rmSetObjectDefMinDistance(playerHunt2ID, 24.0);
    rmSetObjectDefMaxDistance(playerHunt2ID, 30.0);
    rmAddObjectDefToClass(playerHunt2ID, classStartingResource);
    rmAddObjectDefConstraint(playerHunt2ID, avoidStartingResources);

    int playerCowID = rmCreateObjectDef("ll starting cow");
    rmAddObjectDefItem(playerCowID, "cow", 2, 4.0);
    rmSetObjectDefMinDistance(playerCowID, 10.0);
    rmSetObjectDefMaxDistance(playerCowID, 14.0);
    rmAddObjectDefToClass(playerCowID, classStartingResource);
    rmAddObjectDefConstraint(playerCowID, avoidStartingResources);

    int playerNuggetID = rmCreateObjectDef("ll starting nugget");
    rmAddObjectDefItem(playerNuggetID, "Nugget", 1, 0.0);
    rmSetNuggetDifficulty(1, 1);
    rmSetObjectDefMinDistance(playerNuggetID, 22.0);
    rmSetObjectDefMaxDistance(playerNuggetID, 26.0);
    rmAddObjectDefToClass(playerNuggetID, classStartingResource);
    rmAddObjectDefConstraint(playerNuggetID, avoidStartingResources);

    for (int i = 1; < numPlayer)
    {
        float tcX = rmPlayerLocXFraction(i);
        float tcZ = rmPlayerLocZFraction(i);

        rmPlaceObjectDefAtLoc(TCID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(startingUnits, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerGoldID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerGold2ID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerHuntID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerHunt2ID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerCowID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerNuggetID, i, tcX, tcZ);
    }

    rmSetStatusText("", 0.60);

    int laneMineID = rmCreateObjectDef("ll lane mine");
    rmAddObjectDefItem(laneMineID, "MineCopper", 1, 0.0);
    rmAddObjectDefToClass(laneMineID, classGold);
    rmAddObjectDefConstraint(laneMineID, avoidTownCenterFar);
    rmAddObjectDefConstraint(laneMineID, avoidGold);

    int laneHuntID = rmCreateObjectDef("ll lane hunt");
    rmAddObjectDefItem(laneHuntID, "bison", 8, 6.0);
    rmSetObjectDefCreateHerd(laneHuntID, true);
    rmAddObjectDefConstraint(laneHuntID, avoidTownCenter);
    rmAddObjectDefConstraint(laneHuntID, avoidAll);
    rmAddObjectDefConstraint(laneHuntID, avoidImpassableLand);

    int laneNuggetID = rmCreateObjectDef("ll lane nugget");
    rmAddObjectDefItem(laneNuggetID, "Nugget", 1, 0.0);
    rmSetNuggetDifficulty(2, 2);
    rmAddObjectDefConstraint(laneNuggetID, avoidTownCenterFar);
    rmAddObjectDefConstraint(laneNuggetID, avoidAll);

    int forestPatchAID = rmCreateArea("ll forest patch a");
    rmSetAreaSize(forestPatchAID, 0.020, 0.020);
    rmSetAreaLocation(forestPatchAID, 0.32, 0.50);
    rmSetAreaForestType(forestPatchAID, "Texas Forest");
    rmSetAreaForestDensity(forestPatchAID, 0.8);
    rmSetAreaForestClumpiness(forestPatchAID, 0.4);
    rmSetAreaForestUnderbrush(forestPatchAID, 0.0);
    rmSetAreaCoherence(forestPatchAID, 0.6);
    rmAddAreaToClass(forestPatchAID, classForest);
    rmAddAreaConstraint(forestPatchAID, avoidTownCenterFar);
    rmBuildArea(forestPatchAID);

    int forestPatchBID = rmCreateArea("ll forest patch b");
    rmSetAreaSize(forestPatchBID, 0.020, 0.020);
    rmSetAreaLocation(forestPatchBID, 0.68, 0.50);
    rmSetAreaForestType(forestPatchBID, "Texas Forest");
    rmSetAreaForestDensity(forestPatchBID, 0.8);
    rmSetAreaForestClumpiness(forestPatchBID, 0.4);
    rmSetAreaForestUnderbrush(forestPatchBID, 0.0);
    rmSetAreaCoherence(forestPatchBID, 0.6);
    rmAddAreaToClass(forestPatchBID, classForest);
    rmAddAreaConstraint(forestPatchBID, avoidTownCenterFar);
    rmBuildArea(forestPatchBID);

    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.50, 0.50, 2);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.50, 0.72, 1);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.50, 0.28, 1);

    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.50, 0.50, 2);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.50, 0.72, 1);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.50, 0.28, 1);

    rmPlaceObjectDefAtLoc(laneNuggetID, 0, 0.50, 0.50, 1);
    rmPlaceObjectDefAtLoc(laneNuggetID, 0, 0.42, 0.72, 1);
    rmPlaceObjectDefAtLoc(laneNuggetID, 0, 0.58, 0.28, 1);

    rmSetStatusText("", 1.00);
}// Legendary Leaders Test
// Flat 2v2-oriented test arena for validating surrender, prison routing,
// elite support, explorer reclaim, and AI attack shape.

include "mercenaries.xs";
include "ypAsianInclude.xs";
include "ypKOTHInclude.xs";

int TeamNum = cNumberTeams;
int PlayerNum = cNumberNonGaiaPlayers;
int numPlayer = cNumberPlayers;

void llBroadcastTestMessage(string message)
{
    rmAddTriggerEffect("Send Chat");
    rmSetTriggerEffectParamInt("PlayerID", 0);
    rmSetTriggerEffectParam("Message", message);
}

void llGrantPhaseResources(int foodAmount, int woodAmount, int xpAmount)
{
    for (int playerID = 1; < numPlayer)
    {
        if (foodAmount > 0)
        {
            rmAddTriggerEffect("Grant Resources");
            rmSetTriggerEffectParamInt("PlayerID", playerID);
            rmSetTriggerEffectParam("ResName", "Food");
            rmSetTriggerEffectParamInt("Amount", foodAmount);
        }

        if (woodAmount > 0)
        {
            rmAddTriggerEffect("Grant Resources");
            rmSetTriggerEffectParamInt("PlayerID", playerID);
            rmSetTriggerEffectParam("ResName", "Wood");
            rmSetTriggerEffectParamInt("Amount", woodAmount);
        }

        if (xpAmount > 0)
        {
            rmAddTriggerEffect("Grant Resources");
            rmSetTriggerEffectParamInt("PlayerID", playerID);
            rmSetTriggerEffectParam("ResName", "XP");
            rmSetTriggerEffectParamInt("Amount", xpAmount);
        }
    }
}

void llDisableTriggerByName(string triggerName)
{
    rmAddTriggerEffect("Disable Trigger");
    rmSetTriggerEffectParamInt("EventID", rmTriggerID(triggerName));
}

void main(void)
{
    rmSetStatusText("", 0.01);

    int effectivePlayers = PlayerNum;
    if (effectivePlayers < 4)
        effectivePlayers = 4;

    int playerTiles = 13500;
    int size = 2.0 * sqrt(effectivePlayers * playerTiles);
    rmSetMapSize(size, size);
    rmSetSeaLevel(0.0);
    rmSetBaseTerrainMix("texas_grass");
    rmTerrainInitialize("grass", 0.0);
    rmSetLightingSet("Texas_Skirmish");
    rmSetMapType("texas");
    rmSetMapType("land");
    rmSetMapType("grass");
    rmSetWorldCircleConstraint(true);

    if ((PlayerNum == 4) && (TeamNum == 2) && (rmGetNumberPlayersOnTeam(0) == 2) && (rmGetNumberPlayersOnTeam(1) == 2))
    {
        // Place full teams on fixed west/east sides so slot order does not matter.
        rmSetPlacementTeam(0);
        rmSetPlayerPlacementArea(0.10, 0.18, 0.26, 0.82);
        rmPlacePlayersLine(0.18, 0.33, 0.18, 0.67, 0.0, 0.0);

        rmSetPlacementTeam(1);
        rmSetPlayerPlacementArea(0.74, 0.18, 0.90, 0.82);
        rmPlacePlayersLine(0.82, 0.33, 0.82, 0.67, 0.0, 0.0);

        rmSetPlacementTeam(-1);
    }
    else if (PlayerNum == 2)
    {
        rmPlacePlayer(1, 0.18, 0.50);
        rmPlacePlayer(2, 0.82, 0.50);
    }
    else
    {
        rmPlacePlayersCircular(0.35, 0.35, 0.0);
    }

    int classStartingResource = rmDefineClass("ll starting resource");
    int classGold = rmDefineClass("ll gold");
    int classForest = rmDefineClass("ll forest");

    int avoidStartingResourcesShort = rmCreateClassDistanceConstraint("ll avoid starting resources short", classStartingResource, 8.0);
    int avoidStartingResources = rmCreateClassDistanceConstraint("ll avoid starting resources", classStartingResource, 12.0);
    int avoidGoldShort = rmCreateClassDistanceConstraint("ll avoid gold short", classGold, 16.0);
    int avoidForestShort = rmCreateClassDistanceConstraint("ll avoid forest short", classForest, 12.0);
    int avoidTownCenter = rmCreateTypeDistanceConstraint("ll avoid town center", "townCenter", 26.0);
    int avoidTownCenterFar = rmCreateTypeDistanceConstraint("ll avoid town center far", "townCenter", 60.0);
    int avoidWaterShort = rmCreateTerrainDistanceConstraint("ll avoid water short", "land", false, 10.0);
    int stayNearWater = rmCreateTerrainDistanceConstraint("ll stay near water", "land", true, 8.0);

    int westSouthStartID = rmCreateArea("ll west south start");
    rmSetAreaSize(westSouthStartID, 0.022);
    rmSetAreaLocation(westSouthStartID, 0.18, 0.33);
    rmSetAreaMix(westSouthStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(westSouthStartID, 1.0);
    rmBuildArea(westSouthStartID);

    int westNorthStartID = rmCreateArea("ll west north start");
    rmSetAreaSize(westNorthStartID, 0.022);
    rmSetAreaLocation(westNorthStartID, 0.18, 0.67);
    rmSetAreaMix(westNorthStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(westNorthStartID, 1.0);
    rmBuildArea(westNorthStartID);

    int eastSouthStartID = rmCreateArea("ll east south start");
    rmSetAreaSize(eastSouthStartID, 0.022);
    rmSetAreaLocation(eastSouthStartID, 0.82, 0.33);
    rmSetAreaMix(eastSouthStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(eastSouthStartID, 1.0);
    rmBuildArea(eastSouthStartID);

    int eastNorthStartID = rmCreateArea("ll east north start");
    rmSetAreaSize(eastNorthStartID, 0.022);
    rmSetAreaLocation(eastNorthStartID, 0.82, 0.67);
    rmSetAreaMix(eastNorthStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(eastNorthStartID, 1.0);
    rmBuildArea(eastNorthStartID);

    int northLaneID = rmCreateArea("ll north lane");
    rmSetAreaSize(northLaneID, 0.018);
    rmSetAreaLocation(northLaneID, 0.50, 0.72);
    rmSetAreaMix(northLaneID, "texas_dirt_Skirmish");
    rmSetAreaCoherence(northLaneID, 0.9);
    rmBuildArea(northLaneID);

    int centerLaneID = rmCreateArea("ll center lane");
    rmSetAreaSize(centerLaneID, 0.020);
    rmSetAreaLocation(centerLaneID, 0.50, 0.50);
    rmSetAreaMix(centerLaneID, "texas_dirt_Skirmish");
    rmSetAreaCoherence(centerLaneID, 1.0);
    rmBuildArea(centerLaneID);

    int southLaneID = rmCreateArea("ll south lane");
    rmSetAreaSize(southLaneID, 0.018);
    rmSetAreaLocation(southLaneID, 0.50, 0.28);
    rmSetAreaMix(southLaneID, "texas_dirt_Skirmish");
    rmSetAreaCoherence(southLaneID, 0.9);
    rmBuildArea(southLaneID);

    int northWaterLaneID = rmCreateArea("ll north water lane");
    rmSetAreaSize(northWaterLaneID, 0.080);
    rmSetAreaLocation(northWaterLaneID, 0.50, 0.86);
    rmSetAreaWaterType(northWaterLaneID, "texas river");
    rmSetAreaBaseHeight(northWaterLaneID, -6.0);
    rmSetAreaCoherence(northWaterLaneID, 0.95);
    rmBuildArea(northWaterLaneID);

    int southWaterLaneID = rmCreateArea("ll south water lane");
    rmSetAreaSize(southWaterLaneID, 0.080);
    rmSetAreaLocation(southWaterLaneID, 0.50, 0.14);
    rmSetAreaWaterType(southWaterLaneID, "texas river");
    rmSetAreaBaseHeight(southWaterLaneID, -6.0);
    rmSetAreaCoherence(southWaterLaneID, 0.95);
    rmBuildArea(southWaterLaneID);

    for (int i = 1; < numPlayer)
    {
        int playerAreaID = rmCreateArea("playerarea" + i);
        rmSetPlayerArea(i, playerAreaID);
        rmSetAreaSize(playerAreaID, rmAreaTilesToFraction(120));
        rmSetAreaCoherence(playerAreaID, 0.0);
        rmSetAreaWarnFailure(playerAreaID, false);
        rmSetAreaMix(playerAreaID, "texas_grass_Skrimish");
        rmSetAreaLocPlayer(playerAreaID, i);
        rmBuildArea(playerAreaID);
    }

    rmSetStatusText("", 0.20);

    int TCID = rmCreateObjectDef("ll player tc");
    int startingUnits = rmCreateStartingUnitsObjectDef(5.0);
    if (rmGetNomadStart())
        rmAddObjectDefItem(TCID, "CoveredWagon", 1, 0.0);
    else
        rmAddObjectDefItem(TCID, "TownCenter", 1, 0.0);
    rmAddObjectDefToClass(TCID, classStartingResource);
    rmSetObjectDefMinDistance(TCID, 0.0);
    rmSetObjectDefMaxDistance(TCID, 0.0);

    int playerGoldID = rmCreateObjectDef("ll starting mine");
    rmAddObjectDefItem(playerGoldID, "MineCopper", 1, 0.0);
    rmSetObjectDefMinDistance(playerGoldID, 16.0);
    rmSetObjectDefMaxDistance(playerGoldID, 16.0);
    rmAddObjectDefToClass(playerGoldID, classStartingResource);
    rmAddObjectDefToClass(playerGoldID, classGold);
    rmAddObjectDefConstraint(playerGoldID, avoidStartingResourcesShort);

    int playerGold2ID = rmCreateObjectDef("ll second mine");
    rmAddObjectDefItem(playerGold2ID, "MineCopper", 1, 0.0);
    rmSetObjectDefMinDistance(playerGold2ID, 28.0);
    rmSetObjectDefMaxDistance(playerGold2ID, 30.0);
    rmAddObjectDefToClass(playerGold2ID, classStartingResource);
    rmAddObjectDefToClass(playerGold2ID, classGold);
    rmAddObjectDefConstraint(playerGold2ID, avoidStartingResourcesShort);
    rmAddObjectDefConstraint(playerGold2ID, avoidGoldShort);

    int playerTreeID = rmCreateObjectDef("ll starting tree");
    rmAddObjectDefItem(playerTreeID, "TreeTexas", 1, 0.0);
    rmSetObjectDefMinDistance(playerTreeID, 13.0);
    rmSetObjectDefMaxDistance(playerTreeID, 18.0);
    rmAddObjectDefToClass(playerTreeID, classStartingResource);
    rmAddObjectDefToClass(playerTreeID, classForest);
    rmAddObjectDefConstraint(playerTreeID, avoidStartingResourcesShort);
    rmAddObjectDefConstraint(playerTreeID, avoidGoldShort);
    rmAddObjectDefConstraint(playerTreeID, avoidForestShort);

    int playerHerdID = rmCreateObjectDef("ll starting herd");
    rmAddObjectDefItem(playerHerdID, "bison", 8, 4.0);
    rmSetObjectDefMinDistance(playerHerdID, 12.0);
    rmSetObjectDefMaxDistance(playerHerdID, 14.0);
    rmSetObjectDefCreateHerd(playerHerdID, true);
    rmAddObjectDefToClass(playerHerdID, classStartingResource);
    rmAddObjectDefConstraint(playerHerdID, avoidStartingResourcesShort);

    int playerHerd2ID = rmCreateObjectDef("ll second herd");
    rmAddObjectDefItem(playerHerd2ID, "deer", 10, 6.0);
    rmSetObjectDefMinDistance(playerHerd2ID, 26.0);
    rmSetObjectDefMaxDistance(playerHerd2ID, 32.0);
    rmSetObjectDefCreateHerd(playerHerd2ID, true);
    rmAddObjectDefToClass(playerHerd2ID, classStartingResource);
    rmAddObjectDefConstraint(playerHerd2ID, avoidStartingResources);

    int playerCowID = rmCreateObjectDef("ll starting cow");
    rmAddObjectDefItem(playerCowID, "cow", 2, 4.0);
    rmSetObjectDefMinDistance(playerCowID, 10.0);
    rmSetObjectDefMaxDistance(playerCowID, 14.0);
    rmAddObjectDefToClass(playerCowID, classStartingResource);
    rmAddObjectDefConstraint(playerCowID, avoidStartingResourcesShort);

    int playerNuggetID = rmCreateObjectDef("ll starting nugget");
    rmAddObjectDefItem(playerNuggetID, "Nugget", 1, 0.0);
    rmSetNuggetDifficulty(1, 1);
    rmSetObjectDefMinDistance(playerNuggetID, 24.0);
    rmSetObjectDefMaxDistance(playerNuggetID, 28.0);
    rmAddObjectDefToClass(playerNuggetID, classStartingResource);
    rmAddObjectDefConstraint(playerNuggetID, avoidStartingResourcesShort);

    for (int i = 1; < numPlayer)
    {
        float tcX = rmPlayerLocXFraction(i);
        float tcZ = rmPlayerLocZFraction(i);

        rmPlaceObjectDefAtLoc(TCID, i, tcX, tcZ);

        rmPlaceObjectDefAtLoc(startingUnits, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerGoldID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerGold2ID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerHerdID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerHerd2ID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerCowID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerNuggetID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
        rmPlaceObjectDefAtLoc(playerTreeID, i, tcX, tcZ);
    }

    rmSetStatusText("", 0.55);

    int laneMineID = rmCreateObjectDef("ll lane mine");
    rmAddObjectDefItem(laneMineID, "MineCopper", 1, 0.0);
    rmAddObjectDefToClass(laneMineID, classGold);
    rmAddObjectDefConstraint(laneMineID, avoidTownCenterFar);

    int waterFishID = rmCreateObjectDef("ll water fish");
    rmAddObjectDefItem(waterFishID, "FishSalmon", 3, 10.0);
    rmSetObjectDefMinDistance(waterFishID, 0.0);
    rmSetObjectDefMaxDistance(waterFishID, 12.0);

    int waterWhaleID = rmCreateObjectDef("ll water whale");
    rmAddObjectDefItem(waterWhaleID, "MinkeWhale", 1, 0.0);
    rmSetObjectDefMinDistance(waterWhaleID, 0.0);
    rmSetObjectDefMaxDistance(waterWhaleID, 10.0);

    int shoreMineID = rmCreateObjectDef("ll shore mine");
    rmAddObjectDefItem(shoreMineID, "MineCopper", 1, 0.0);
    rmAddObjectDefToClass(shoreMineID, classGold);
    rmAddObjectDefConstraint(shoreMineID, avoidTownCenterFar);
    rmAddObjectDefConstraint(shoreMineID, stayNearWater);

    int shoreTreePatchID = rmCreateObjectDef("ll shore tree patch");
    rmAddObjectDefItem(shoreTreePatchID, "TreeTexas", 8, 5.0);
    rmAddObjectDefToClass(shoreTreePatchID, classForest);
    rmAddObjectDefConstraint(shoreTreePatchID, avoidTownCenter);
    rmAddObjectDefConstraint(shoreTreePatchID, avoidForestShort);
    rmAddObjectDefConstraint(shoreTreePatchID, stayNearWater);

    int laneHuntID = rmCreateObjectDef("ll lane hunt");
    rmAddObjectDefItem(laneHuntID, "bison", 8, 6.0);
    rmSetObjectDefCreateHerd(laneHuntID, true);
    rmAddObjectDefConstraint(laneHuntID, avoidTownCenter);

    int midNuggetID = rmCreateObjectDef("ll mid nugget");
    rmAddObjectDefItem(midNuggetID, "Nugget", 1, 0.0);
    rmSetNuggetDifficulty(2, 2);
    rmAddObjectDefConstraint(midNuggetID, avoidTownCenterFar);

    int sideTreePatchID = rmCreateObjectDef("ll side tree patch");
    rmAddObjectDefItem(sideTreePatchID, "TreeTexas", 10, 6.0);
    rmAddObjectDefToClass(sideTreePatchID, classForest);
    rmAddObjectDefConstraint(sideTreePatchID, avoidTownCenter);
    rmAddObjectDefConstraint(sideTreePatchID, avoidForestShort);

    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.38, 0.72);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.62, 0.72);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.38, 0.50);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.62, 0.50);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.38, 0.28);
    rmPlaceObjectDefAtLoc(laneMineID, 0, 0.62, 0.28);

    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.45, 0.72);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.55, 0.72);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.45, 0.50);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.55, 0.50);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.45, 0.28);
    rmPlaceObjectDefAtLoc(laneHuntID, 0, 0.55, 0.28);

    rmPlaceObjectDefAtLoc(midNuggetID, 0, 0.50, 0.72);
    rmPlaceObjectDefAtLoc(midNuggetID, 0, 0.50, 0.50);
    rmPlaceObjectDefAtLoc(midNuggetID, 0, 0.50, 0.28);

    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.22, 0.86);
    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.50, 0.86);
    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.78, 0.86);
    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.22, 0.14);
    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.50, 0.14);
    rmPlaceObjectDefAtLoc(waterFishID, 0, 0.78, 0.14);

    rmPlaceObjectDefAtLoc(waterWhaleID, 0, 0.40, 0.86);
    rmPlaceObjectDefAtLoc(waterWhaleID, 0, 0.60, 0.86);
    rmPlaceObjectDefAtLoc(waterWhaleID, 0, 0.40, 0.14);
    rmPlaceObjectDefAtLoc(waterWhaleID, 0, 0.60, 0.14);

    rmPlaceObjectDefAtLoc(shoreMineID, 0, 0.18, 0.80);
    rmPlaceObjectDefAtLoc(shoreMineID, 0, 0.82, 0.80);
    rmPlaceObjectDefAtLoc(shoreMineID, 0, 0.18, 0.20);
    rmPlaceObjectDefAtLoc(shoreMineID, 0, 0.82, 0.20);

    rmPlaceObjectDefAtLoc(shoreTreePatchID, 0, 0.14, 0.88);
    rmPlaceObjectDefAtLoc(shoreTreePatchID, 0, 0.86, 0.88);
    rmPlaceObjectDefAtLoc(shoreTreePatchID, 0, 0.14, 0.12);
    rmPlaceObjectDefAtLoc(shoreTreePatchID, 0, 0.86, 0.12);

    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.10, 0.16);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.10, 0.84);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.90, 0.16);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.90, 0.84);

    rmSetStatusText("", 1.00);
}