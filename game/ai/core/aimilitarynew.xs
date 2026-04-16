//==============================================================================
// militaryBuildingsManager
// Make sure we build extra military buildings if we have the money.
//==============================================================================
rule militaryBuildingsManager
inactive
minInterval 10
{
    if ((kbUnitCount(cMyID, cUnitTypeBarracks, cUnitStateABQ) < 10) && (kbGetAge() > cAge4) &&
    gExcessResources)
    {
        createSimpleBuildPlan(cUnitTypeBarracks, 1, 60, true, cMilitaryEscrowID, kbBaseGetMainID(cMyID), 1);
    }

    if ((kbUnitCount(cMyID, cUnitTypeAbstractStables, cUnitStateABQ) < 10) && (kbGetAge() > cAge4) &&
    gExcessResources)
    {
        createSimpleBuildPlan(cUnitTypeAbstractStables, 1, 60, true, cMilitaryEscrowID, kbBaseGetMainID(cMyID), 1);
    }

    if ((kbUnitCount(cMyID, cUnitTypeArtilleryDepot, cUnitStateABQ) < 7) && (kbGetAge() > cAge4) &&
    gExcessResources)
    {
        createSimpleBuildPlan(cUnitTypeArtilleryDepot, 1, 59, true, cMilitaryEscrowID, kbBaseGetMainID(cMyID), 1);
    }
    //updateMilitaryTrainPlanBuildings(kbBaseGetMainID(cMyID));
}
//==============================================================================
// setUnitPickerRoyalGuardPreference
// Sets higher preference for civilization-specific Royal Guard units.
// Call this in setUnitPickerPreference() after the base preferences are set.
//==============================================================================
void setUnitPickerRoyalGuardPreference(int upID = -1)
{
   if (upID < 0)
   {
      return;
   }

   // Only boost Royal Guard preferences from Age 3 onwards when upgrades become available
   if (kbGetAge() < cAge3)
   {
      return;
   }

   // High preference value for Royal Guard units
   float royalGuardPref = 0.9;
   // Lower preference for units that are outclassed by Royal Guard equivalents
   float outclassedPref = 0.2;

   switch (cMyCiv)
   {
      // European civilizations
      case cCivBritish:
      {
         // Redcoats (Musketeers)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeMusketeer, royalGuardPref);
         break;
      }
      case cCivDutch:
      {
         // Nassau Halberdiers (Halberdiers) and Carabiniers (Ruyters)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeHalberdier, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeRuyter, royalGuardPref);
         // Reduce preference for regular Pikemen since Halberdiers are better
         kbUnitPickSetPreferenceFactor(upID, cUnitTypePikeman, outclassedPref);
         break;
      }
      case cCivFrench:
      {
         // Voltigeurs (Skirmishers) and Gendarmes (Cuirassiers)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeSkirmisher, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeCuirassier, royalGuardPref);
         break;
      }
      case cCivGermans:
      {
         // Needle Gunners (Skirmishers) and Czapka Uhlans (Uhlans)
         royalGuardPref = 0.74;
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeSkirmisher, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeUhlan, royalGuardPref);
         //kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercenary, royalGuardPref);
         break;
      }
      case cCivOttomans:
      {
         // Baratcu (Grenadiers) and Gardener Hussars (Hussars)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeGrenadier, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeHussar, royalGuardPref);
         break;
      }
      case cCivPortuguese:
      {
         // Guerreiros (Musketeers) and Jinetes (Dragoons)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeMusketeer, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeDragoon, royalGuardPref);
         break;
      }
      case cCivRussians:
      {
         // Pavlov Grenadiers (Grenadiers) and Tartar Loyalists (Cavalry Archers)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeGrenadier, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeCavalryArcher, royalGuardPref);
         break;
      }
      case cCivSpanish:
      {
         // Tercio Pikemen (Rodeleros) and Garrochistas (Lancers)
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeRodelero, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeLancer, royalGuardPref);
         break;
      }
      case cCivDESwedish:
      {
         // Dalkarls (Pikemen) and Hakkapelits
         kbUnitPickSetPreferenceFactor(upID, cUnitTypePikeman, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeFinnishRider, royalGuardPref);
         break;
      }
      // Native American civilizations
      case cCivXPAztec:
      {
         // Skull Knights (Jaguar Prowl Knights) and Arrow Knights
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpJaguarKnight, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpArrowKnight, royalGuardPref);
         break;
      }
      case cCivXPIroquois:
      {
         // Champion Tomahawks and Elite Forest Prowlers
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpTomahawk, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpWarRifle, royalGuardPref);
         break;
      }
      case cCivXPSioux:
      {
         // Champion Axe Riders and Elite Rifle Riders
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpAxeRider, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypexpRifleRider, royalGuardPref);
         break;
      }
      // Asian civilizations
      case cCivChinese:
      case cCivSPCChinese:
      {
         // Arquebusiers and Meteor Hammers
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypArquebusier, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypMeteorHammer, royalGuardPref);
         break;
      }
      case cCivIndians:
      case cCivSPCIndians:
      {
         // Sepoys and Sowars
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypSepoy, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypSowar, royalGuardPref);
         break;
      }
      case cCivJapanese:
      case cCivSPCJapanese:
      case cCivSPCJapaneseEnemy:
      {
         // Samurai and Ashigaru
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypKensei, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeypAshigaru, royalGuardPref);
         break;
      }
      // African civilizations
      case cCivDEEthiopians:
      {
         // Oromo Warriors and Shotel Warriors
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeOromoWarrior, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeShotelWarrior, royalGuardPref);
         break;
      }
      case cCivDEHausa:
      {
         // Fulani Archers and Raiders
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeFulaWarrior, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeRaider, royalGuardPref);
         break;
      }
      // Inca
      case cCivDEInca:
      {
         // Bolas Warriors and Jungle Bowmen
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeBolasWarrior, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeJungleBowman, royalGuardPref);
         break;
      }
      // American civilizations (DE)
      case cCivDEAmericans:
      {
         // Sharpshooters and Carbine Cavalry
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeRifleman, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeUSCavalry, royalGuardPref);
         break;
      }
      case cCivDEMexicans:
      {
         // Soldados and Chinacos
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeSoldado, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeChinaco, royalGuardPref);
         break;
      }
      case cCivDEItalians:
      {
         // Bersaglieri and Pavisiers
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeBersagliere, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedePavisier, royalGuardPref);
         break;
      }
      case cCivDEMaltese:
      {
         // Hospitaller Knights and Fire Throwers
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeHospitaller, royalGuardPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypedeHoopThrower, royalGuardPref);
         break;
      }
   }
}
//==============================================================================
// setUnitPickerSpecialUnitPreference
// Sets higher preference for civilization-specific special units that are
// unlocked through cards or other means.
// Call this in setUnitPickerPreference() after the base preferences are set.
//==============================================================================
void setUnitPickerSpecialUnitPreference(int upID = -1)
{
   if (upID < 0)
   {
      return;
   }

   // High preference value for special unlocked units
   float specialUnitPref = 0.8;

   // Tavern unit preferences - applies to all civs with a Tavern/Saloon
   int tavernCount = kbUnitCount(cMyID, cUnitTypeSaloon, cUnitStateAlive);
   if (tavernCount < 1)
   {
      tavernCount = kbUnitCount(cMyID, cUnitTypedeTavern, cUnitStateAlive);
   }

   if (tavernCount > 0 || tavernCount < 1)
   {
      int age = kbGetAge();
      
      // Base preferences for tavern units, scaling with age
      float outlawPref = -1.0;
      float mercenaryPref = 0.1;

    //   if (age >= cAge3)
    //   {
    //      outlawPref = 0.5;
    //      mercenaryPref = 0.6;
    //   }

    //   if (age >= cAge4)
    //   {
    //      outlawPref = 0.6;
    //      mercenaryPref = 0.7;
    //   }

      // Set base preferences for outlaws and mercenaries
      kbUnitPickSetPreferenceFactor(upID, cUnitTypeAbstractOutlaw, outlawPref);
      kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercenary, mercenaryPref);

      // Civilization-specific bonuses for tavern units
      if (cMyCiv == cCivGermans)
      {
         // Germans get cheaper mercenaries and should use them more
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercenary, mercenaryPref + 0.15);
         //kbUnitPickSetPreferenceFactor(upID, cUnitTypeAbstractOutlaw, outlawPref + 0.1);
      }
      else if (cMyCiv == cCivDEAmericans)
      {
         // Americans have strong outlaw synergy
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeAbstractOutlaw, outlawPref + 0.15);
      }
      else if (cMyCiv == cCivDEMexicans)
      {
         // Mexicans have outlaw bonuses
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeAbstractOutlaw, outlawPref + 0.2);
      }
   }

   // Civilization-specific special units
   switch (cMyCiv)
   {
      case cCivBritish:
      {
         // Black Watch (Highland Infantry) - unlocked via "Black Watch" card
         if (kbGetBuildLimit(cMyID, cUnitTypeMercHighlander) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercHighlander, specialUnitPref);
         }
         break;
      }
      case cCivDutch:
      {
         // Swiss Pikemen - unlocked via "Swiss Pikemen" card
         if (kbGetBuildLimit(cMyID, cUnitTypeMercSwissPikeman) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercSwissPikeman, specialUnitPref);
         }
         // Blue Guards (Stadhouder Guard) - unlocked via "Blue Guards" card
         if (kbGetBuildLimit(cMyID, cUnitTypeMusketeer) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMusketeer, specialUnitPref);
         }
         break;
      }
      case cCivFrench:
      {
         // French should avoid Native Scouts
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeNativeScout, -1.0);
         break;
      }
      case cCivGermans:
      {
         // German mercenaries unlocked via "Mercenary Camp" card (or similar)
         // Landsknecht
         if (kbGetBuildLimit(cMyID, cUnitTypeMercLandsknecht) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercLandsknecht, specialUnitPref);
         }
         // Black Rider
         if (kbGetBuildLimit(cMyID, cUnitTypeMercBlackRider) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercBlackRider, mercenaryPref + 0.15);
         }
         // Jaeger (Needle Gunner mercenary version)
         if (kbGetBuildLimit(cMyID, cUnitTypeMercJaeger) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeMercJaeger, mercenaryPref + 0.15);
         }
         // War Wagon
         if (kbGetBuildLimit(cMyID, cUnitTypeWarWagon) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypeWarWagon, specialUnitPref);
         }
         // Giant Grenadier
         if (kbGetBuildLimit(cMyID, cUnitTypedeMercGrenadier) > 0)
         {
            kbUnitPickSetPreferenceFactor(upID, cUnitTypedeMercGrenadier, mercenaryPref + 0.15);
         }
         break;
      }
   }
}
//==============================================================================
// setUnitPickerArchaicUnitFilter
// Reduces preference for archaic/outdated units in later ages when the
// civilization has access to superior alternatives.
// Call this in setUnitPickerPreference() after the base preferences are set.
//==============================================================================
void setUnitPickerArchaicUnitFilter(int upID = -1)
{
   if (upID < 0)
   {
      return;
   }

   // Only apply filtering from Age 4 onwards
   if (kbGetAge() < cAge4)
   {
      return;
   }

   // Very low preference to effectively disable these units
   float archaicUnitPref = 0.05;

   switch (cMyCiv)
   {
      case cCivBritish:
      {
         // British should avoid Pikemen and Halberdiers in Age 4+
         // They have Redcoat Musketeers and Hussars as better options
         kbUnitPickSetPreferenceFactor(upID, cUnitTypePikeman, archaicUnitPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeHalberdier, archaicUnitPref);
         break;
      }
      case cCivFrench:
      {
         // French should avoid Pikemen and Halberdiers in Age 4+
         // They have Gendarmes (Cuirassiers) and Voltigeurs (Skirmishers) as Royal Guard
         kbUnitPickSetPreferenceFactor(upID, cUnitTypePikeman, archaicUnitPref);
         kbUnitPickSetPreferenceFactor(upID, cUnitTypeHalberdier, archaicUnitPref);
         break;
      }
   }
}
//==============================================================================
// updateSecondaryBaseMilitaryTrainPlans
// Creates maintain plans for military buildings at forward/island bases
//==============================================================================
void updateSecondaryBaseMilitaryTrainPlans(int baseID = -1)
{
   if (baseID < 0)
   {
      return;
   }
   
   // Query for military buildings at this base
   vector baseLoc = kbBaseGetLocation(cMyID, baseID);
   float baseDist = kbBaseGetDistance(cMyID, baseID);
   
   int buildingQuery = createSimpleUnitQuery(cUnitTypeLogicalTypeBuildingsNotWalls, cMyID, cUnitStateAlive, baseLoc, baseDist);
   int numberFound = kbUnitQueryExecute(buildingQuery);
   
   if (numberFound == 0)
   {
      return;
   }
   
   static int trainBuildingIDs = -1;
   if (trainBuildingIDs < 0)
   {
      trainBuildingIDs = xsArrayCreateInt(8, -1, "Secondary base train buildings");
   }
   
   int buildingID = -1;
   int buildingPUID = -1;
   int planID = -1;
   int puid = -1;
   int popCount = 0;
   int numberToMaintain = 0;
   int numTrainBuildings = 0;
   float totalFactor = 0.0;
   
   // Calculate total factor from unit picker
   for (i = 0; < gNumArmyUnitTypes)
   {
      totalFactor = totalFactor + kbUnitPickGetResultFactor(gLandUnitPicker, i);
   }
   
   // For each unit type in the picker, check if we can train it at this base
   for (i = 0; < gNumArmyUnitTypes)
   {
      puid = kbUnitPickGetResult(gLandUnitPicker, i);
      if (puid < 0)
      {
         continue;
      }
      
      // Find ALL buildings at this base that can train this unit
      numTrainBuildings = 0;
      for (j = 0; < numberFound)
      {
         buildingID = kbUnitQueryGetResult(buildingQuery, j);
         buildingPUID = kbUnitGetProtoUnitID(buildingID);
         if (kbProtoUnitCanTrain(buildingPUID, puid) == true)
         {
            xsArraySetInt(trainBuildingIDs, numTrainBuildings, buildingID);
            numTrainBuildings++;
         }
      }
      
      if (numTrainBuildings == 0)
      {
         continue; // Can't train this unit type at this base
      }
      
      // Calculate number to maintain (portion of military pop for this base)
      popCount = kbGetProtoUnitPopCount(puid);
      if (popCount > 0)
      {
         // Use a fraction of military pop for forward base (e.g., 30%)
         numberToMaintain = (kbUnitPickGetResultFactor(gLandUnitPicker, i) / totalFactor) * aiGetMilitaryPop() * 0.3 / popCount;
      }
      else
      {
         numberToMaintain = (kbUnitPickGetResultFactor(gLandUnitPicker, i) / totalFactor) * aiGetMilitaryPop() * 0.3 /
                            (kbUnitCostPerResource(puid, cResourceFood) + kbUnitCostPerResource(puid, cResourceWood) +
                             kbUnitCostPerResource(puid, cResourceGold));
      }
      
      if (numberToMaintain < 1)
      {
         numberToMaintain = 1;
      }
      
      // Create the maintain plan
      planID = aiPlanCreate("Forward base " + baseID + " " + kbGetUnitTypeName(puid) + " maintain", cPlanTrain);
      aiPlanSetVariableInt(planID, cTrainPlanUnitType, 0, puid);
      aiPlanSetVariableInt(planID, cTrainPlanNumberToMaintain, 0, numberToMaintain);
      aiPlanSetBaseID(planID, baseID);
      aiPlanSetVariableVector(planID, cTrainPlanGatherPoint, 0, baseLoc);
      
      // Assign ALL buildings that can train this unit
      aiPlanSetNumberVariableValues(planID, cTrainPlanBuildingID, numTrainBuildings, true);
      for (j = 0; < numTrainBuildings)
      {
         aiPlanSetVariableInt(planID, cTrainPlanBuildingID, j, xsArrayGetInt(trainBuildingIDs, j));
      }
      
      aiPlanSetActive(planID);
      
      debugMilitary("*** Created forward base maintain plan for " + kbGetUnitTypeName(puid) + " at base " + baseID + " with " + numTrainBuildings + " buildings");
   }
}