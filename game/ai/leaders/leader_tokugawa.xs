//==============================================================================
/* leader_tokugawa.xs */
//==============================================================================

bool gTokugawaRulesEnabled = false;

void initLeaderTokugawa(void)
{
   aiEcho("Legendary Leaders: activating Tokugawa Ieyasu personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.2;
   btOffenseDefense = -0.1;
   btBiasTrade = 0.3;
   btBiasNative = -0.1;
   llSetMilitaryFocus(0.5, -0.2, 0.3);
   cvMaxTowers = 5;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.18, 54.0);
   llEnablePrisonerSystem();
   gTokugawaRulesEnabled = true;
}

rule tokugawaBakufuOrder
inactive
minInterval 80
{
   if (gTokugawaRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.7;
      btBiasTrade = 0.4;
   }
}

void enableLeaderTokugawaRules(void)
{
   if (gTokugawaRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("tokugawaBakufuOrder");
}