//==============================================================================
/* leader_gustavus.xs */
//==============================================================================

bool gGustavusRulesEnabled = false;

void initLeaderGustavus(void)
{
   aiEcho("Legendary Leaders: activating Gustavus Adolphus personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.5;
   btOffenseDefense = 0.6;
   btBiasTrade = 0.1;
   btBiasNative = -0.2;
   llSetMilitaryFocus(0.5, 0.1, 0.5);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.24, 58.0);
   llEnablePrisonerSystem();
   gGustavusRulesEnabled = true;
}

rule gustavusMobileArtillery
inactive
minInterval 75
{
   if (gGustavusRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.6;
      btBiasArt = 0.6;
   }
}

void enableLeaderGustavusRules(void)
{
   if (gGustavusRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("gustavusMobileArtillery");
}