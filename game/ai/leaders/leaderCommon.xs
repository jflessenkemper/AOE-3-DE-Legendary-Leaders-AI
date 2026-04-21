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
   gLLEarlyWallingEnabled = true;
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
   gLLEarlyWallingEnabled = true;
   gLLLateWallingEnabled = (wallLevel > 0);
   gLLHouseDistanceMultiplier = houseDistanceMultiplier;
   gLLEconomicDistanceMultiplier = economicDistanceMultiplier;
   gLLMilitaryDistanceMultiplier = militaryDistanceMultiplier;
   gLLTownCenterDistanceMultiplier = townCenterDistanceMultiplier;
   gLLTowerLevel = towerLevel;
   gLLFortLevel = fortLevel;
   gLLForwardBaseTowerCount = forwardBaseTowerCount;
   gLLPreferForwardFortifiedBase = preferForwardFortifiedBase;
   cvOkToBuildWalls = true;
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

// ── Bespoke historical archetypes ────────────────────────────────────────
// Steppe Cavalry Wedge — Lakota / Hungarian hussar doctrine: dispersed mobile
// camps, no perimeter, fast raiding cavalry from forward muster points.
void llUseSteppeCavalryWedgeStyle(int wallLevel = 0)
{
   llConfigureBuildStyleProfile(cLLBuildStyleSteppeCavalryWedge, wallLevel, false,
      1.40, 1.50, 1.15, 1.55, 1, 0, 1, false);
}

// Naval Mercantile Compound — Dutch / British / Portuguese commercial empire:
// coastal bank-and-dock spine, deep harbour batteries, money before muskets.
void llUseNavalMercantileCompoundStyle(int wallLevel = 2)
{
   llConfigureBuildStyleProfile(cLLBuildStyleNavalMercantileCompound, wallLevel, false,
      1.10, 1.30, 1.00, 1.25, 2, 2, 1, false);
}

// Siege Train Concentration — Ottoman / Prussian / Swedish cannon doctrine:
// clustered military quarter, grand battery park, forward fortified line.
void llUseSiegeTrainConcentrationStyle(int wallLevel = 2)
{
   llConfigureBuildStyleProfile(cLLBuildStyleSiegeTrainConcentration, wallLevel, true,
      0.90, 1.00, 0.85, 0.95, 2, 2, 3, true);
}

// Jungle Guerrilla Network — Maya / Haitian / Aztec scout-and-ambush doctrine:
// scattered war huts hidden in terrain, no perimeter wall, fluid response.
void llUseJungleGuerrillaNetworkStyle(int wallLevel = 0)
{
   llConfigureBuildStyleProfile(cLLBuildStyleJungleGuerrillaNetwork, wallLevel, false,
      1.10, 1.30, 0.95, 1.30, 1, 0, 2, true);
}

// Highland Citadel — Maltese / Egyptian Mameluk / mountain fortress: tight
// core, multi-ring high walls, maximum towers and forts.
void llUseHighlandCitadelStyle(int wallLevel = 5)
{
   llConfigureBuildStyleProfile(cLLBuildStyleHighlandCitadel, wallLevel, true,
      0.65, 0.90, 0.80, 0.70, 4, 3, 2, false);
}

// Cossack Voisko — Russian / Ukrainian host muster: massed barracks and
// Blockhouse net, forward host camp, swarm production.
void llUseCossackVoiskoStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleCossackVoisko, wallLevel, false,
      0.90, 1.00, 0.80, 0.95, 2, 2, 3, true);
}

// Republican Levee — French Revolution / American / Mexican citizen-army:
// civic spine of militia centers, town-center decentralised, militia first.
void llUseRepublicanLeveeStyle(int wallLevel = 1)
{
   llConfigureBuildStyleProfile(cLLBuildStyleRepublicanLevee, wallLevel, false,
      0.95, 1.05, 0.90, 1.10, 2, 1, 3, true);
}

// Andean Terrace Fortress — Inca / Peruvian / Chilean highland doctrine:
// tight core on terraces, tower-heavy ring, dual fort backbone.
void llUseAndeanTerraceFortressStyle(int wallLevel = 3)
{
   llConfigureBuildStyleProfile(cLLBuildStyleAndeanTerraceFortress, wallLevel, true,
      0.80, 0.95, 0.90, 0.90, 3, 2, 2, false);
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
   if (style == cLLBuildStyleSteppeCavalryWedge)
   {
      return ("Steppe Cavalry Wedge");
   }
   if (style == cLLBuildStyleNavalMercantileCompound)
   {
      return ("Naval Mercantile Compound");
   }
   if (style == cLLBuildStyleSiegeTrainConcentration)
   {
      return ("Siege Train Concentration");
   }
   if (style == cLLBuildStyleJungleGuerrillaNetwork)
   {
      return ("Jungle Guerrilla Network");
   }
   if (style == cLLBuildStyleHighlandCitadel)
   {
      return ("Highland Citadel");
   }
   if (style == cLLBuildStyleCossackVoisko)
   {
      return ("Cossack Voisko");
   }
   if (style == cLLBuildStyleRepublicanLevee)
   {
      return ("Republican Levee");
   }
   if (style == cLLBuildStyleAndeanTerraceFortress)
   {
      return ("Andean Terrace Fortress");
   }
   return ("Unassigned");
}

void llApplyBuildStyleForActiveCiv(void)
{
   string rvltName = kbGetCivName(cMyCiv);

   llResetBuildStyleProfile();

   // ── STANDARD NATIONS (22) — bespoke per-civ profiles ─────────────────
   if (cMyCiv == cCivXPAztec)
   {
      // Montezuma — Flower War tribute aggression. Hidden war huts, no perimeter.
      llUseJungleGuerrillaNetworkStyle(0);
      gLLHouseDistanceMultiplier = 0.85;
   }
   else if (cMyCiv == cCivBritish)
   {
      // Henry VIII — Royal Navy and the Manor economy. Coastal compound.
      llUseNavalMercantileCompoundStyle(2);
      gLLEconomicDistanceMultiplier = 1.30;
   }
   else if (cMyCiv == cCivChinese)
   {
      // Kangxi — High-walled Forbidden City. Compact, multi-ring fortress.
      llUseCompactFortifiedCoreStyle(4, true);
      gLLHouseDistanceMultiplier = 0.70;
      llSetBuildStrongpointProfile(3, 2, 2, false);
   }
   else if (cMyCiv == cCivDutch)
   {
      // Maurice of Nassau — Dutch trade republic. Bank-and-dock spine.
      llUseNavalMercantileCompoundStyle(2);
      gLLEconomicDistanceMultiplier = 1.40;
      gLLHouseDistanceMultiplier = 1.05;
   }
   else if (cMyCiv == cCivDEEthiopians)
   {
      // Menelik II — Highland citadel of Entoto / Magdala.
      llUseHighlandCitadelStyle(3);
      gLLHouseDistanceMultiplier = 0.80;
      llSetBuildStrongpointProfile(3, 2, 2, false);
   }
   else if (cMyCiv == cCivFrench)
   {
      // Napoleon — Grand Armée operational manoeuvre.
      llUseForwardOperationalLineStyle(2);
      gLLMilitaryDistanceMultiplier = 0.85;
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (cMyCiv == cCivGermans)
   {
      // Frederick the Great — Prussian siege train and oblique order.
      llUseSiegeTrainConcentrationStyle(2);
      gLLMilitaryDistanceMultiplier = 0.85;
      llSetBuildStrongpointProfile(2, 2, 2, true);
   }
   else if (cMyCiv == cCivXPIroquois)
   {
      // Hiawatha — Confederation longhouse and trade.
      llUseShrineTradeNodeSpreadStyle(1);
      gLLEconomicDistanceMultiplier = 1.20;
   }
   else if (cMyCiv == cCivDEHausa)
   {
      // Usman dan Fodio — Sokoto caliphate trade-and-cavalry.
      llUseDistributedEconomicNetworkStyle(2);
      gLLEconomicDistanceMultiplier = 1.30;
   }
   else if (cMyCiv == cCivDEInca)
   {
      // Pachacuti — Sacsayhuamán terraced fortress.
      llUseAndeanTerraceFortressStyle(4);
      gLLHouseDistanceMultiplier = 0.75;
      llSetBuildStrongpointProfile(3, 3, 2, false);
   }
   else if (cMyCiv == cCivIndians)
   {
      // Shivaji — Maratha hill-fort guerrilla and Sacred Field economy.
      llUseShrineTradeNodeSpreadStyle(2);
      gLLEconomicDistanceMultiplier = 1.10;
      llSetBuildStrongpointProfile(2, 1, 2, false);
   }
   else if (cMyCiv == cCivDEItalians)
   {
      // Garibaldi — Risorgimento volunteer Redshirts.
      llUseRepublicanLeveeStyle(2);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (cMyCiv == cCivJapanese)
   {
      // Tokugawa — Sankin-kōtai shrine network and castle towns.
      llUseShrineTradeNodeSpreadStyle(3);
      gLLEconomicDistanceMultiplier = 1.25;
      llSetBuildStrongpointProfile(2, 2, 1, false);
   }
   else if (cMyCiv == cCivXPSioux)
   {
      // Crazy Horse — Lakota wedge of mounted warriors.
      llUseSteppeCavalryWedgeStyle(0);
   }
   else if (cMyCiv == cCivDEMaltese)
   {
      // Jean de Valette — Hospitaller fortress of Birgu and Senglea.
      llUseHighlandCitadelStyle(5);
      llSetBuildStrongpointProfile(4, 3, 2, false);
   }
   else if (cMyCiv == cCivDEMexicans)
   {
      // Hidalgo (standard) — Insurgent town-civic militia.
      llUseRepublicanLeveeStyle(1);
      gLLEconomicDistanceMultiplier = 1.15;
      llSetBuildStrongpointProfile(2, 1, 2, false);
   }
   else if (cMyCiv == cCivOttomans)
   {
      // Suleiman the Magnificent — Ottoman siege at Vienna and Rhodes.
      llUseSiegeTrainConcentrationStyle(3);
      gLLEconomicDistanceMultiplier = 1.05;
      llSetBuildStrongpointProfile(2, 2, 2, true);
   }
   else if (cMyCiv == cCivPortuguese)
   {
      // Henry the Navigator — Carrack-and-feitoria mercantile network.
      llUseNavalMercantileCompoundStyle(2);
      gLLEconomicDistanceMultiplier = 1.30;
   }
   else if (cMyCiv == cCivRussians)
   {
      // Catherine the Great — Cossack host muster and Blockhouse net.
      llUseCossackVoiskoStyle(1);
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (cMyCiv == cCivSpanish)
   {
      // Isabella — Reconquista forward operational line.
      llUseForwardOperationalLineStyle(2);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (cMyCiv == cCivDESwedish)
   {
      // Gustavus Adolphus — Lion of the North, mobile field artillery.
      llUseSiegeTrainConcentrationStyle(1);
      gLLMilitaryDistanceMultiplier = 0.85;
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (cMyCiv == cCivDEAmericans)
   {
      // Washington (standard) — Continental Army republican compound.
      llUseRepublicanLeveeStyle(1);
      gLLTownCenterDistanceMultiplier = 1.10;
   }

   // ── REVOLUTION NATIONS (26) — bespoke per-nation profiles ────────────
   else if (rvltName == "RvltModAmericans")
   {
      // Jefferson — Continental Congress republican civic spine.
      llUseRepublicanLeveeStyle(0);
      gLLEconomicDistanceMultiplier = 1.05;
      gLLTownCenterDistanceMultiplier = 1.15;
   }
   else if (rvltName == "RvltModArgentines")
   {
      // San Martin — Army of the Andes liberation column.
      llUseForwardOperationalLineStyle(0);
      gLLMilitaryDistanceMultiplier = 0.85;
      llSetBuildStrongpointProfile(1, 2, 3, true);
   }
   else if (rvltName == "RvltModBajaCalifornians")
   {
      // Baja Californians — Mission scatter on a long peninsula.
      llUseMobileFrontierScatterStyle(0);
      gLLHouseDistanceMultiplier = 1.40;
      gLLEconomicDistanceMultiplier = 1.50;
   }
   else if (rvltName == "RvltModBarbary")
   {
      // Barbary — Corsair coastal compound, fortified harbour.
      llUseNavalMercantileCompoundStyle(2);
      gLLEconomicDistanceMultiplier = 1.20;
      llSetBuildStrongpointProfile(2, 2, 2, true);
   }
   else if (rvltName == "RvltModBrazil")
   {
      // Brazil — Empire of Pedro II, sugar economy distributed network.
      llUseDistributedEconomicNetworkStyle(2);
      gLLEconomicDistanceMultiplier = 1.35;
   }
   else if (rvltName == "RvltModCalifornians")
   {
      // Californians — Gold Rush economic boom, sprawling sites.
      llUseDistributedEconomicNetworkStyle(1);
      gLLHouseDistanceMultiplier = 1.15;
      gLLEconomicDistanceMultiplier = 1.40;
      llSetBuildStrongpointProfile(2, 1, 1, false);
   }
   else if (rvltName == "RvltModCanadians")
   {
      // Canadians — Loyalist garrison along the St Lawrence.
      llUseCompactFortifiedCoreStyle(2, false);
      gLLEconomicDistanceMultiplier = 0.95;
      llSetBuildStrongpointProfile(2, 2, 2, false);
   }
   else if (rvltName == "RvltModCentralAmericans")
   {
      // Morazán — Federal Republic of Central America trade league.
      llUseDistributedEconomicNetworkStyle(1);
      gLLEconomicDistanceMultiplier = 1.25;
   }
   else if (rvltName == "RvltModChileans")
   {
      // O'Higgins — Andean column on the Pacific coast.
      llUseAndeanTerraceFortressStyle(2);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 2, 2, false);
   }
   else if (rvltName == "RvltModColumbians")
   {
      // Bolívar — Gran Colombia liberation drive.
      llUseForwardOperationalLineStyle(0);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(1, 1, 3, true);
   }
   else if (rvltName == "RvltModEgyptians")
   {
      // Muhammad Ali — Mameluke citadel of Cairo.
      llUseHighlandCitadelStyle(4);
      gLLHouseDistanceMultiplier = 0.75;
      llSetBuildStrongpointProfile(3, 3, 2, false);
   }
   else if (rvltName == "RvltModFinnish")
   {
      // Finns — Mannerheim Line winter fortress.
      llUseCompactFortifiedCoreStyle(3, true);
      gLLHouseDistanceMultiplier = 0.80;
      llSetBuildStrongpointProfile(3, 2, 2, false);
   }
   else if (rvltName == "RvltModFrenchCanadians")
   {
      // French Canadians — Patriote militia of Lower Canada.
      llUseCivicMilitiaCenterStyle(1);
      gLLEconomicDistanceMultiplier = 1.05;
      llSetBuildStrongpointProfile(2, 1, 2, false);
   }
   else if (rvltName == "RvltModHaitians")
   {
      // Toussaint / Dessalines — Haitian Revolution jungle ambush.
      llUseJungleGuerrillaNetworkStyle(0);
      gLLEconomicDistanceMultiplier = 1.40;
      gLLTownCenterDistanceMultiplier = 1.40;
   }
   else if (rvltName == "RvltModHungarians")
   {
      // Kossuth — Hungarian hussar wedge of the 1848 Honvéd.
      llUseSteppeCavalryWedgeStyle(1);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 1, 3, true);
   }
   else if (rvltName == "RvltModIndonesians")
   {
      // Diponegoro — Java War shrine and pesantren network.
      llUseShrineTradeNodeSpreadStyle(1);
      gLLEconomicDistanceMultiplier = 1.40;
   }
   else if (rvltName == "RvltModMayans")
   {
      // Caste War — Maya jungle guerrilla, Yucatán bush huts.
      llUseJungleGuerrillaNetworkStyle(1);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 1, 2, true);
   }
   else if (rvltName == "RvltModMexicans")
   {
      // Hidalgo (revolution) — Grito de Dolores citizen army.
      llUseRepublicanLeveeStyle(0);
      gLLEconomicDistanceMultiplier = 1.10;
      llSetBuildStrongpointProfile(1, 2, 3, true);
   }
   else if (rvltName == "RvltModRevolutionaryFrance")
   {
      // Revolutionary France — Levée en masse of the Year II.
      llUseRepublicanLeveeStyle(0);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(1, 1, 3, true);
   }
   else if (rvltName == "RvltModNapoleonicFrance")
   {
      // Napoleon — Grande Armée operational manoeuvre.
      llUseForwardOperationalLineStyle(1);
      gLLMilitaryDistanceMultiplier = 0.85;
      llSetBuildStrongpointProfile(2, 2, 3, true);
   }
   else if (rvltName == "RvltModPeruvians")
   {
      // Túpac Amaru — Andean terrace fortress.
      llUseAndeanTerraceFortressStyle(3);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(3, 2, 2, false);
   }
   else if (rvltName == "RvltModRioGrande")
   {
      // Rio Grande — Republic-on-the-frontier ranching scatter.
      llUseMobileFrontierScatterStyle(0);
      gLLHouseDistanceMultiplier = 1.35;
      gLLTownCenterDistanceMultiplier = 1.50;
      llSetBuildStrongpointProfile(1, 0, 2, false);
   }
   else if (rvltName == "RvltModRomanians")
   {
      // Cuza — Romanian unification civic militia.
      llUseCivicMilitiaCenterStyle(2);
      gLLEconomicDistanceMultiplier = 1.10;
      llSetBuildStrongpointProfile(2, 1, 2, false);
   }
   else if (rvltName == "RvltModSouthAfricans")
   {
      // Boer Voortrekker — Laager-and-port colonial compound.
      llUseNavalMercantileCompoundStyle(1);
      gLLEconomicDistanceMultiplier = 1.25;
      llSetBuildStrongpointProfile(2, 1, 2, true);
   }
   else if (rvltName == "RvltModTexians")
   {
      // Houston — Texan revolution forward line at San Jacinto.
      llUseForwardOperationalLineStyle(0);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 1, 3, true);
   }
   else if (rvltName == "RvltModYucatan")
   {
      // Yucatán — Caste War jungle guerrilla.
      llUseJungleGuerrillaNetworkStyle(1);
      gLLMilitaryDistanceMultiplier = 0.90;
      llSetBuildStrongpointProfile(2, 1, 2, true);
   }

   llLogEvent("BUILDSTYLE", kbGetCivName(cMyCiv) + " -> " + llGetBuildStyleName(gLLBuildStyle) +
      " walls=" + gLLWallLevel + " earlyWalls=" + gLLEarlyWallingEnabled +
      " house=" + gLLHouseDistanceMultiplier + " eco=" + gLLEconomicDistanceMultiplier +
      " mil=" + gLLMilitaryDistanceMultiplier + " tc=" + gLLTownCenterDistanceMultiplier +
      " towerLevel=" + gLLTowerLevel + " fortLevel=" + gLLFortLevel +
      " forwardBaseTowers=" + gLLForwardBaseTowerCount + " forwardFortified=" + gLLPreferForwardFortifiedBase);
}
