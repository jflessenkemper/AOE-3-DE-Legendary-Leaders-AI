//==============================================================================
/* getRandomIslandToBuildOn
   Finds an island to build a new colony on...
*/
//==============================================================================
vector getRandomIslandToBuildOn()
{
   vector startingLoc = kbGetPlayerStartingPosition(cMyID);
   int startingAreaID = kbAreaGetIDByPosition(startingLoc);
   int startingAreaGroupID = kbAreaGroupGetIDByPosition(startingLoc);
   vector islandLoc = cInvalidVector;
   vector islandAreaCentralPoint = cInvalidVector;
   int islandAreaID = -1;
   int islandAreaGroupID = -1;
   float xFloat = 0.0;
   float zFloat = 0.0;
   int numEnemyBuildings = -1;

   // Check if we have seen the enemy base, if so, this is our destination, not just some island...
   int closestBaseID = kbFindClosestBase(cPlayerRelationEnemy, startingLoc);
   vector closestBaseLocation = kbBaseGetLocation(kbBaseGetOwner(closestBaseID), closestBaseID);
   int closestBaseAreaGroupID = kbAreaGroupGetIDByPosition(closestBaseLocation);
   int enemyUnitQueryID = createSimpleUnitQuery(cUnitTypeBuilding, cPlayerRelationEnemyNotGaia, cUnitStateABQ);
   int enemyNumberFound = kbUnitQueryExecute(enemyUnitQueryID);
   int enemyAreaGroupID = -1;
   int areaGroupID = -1;
   int unitID = -1;
   for (i = 0; < enemyNumberFound)
   {
      unitID = kbUnitQueryGetResult(enemyUnitQueryID, i);
      if (kbHasPlayerLost(kbUnitGetPlayerID(unitID)) == true)
      {
         continue;
      }
      areaGroupID = kbAreaGroupGetIDByPosition(kbUnitGetPosition(unitID));
      if (areaGroupID == startingAreaGroupID)
      {
         continue;
      }
      enemyAreaGroupID = areaGroupID;
      //aiEcho("Found enemy buildings at: "+enemyAreaGroupID+"");
      break;
   }

   float mapWidth = kbGetMapXSize();
   float mapHeight = kbGetMapZSize();

   for (i = 0; < 90)
   {
      // Get a random vector on the map...
      xFloat = aiRandFloat(150.0, kbGetMapXSize());
      zFloat = aiRandFloat(150.0, kbGetMapZSize());
      islandLoc = xsVectorSet(xFloat, 0.0, zFloat);
      
      islandAreaID = kbAreaGetIDByPosition(islandLoc);
      islandAreaGroupID = kbAreaGroupGetIDByPosition(islandLoc);
      islandAreaCentralPoint = kbAreaGroupGetCenter(islandAreaGroupID);
      //numEnemyBuildings = getUnitCountByLocation(cUnitTypeBuilding, cPlayerRelationEnemyNotGaia, cUnitStateAlive, islandAreaCentralPoint, 20.0);
      if (kbAreaGroupGetType(islandAreaGroupID) == cAreaGroupTypeLand &&
          kbAreAreaGroupsPassableByLand(islandAreaGroupID, startingAreaGroupID) == false) //&& distance(islandLoc, startingLoc) > 270.0
      {
         gVillagersIslandX = xFloat;
         gVillagersIslandZ = zFloat;
         // aiEcho("Found another island! It is at: "+islandLoc+"");
         // sendStatement(1, cAICommPromptToAllyConfirm, islandLoc);
         gVillagersIslandAreaId = kbAreaGetIDByPosition(islandLoc);
         gVillagersIslandGroupId = kbAreaGroupGetIDByPosition(islandLoc);
         gVillagersIslandFound = true;
         return islandLoc;
      }
   }
   return cInvalidVector;
}