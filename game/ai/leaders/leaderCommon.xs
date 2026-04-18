//==============================================================================
/* leaderCommon.xs

   Shared helper functions for Legendary Leaders personalities.
*/
//==============================================================================

void llResetLeaderBiases(void)
{
   btRushBoom = 0.0;
   btOffenseDefense = 0.0;
   btBiasNative = 0.0;
   btBiasTrade = 0.0;
   btBiasCav = 0.0;
   btBiasArt = 0.0;
   btBiasInf = 0.0;
   llLogEvent("LEADER", "reset leader biases to neutral defaults.");
}

void llSetBalancedPersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = 0.0;
   btOffenseDefense = 0.0;
   llLogLeaderState("balanced personality applied");
}

void llSetAggressivePersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = 0.8;
   btOffenseDefense = 0.8;
   llLogLeaderState("aggressive personality applied");
}

void llSetDefensivePersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = -0.4;
   btOffenseDefense = -0.6;
   llLogLeaderState("defensive personality applied");
}

void llSetMilitaryFocus(float infantryBias = 0.0, float cavalryBias = 0.0, float artilleryBias = 0.0)
{
   btBiasInf = infantryBias;
   btBiasCav = cavalryBias;
   btBiasArt = artilleryBias;
   llLogLeaderState("military focus updated");
}

void llEnableForwardBaseStyle(void)
{
   btOffenseDefense = 1.0;
   cvDefenseReflexRadiusActive = 75.0;
   cvDefenseReflexSearchRadius = 75.0;
   llLogLeaderState("forward-base style enabled");
}

void llEnableDeepDefenseStyle(void)
{
   btOffenseDefense = -0.5;
   cvMaxTowers = 7;
   cvDefenseReflexRadiusPassive = 40.0;
   llLogLeaderState("deep-defense style enabled");
}

void llResetBuildStyleProfile(void)
{
   gLLBuildStyle = 0;
   gLLWallLevel = 1;
   gLLEarlyWallingEnabled = false;
   gLLLateWallingEnabled = true;
   gLLHouseDistanceMultiplier = 1.0;
   gLLEconomicDistanceMultiplier = 1.0;
   gLLMilitaryDistanceMultiplier = 1.0;
   gLLTownCenterDistanceMultiplier = 1.0;
   gLLTowerLevel = 1;
   gLLFortLevel = 1;
   gLLForwardBaseTowerCount = 2;
   gLLPreferForwardFortifiedBase = false;
   cvOkToBuildWalls = true;
}

void llConfigureBuildStyleProfile(int style = 0, int wallLevel = 1, bool earlyWalls = false,
   float houseDistanceMultiplier = 1.0, float economicDistanceMultiplier = 1.0,
   float militaryDistanceMultiplier = 1.0, float townCenterDistanceMultiplier = 1.0,
   int towerLevel = 1, int fortLevel = 1, int forwardBaseTowerCount = 2,
   bool preferForwardFortifiedBase = false)
{
   gLLBuildStyle = style;
   gLLWallLevel = wallLevel;
   gLLEarlyWallingEnabled = earlyWalls;
   gLLLateWallingEnabled = (wallLevel > 0);
   gLLHouseDistanceMultiplier = houseDistanceMultiplier;
   gLLEconomicDistanceMultiplier = economicDistanceMultiplier;
   gLLMilitaryDistanceMultiplier = militaryDistanceMultiplier;
   gLLTownCenterDistanceMultiplier = townCenterDistanceMultiplier;
   gLLTowerLevel = towerLevel;
   gLLFortLevel = fortLevel;
   gLLForwardBaseTowerCount = forwardBaseTowerCount;
   gLLPreferForwardFortifiedBase = preferForwardFortifiedBase;
   cvOkToBuildWalls = (wallLevel > 0);
}

void llUseCompactFortifiedCoreStyle(int wallLevel = 3, bool earlyWalls = true)
{
   llConfigureBuildStyleProfile(cLLBuildStyleCompactFortifiedCore, wallLevel, earlyWalls, 0.75, 0.85, 0.85, 0.85, 3, 2, 2, false);
}

void llUseDistributedEconomicNetworkStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleDistributedEconomicNetwork, wallLevel, false, 1.15, 1.35, 1.0, 1.35, 1, 1, 1, false);
}

void llUseForwardOperationalLineStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleForwardOperationalLine, wallLevel, false, 1.0, 1.05, 0.95, 1.1, 1, 2, 3, true);
}

void llUseMobileFrontierScatterStyle(int wallLevel = 0)
{
   llConfigureBuildStyleProfile(cLLBuildStyleMobileFrontierScatter, wallLevel, false, 1.35, 1.45, 1.1, 1.5, 1, 0, 1, false);
}

void llUseShrineTradeNodeSpreadStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleShrineTradeNodeSpread, wallLevel, false, 1.0, 1.5, 0.95, 1.2, 1, 1, 1, false);
}

void llUseCivicMilitiaCenterStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleCivicMilitiaCenter, wallLevel, false, 0.95, 1.05, 0.95, 1.15, 2, 1, 2, false);
}

void llSetBuildStrongpointProfile(int towerLevel = 1, int fortLevel = 1, int forwardBaseTowerCount = 2,
   bool preferForwardFortifiedBase = false)
{
   gLLTowerLevel = towerLevel;
   gLLFortLevel = fortLevel;
   gLLForwardBaseTowerCount = forwardBaseTowerCount;
   gLLPreferForwardFortifiedBase = preferForwardFortifiedBase;
}

int llGetWantedFortCount(void)
{
   int age = kbGetAge();
   int buildLimit = kbGetBuildLimit(cMyID, gFortUnit);
   int fortsWanted = 0;

   if ((cvOkToBuildForts == false) || (buildLimit < 1))
   {
      return (0);
   }

   if (gLLFortLevel <= 0)
   {
      fortsWanted = 0;
   }
   else if (gLLFortLevel == 1)
   {
      fortsWanted = age >= cAge4 ? 1 : 0;
   }
   else if (gLLFortLevel == 2)
   {
      fortsWanted = age >= cAge3 ? 1 : 0;
      if ((age >= cAge4) && (buildLimit > 1) && (gLLPreferForwardFortifiedBase == true))
      {
         fortsWanted = 2;
      }
   }
   else
   {
      fortsWanted = age >= cAge3 ? 1 : 0;
      if ((age >= cAge4) && (buildLimit > 1))
      {
         fortsWanted = 2;
      }
      if ((age >= cvMaxAge) && (buildLimit > fortsWanted))
      {
         fortsWanted = buildLimit;
      }
   }

   if (fortsWanted > buildLimit)
   {
      fortsWanted = buildLimit;
   }

   return (fortsWanted);
}

string llGetBuildStyleName(int style = 0)
{
   if (style == cLLBuildStyleCompactFortifiedCore)
   {
      return ("Compact Fortified Core");
   }
   if (style == cLLBuildStyleDistributedEconomicNetwork)
   {
      return ("Distributed Economic Network");
   }
   if (style == cLLBuildStyleForwardOperationalLine)
   {
      return ("Forward Operational Line");
   }
   if (style == cLLBuildStyleMobileFrontierScatter)
   {
      return ("Mobile Frontier Scatter");
   }
   if (style == cLLBuildStyleShrineTradeNodeSpread)
   {
      return ("Shrine or Trade Node Spread");
   }
   if (style == cLLBuildStyleCivicMilitiaCenter)
   {
      return ("Civic Militia Center");
   }
   return ("Unassigned");
}

void llApplyBuildStyleForActiveCiv(void)
{
   string rvltName = kbGetCivName(cMyCiv);

   llResetBuildStyleProfile();

   if (cMyCiv == cCivXPAztec)
   {
      llUseCompactFortifiedCoreStyle(0, false);
   }
   else if (cMyCiv == cCivBritish)
   {
      llUseDistributedEconomicNetworkStyle(2);
   }
   else if (cMyCiv == cCivChinese)
   {
      llUseCompactFortifiedCoreStyle(3, true);
   }
   else if (cMyCiv == cCivDutch)
   {
      llUseCompactFortifiedCoreStyle(2, false);
   }
   else if (cMyCiv == cCivDEEthiopians)
   {
      llUseCompactFortifiedCoreStyle(2, false);
   }
   else if (cMyCiv == cCivFrench)
   {
      llUseCompactFortifiedCoreStyle(2, false);
   }
   else if (cMyCiv == cCivGermans)
   {
      llUseDistributedEconomicNetworkStyle(1);
      gLLMilitaryDistanceMultiplier = 0.9;
      llSetBuildStrongpointProfile(1, 1, 2, false);
   }
   else if (cMyCiv == cCivXPIroquois)
   {
      llUseCivicMilitiaCenterStyle(1);
   }
   else if (cMyCiv == cCivDEHausa)
   {
      llUseDistributedEconomicNetworkStyle(2);
   }
   else if (cMyCiv == cCivDEInca)
   {
      llUseCompactFortifiedCoreStyle(3, true);
   }
   else if (cMyCiv == cCivIndians)
   {
      llUseCivicMilitiaCenterStyle(2);
   }
   else if (cMyCiv == cCivDEItalians)
   {
      llUseCivicMilitiaCenterStyle(2);
   }
   else if (cMyCiv == cCivJapanese)
   {
      llUseShrineTradeNodeSpreadStyle(3);
   }
   else if (cMyCiv == cCivXPSioux)
   {
      llUseMobileFrontierScatterStyle(0);
   }
   else if (cMyCiv == cCivDEMaltese)
   {
      llUseCompactFortifiedCoreStyle(4, true);
   }
   else if (cMyCiv == cCivDEMexicans)
   {
      llUseCivicMilitiaCenterStyle(1);
      gLLEconomicDistanceMultiplier = 1.15;
      llSetBuildStrongpointProfile(1, 1, 2, false);
   }
   else if (cMyCiv == cCivOttomans)
   {
      llUseCompactFortifiedCoreStyle(2, false);
      gLLWallLevel = 1;
      gLLEconomicDistanceMultiplier = 1.1;
      gLLMilitaryDistanceMultiplier = 1.05;
      llSetBuildStrongpointProfile(1, 1, 2, false);
   }
   else if (cMyCiv == cCivPortuguese)
   {
      llUseDistributedEconomicNetworkStyle(2);
   }
   else if (cMyCiv == cCivRussians)
   {
      llUseForwardOperationalLineStyle(0);
   }
   else if (cMyCiv == cCivSpanish)
   {
      llUseForwardOperationalLineStyle(2);
   }
   else if (cMyCiv == cCivDESwedish)
   {
      llUseShrineTradeNodeSpreadStyle(1);
   }
   else if (cMyCiv == cCivDEAmericans)
   {
      llUseCivicMilitiaCenterStyle(1);
   }
   else if (rvltName == "RvltModAmericans")
   {
      llUseCivicMilitiaCenterStyle(0);
   }
   else if (rvltName == "RvltModArgentines")
   {
      llUseForwardOperationalLineStyle(0);
   }
   else if (rvltName == "RvltModBajaCalifornians")
   {
      llUseMobileFrontierScatterStyle(0);
   }
   else if (rvltName == "RvltModBarbary")
   {
      llUseForwardOperationalLineStyle(2);
      gLLEconomicDistanceMultiplier = 1.2;
      llSetBuildStrongpointProfile(2, 2, 2, true);
   }
   else if (rvltName == "RvltModBrazil")
   {
      llUseDistributedEconomicNetworkStyle(2);
   }
   else if (rvltName == "RvltModCalifornians")
   {
      llUseCivicMilitiaCenterStyle(1);
      gLLHouseDistanceMultiplier = 1.15;
      gLLEconomicDistanceMultiplier = 1.3;
      llSetBuildStrongpointProfile(2, 1, 1, false);
   }
   else if (rvltName == "RvltModCanadians")
   {
      llUseCompactFortifiedCoreStyle(2, false);
   }
   else if (rvltName == "RvltModCentralAmericans")
   {
      llUseDistributedEconomicNetworkStyle(1);
   }
   else if (rvltName == "RvltModChileans")
   {
      llUseCivicMilitiaCenterStyle(2);
   }
   else if (rvltName == "RvltModColumbians")
   {
      llUseForwardOperationalLineStyle(0);
   }
   else if (rvltName == "RvltModEgyptians")
   {
      llUseCompactFortifiedCoreStyle(3, false);
   }
   else if (rvltName == "RvltModFinnish")
   {
      llUseCompactFortifiedCoreStyle(3, true);
   }
   else if (rvltName == "RvltModFrenchCanadians")
   {
      llUseCivicMilitiaCenterStyle(1);
   }
   else if (rvltName == "RvltModHaitians")
   {
      llUseMobileFrontierScatterStyle(0);
   }
   else if (rvltName == "RvltModHungarians")
   {
      llUseForwardOperationalLineStyle(1);
   }
   else if (rvltName == "RvltModIndonesians")
   {
      llUseDistributedEconomicNetworkStyle(1);
   }
   else if (rvltName == "RvltModMayans")
   {
      llUseCivicMilitiaCenterStyle(1);
   }
   else if (rvltName == "RvltModMexicans")
   {
      llUseForwardOperationalLineStyle(0);
   }
   else if (rvltName == "RvltModRevolutionaryFrance")
   {
      llUseCivicMilitiaCenterStyle(0);
   }
   else if (rvltName == "RvltModNapoleonicFrance")
   {
      llUseForwardOperationalLineStyle(1);
   }
   else if (rvltName == "RvltModPeruvians")
   {
      llUseCompactFortifiedCoreStyle(3, false);
   }
   else if (rvltName == "RvltModRioGrande")
   {
      llUseMobileFrontierScatterStyle(0);
   }
   else if (rvltName == "RvltModRomanians")
   {
      llUseCivicMilitiaCenterStyle(2);
   }
   else if (rvltName == "RvltModSouthAfricans")
   {
      llUseMobileFrontierScatterStyle(0);
      llSetBuildStrongpointProfile(2, 1, 2, true);
   }
   else if (rvltName == "RvltModTexians")
   {
      llUseCivicMilitiaCenterStyle(1);
   }
   else if (rvltName == "RvltModYucatan")
   {
      llUseCivicMilitiaCenterStyle(2);
   }

   llLogEvent("BUILDSTYLE", kbGetCivName(cMyCiv) + " -> " + llGetBuildStyleName(gLLBuildStyle) +
      " walls=" + gLLWallLevel + " earlyWalls=" + gLLEarlyWallingEnabled +
      " house=" + gLLHouseDistanceMultiplier + " eco=" + gLLEconomicDistanceMultiplier +
      " mil=" + gLLMilitaryDistanceMultiplier + " tc=" + gLLTownCenterDistanceMultiplier +
      " towerLevel=" + gLLTowerLevel + " fortLevel=" + gLLFortLevel +
      " forwardBaseTowers=" + gLLForwardBaseTowerCount + " forwardFortified=" + gLLPreferForwardFortifiedBase);
}
