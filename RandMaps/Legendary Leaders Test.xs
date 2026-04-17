// Legendary Leaders Test
// Flat 1v1-oriented test arena for validating surrender, prison routing,
// elite support, explorer reclaim, and AI attack shape.

int TeamNum = cNumberTeams;
int PlayerNum = cNumberNonGaiaPlayers;
int numPlayer = cNumberPlayers;

void main(void)
{
    rmSetStatusText("", 0.01);

    int effectivePlayers = PlayerNum;
    if (effectivePlayers < 2)
        effectivePlayers = 2;

    int playerTiles = 13500;
    int size = 2.0 * sqrt(effectivePlayers * playerTiles);
    rmSetMapSize(size, size);
    rmSetSeaLevel(0.0);
    rmTerrainInitialize("grass", 0.0);
    rmSetLightingSet("Texas_Skirmish");

    if (PlayerNum == 2)
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

    int westStartID = rmCreateArea("ll west start");
    rmSetAreaSize(westStartID, 0.03);
    rmSetAreaLocation(westStartID, 0.18, 0.50);
    rmSetAreaMix(westStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(westStartID, 1.0);
    rmBuildArea(westStartID);

    int eastStartID = rmCreateArea("ll east start");
    rmSetAreaSize(eastStartID, 0.03);
    rmSetAreaLocation(eastStartID, 0.82, 0.50);
    rmSetAreaMix(eastStartID, "texas_grass_Skrimish");
    rmSetAreaCoherence(eastStartID, 1.0);
    rmBuildArea(eastStartID);

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
        rmPlaceObjectDefAtLoc(TCID, i, rmPlayerLocXFraction(i), rmPlayerLocZFraction(i));
        vector tcLoc = rmGetUnitPosition(rmGetUnitPlacedOfPlayer(TCID, i));
        float tcX = rmXMetersToFraction(xsVectorGetX(tcLoc));
        float tcZ = rmZMetersToFraction(xsVectorGetZ(tcLoc));

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

    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.10, 0.16);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.10, 0.84);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.90, 0.16);
    rmPlaceObjectDefAtLoc(sideTreePatchID, 0, 0.90, 0.84);

    rmSetStatusText("", 1.00);
}