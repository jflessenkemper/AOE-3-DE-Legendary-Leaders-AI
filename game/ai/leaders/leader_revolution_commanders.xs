//==============================================================================
/* leader_revolution_commanders.xs

   Commander personalities for the playable revolution roster that does not yet
   have bespoke per-civ loader scripts.
*/
//==============================================================================

bool gLegendaryRevolutionCommanderEnabled = false;
int gLegendaryRevolutionDoctrine = 0;

void initLegendaryRevolutionCommander(void)
{
   if (civIsRevolution() == false)
   {
      return;
   }

   string rvltName = kbGetCivName(cMyCiv);

   if ((rvltName == "RvltModNapoleonicFrance") || (rvltName == "RvltModAmericans") ||
       (rvltName == "RvltModMexicans"))
   {
      return;
   }

   llSetBalancedPersonality();
   gLegendaryRevolutionDoctrine = 0;

   if (rvltName == "RvltModCanadians")
   {
      aiEcho("Legendary Leaders: activating Isaac Brock personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.7, -0.2, 0.3);
      btBiasTrade = 0.2;
      cvOkToBuildForts = true;
      cvMaxTowers = 8;
      gLegendaryRevolutionDoctrine = 1;
   }
   else if (rvltName == "RvltModFrenchCanadians")
   {
      aiEcho("Legendary Leaders: activating Louis-Joseph Papineau personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.6, -0.2, 0.0);
      btBiasTrade = 0.3;
      btBiasNative = 0.2;
      cvMaxTowers = 7;
      gLegendaryRevolutionDoctrine = 5;
   }
   else if (rvltName == "RvltModBrazil")
   {
      aiEcho("Legendary Leaders: activating Pedro I personality.");
      llSetBalancedPersonality();
      llSetMilitaryFocus(0.3, 0.2, 0.3);
      btBiasTrade = 0.2;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 4;
   }
   else if (rvltName == "RvltModArgentines")
   {
      aiEcho("Legendary Leaders: activating Jose de San Martin personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.2, 0.7, 0.1);
      llEnableForwardBaseStyle();
      btBiasTrade = -0.2;
      gLegendaryRevolutionDoctrine = 2;
   }
   else if (rvltName == "RvltModChileans")
   {
      aiEcho("Legendary Leaders: activating Bernardo O'Higgins personality.");
      llSetBalancedPersonality();
      llSetMilitaryFocus(0.5, 0.1, 0.2);
      btBiasTrade = 0.2;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 6;
   }
   else if (rvltName == "RvltModPeruvians")
   {
      aiEcho("Legendary Leaders: activating Andres de Santa Cruz personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.5, 0.0, 0.2);
      btBiasNative = 0.5;
      btBiasTrade = 0.2;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModColumbians")
   {
      aiEcho("Legendary Leaders: activating Simon Bolivar personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.3, 0.4, 0.3);
      llEnableForwardBaseStyle();
      btBiasTrade = 0.1;
      gLegendaryRevolutionDoctrine = 4;
   }
   else if (rvltName == "RvltModHaitians")
   {
      aiEcho("Legendary Leaders: activating Toussaint Louverture personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.7, -0.2, 0.0);
      btBiasNative = 0.6;
      btBiasTrade = 0.2;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModIndonesians")
   {
      aiEcho("Legendary Leaders: activating Diponegoro personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.6, -0.2, 0.1);
      btBiasNative = 0.6;
      btBiasTrade = 0.3;
      cvMaxTowers = 7;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModSouthAfricans")
   {
      aiEcho("Legendary Leaders: activating Paul Kruger personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.2, 0.5, 0.1);
      btBiasTrade = 0.4;
      cvOkToBuildForts = true;
      cvMaxTowers = 7;
      gLegendaryRevolutionDoctrine = 7;
   }
   else if (rvltName == "RvltModFinnish")
   {
      aiEcho("Legendary Leaders: activating Carl Gustaf Mannerheim personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.6, 0.0, 0.3);
      btBiasTrade = -0.1;
      cvOkToBuildForts = true;
      cvMaxTowers = 8;
      gLegendaryRevolutionDoctrine = 1;
   }
   else if (rvltName == "RvltModHungarians")
   {
      aiEcho("Legendary Leaders: activating Lajos Kossuth personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.4, 0.4, 0.1);
      btBiasTrade = 0.1;
      llEnableForwardBaseStyle();
      gLegendaryRevolutionDoctrine = 2;
   }
   else if (rvltName == "RvltModRomanians")
   {
      aiEcho("Legendary Leaders: activating Alexandru Ioan Cuza personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.4, 0.2, 0.3);
      btBiasTrade = 0.2;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 6;
   }
   else if (rvltName == "RvltModBarbary")
   {
      aiEcho("Legendary Leaders: activating Hayreddin Barbarossa personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.2, 0.5, 0.0);
      btBiasTrade = 0.4;
      btBiasNative = 0.3;
      gLegendaryRevolutionDoctrine = 2;
   }
   else if (rvltName == "RvltModEgyptians")
   {
      aiEcho("Legendary Leaders: activating Muhammad Ali Pasha personality.");
      llSetBalancedPersonality();
      llSetMilitaryFocus(0.4, 0.0, 0.4);
      btBiasTrade = 0.3;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 4;
   }
   else if (rvltName == "RvltModCentralAmericans")
   {
      aiEcho("Legendary Leaders: activating Francisco Morazan personality.");
      llSetBalancedPersonality();
      llSetMilitaryFocus(0.5, 0.1, 0.1);
      btBiasNative = 0.5;
      btBiasTrade = 0.3;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModBajaCalifornians")
   {
      aiEcho("Legendary Leaders: activating Juan Bautista Alvarado personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.2, 0.6, 0.0);
      btBiasTrade = 0.1;
      gLegendaryRevolutionDoctrine = 2;
   }
   else if (rvltName == "RvltModYucatan")
   {
      aiEcho("Legendary Leaders: activating Felipe Carrillo Puerto personality.");
      llSetBalancedPersonality();
      llSetMilitaryFocus(0.6, -0.2, 0.0);
      btBiasNative = 0.7;
      btBiasTrade = 0.2;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModRioGrande")
   {
      aiEcho("Legendary Leaders: activating Antonio Canales Rosillo personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.3, 0.6, 0.0);
      llEnableForwardBaseStyle();
      btBiasTrade = -0.1;
      gLegendaryRevolutionDoctrine = 2;
   }
   else if (rvltName == "RvltModMayans")
   {
      aiEcho("Legendary Leaders: activating Jacinto Canek personality.");
      llSetAggressivePersonality();
      llSetMilitaryFocus(0.7, -0.3, 0.0);
      btBiasNative = 0.8;
      btBiasTrade = 0.1;
      gLegendaryRevolutionDoctrine = 3;
   }
   else if (rvltName == "RvltModCalifornians")
   {
      aiEcho("Legendary Leaders: activating Mariano Guadalupe Vallejo personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.2, 0.4, 0.1);
      btBiasTrade = 0.5;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 7;
   }
   else if (rvltName == "RvltModTexians")
   {
      aiEcho("Legendary Leaders: activating Sam Houston personality.");
      llSetDefensivePersonality();
      llSetMilitaryFocus(0.5, 0.3, 0.0);
      btBiasTrade = 0.1;
      cvOkToBuildForts = true;
      gLegendaryRevolutionDoctrine = 6;
   }
   else
   {
      return;
   }

   if (gLegendaryRevolutionDoctrine == 1)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.24, 58.0);
   }
   else if (gLegendaryRevolutionDoctrine == 2)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineExecution, 0.38, 72.0);
   }
   else if (gLegendaryRevolutionDoctrine == 3)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineIntegration, 0.34, 66.0);
   }
   else if (gLegendaryRevolutionDoctrine == 4)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineForcedLabor, 0.30, 68.0);
   }
   else if (gLegendaryRevolutionDoctrine == 5)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.20, 54.0);
   }
   else if (gLegendaryRevolutionDoctrine == 6)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.22, 60.0);
   }
   else if (gLegendaryRevolutionDoctrine == 7)
   {
      llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.24, 58.0);
   }

   llEnablePrisonerSystem();
   debugLegendaryLeaders("revolution commander initialized for " + rvltName + " with doctrine bucket " + gLegendaryRevolutionDoctrine);
   gLegendaryRevolutionCommanderEnabled = true;
}

rule legendaryRevolutionCommanderDoctrine
inactive
minInterval 75
{
   if (gLegendaryRevolutionCommanderEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() < cAge3)
   {
      return;
   }

   if (gLegendaryRevolutionDoctrine == 1)
   {
      btBiasInf = 0.8;
      btBiasArt = 0.4;
      cvMaxTowers = 8;
   }
   else if (gLegendaryRevolutionDoctrine == 2)
   {
      btBiasCav = 0.7;
      btBiasInf = 0.3;
      btOffenseDefense = 0.9;
   }
   else if (gLegendaryRevolutionDoctrine == 3)
   {
      btBiasInf = 0.6;
      btBiasNative = 0.8;
      btBiasTrade = 0.3;
   }
   else if (gLegendaryRevolutionDoctrine == 4)
   {
      btBiasArt = 0.6;
      btBiasInf = 0.4;
      cvOkToBuildForts = true;
   }
   else if (gLegendaryRevolutionDoctrine == 5)
   {
      btBiasInf = 0.7;
      btBiasTrade = 0.4;
      btOffenseDefense = -0.4;
   }
   else if (gLegendaryRevolutionDoctrine == 6)
   {
      btBiasInf = 0.6;
      btBiasCav = 0.3;
      cvOkToBuildForts = true;
   }
   else if (gLegendaryRevolutionDoctrine == 7)
   {
      btBiasTrade = 0.6;
      btBiasCav = 0.4;
      btOffenseDefense = -0.2;
   }
}

void enableLegendaryRevolutionCommanderRules(void)
{
   if (gLegendaryRevolutionCommanderEnabled == false)
   {
      return;
   }

   xsEnableRule("legendaryRevolutionCommanderDoctrine");
}