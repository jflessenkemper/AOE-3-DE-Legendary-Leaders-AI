//==============================================================================
/* leader_tokugawa.xs */
//==============================================================================

bool gTokugawaRulesEnabled = false;

void initLeaderTokugawa(void)
{
   llVerboseEcho("Legendary Leaders: activating Tokugawa Ieyasu personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.2;
   btOffenseDefense = -0.1;
   btBiasTrade = 0.3;
   btBiasNative = -0.1;
   llSetMilitaryFocus(0.5, -0.2, 0.3);
   llSetLeaderTacticalDoctrine(0.78, 0.22, 2, 3.0);
   cvMaxTowers = 5;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.18, 54.0);
   llEnablePrisonerSystem();
   gTokugawaRulesEnabled = true;
   llLogLeaderState("Tokugawa initialized");
}

rule tokugawaBakufuOrder
inactive
minInterval 80
{
   llLogRuleTick("tokugawaBakufuOrder");
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