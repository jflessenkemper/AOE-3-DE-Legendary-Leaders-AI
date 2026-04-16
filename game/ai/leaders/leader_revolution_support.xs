//==============================================================================
/* leader_revolution_support.xs

   Shared AI support layer for Fully Playable Revolutions civilizations.
   This is not a named leader personality; it keeps the merged revolution civs
   from behaving like generic fallback Europeans.
*/
//==============================================================================

bool gLegendaryRevolutionSupportEnabled = false;

void initLegendaryRevolutionSupport(void)
{
   if (civIsRevolution() == false)
   {
      return;
   }

   gLegendaryRevolutionSupportEnabled = true;
   cvMaxAge = cAge5;
   cvMaxArmyPop = 120;
   cvMaxCivPop = 80;
   cvOkToBuildForts = true;
   btBiasInf = 0.4;
   btBiasCav = 0.0;
   btBiasArt = 0.0;

   string rvltName = kbGetCivName(cMyCiv);

   if ((rvltName == "RvltModAmericans") || (rvltName == "RvltModMexicans") ||
       (rvltName == "RvltModChileans") || (rvltName == "RvltModColumbians") ||
       (rvltName == "RvltModPeruvians") || (rvltName == "RvltModBrazil") ||
       (rvltName == "RvltModNapoleonicFrance"))
   {
      btBiasArt = 0.3;
   }

   if ((rvltName == "RvltModArgentines") || (rvltName == "RvltModHungarians") ||
       (rvltName == "RvltModTexians") || (rvltName == "RvltModRioGrande") ||
       (rvltName == "RvltModCalifornians"))
   {
      btBiasCav = 0.5;
      btBiasInf = 0.2;
   }

   if ((rvltName == "RvltModCanadians") || (rvltName == "RvltModFrenchCanadians") ||
       (rvltName == "RvltModHaitians") || (rvltName == "RvltModRomanians") ||
       (rvltName == "RvltModEgyptians"))
   {
      btRushBoom = -0.2;
      btOffenseDefense = -0.2;
      cvMaxTowers = 6;
   }

   if ((rvltName == "RvltModMayans") || (rvltName == "RvltModYucatan") ||
       (rvltName == "RvltModCentralAmericans") || (rvltName == "RvltModPeruvians"))
   {
      btBiasNative = 0.6;
      btBiasTrade = 0.2;
   }
}

rule legendaryRevolutionArmyProfile
inactive
minInterval 60
{
   if (gLegendaryRevolutionSupportEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      cvMaxArmyPop = 130;
   }

   if (kbGetAge() >= cAge4)
   {
      cvMaxArmyPop = 145;
      btBiasInf = btBiasInf + 0.1;
      btBiasArt = btBiasArt + 0.1;
   }

   if (btBiasInf > 1.0)
   {
      btBiasInf = 1.0;
   }
   if (btBiasArt > 1.0)
   {
      btBiasArt = 1.0;
   }
}

void enableLegendaryRevolutionSupportRules(void)
{
   if (gLegendaryRevolutionSupportEnabled == false)
   {
      return;
   }

   xsEnableRule("legendaryRevolutionArmyProfile");
}
