//==============================================================================
/* leader_valette.xs */
//==============================================================================

bool gValetteRulesEnabled = false;

void initLeaderValette(void)
{
   aiEcho("Legendary Leaders: activating Jean Parisot de Valette personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.5;
   btOffenseDefense = -0.4;
   btBiasTrade = 0.1;
   btBiasNative = 0.0;
   llSetMilitaryFocus(0.6, -0.2, 0.3);
   cvMaxTowers = 8;
   cvOkToBuildForts = true;
   gValetteRulesEnabled = true;
}

rule valetteFortressDiscipline
inactive
minInterval 70
{
   if (gValetteRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   btBiasInf = 0.7;
   if (kbGetAge() >= cAge3)
   {
      btBiasArt = 0.4;
   }
}

void enableLeaderValetteRules(void)
{
   if (gValetteRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("valetteFortressDiscipline");
}
