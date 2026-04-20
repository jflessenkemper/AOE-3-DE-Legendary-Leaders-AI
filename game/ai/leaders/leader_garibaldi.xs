//==============================================================================
/* leader_garibaldi.xs */
//==============================================================================

bool gGaribaldiRulesEnabled = false;

void initLeaderGaribaldi(void)
{
   llVerboseEcho("Legendary Leaders: activating Giuseppe Garibaldi personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.5;
   btOffenseDefense = 0.4;
   btBiasTrade = 0.0;
   btBiasNative = 0.1;
   llSetMilitaryFocus(0.4, 0.4, 0.0);
   cvMaxTowers = 2;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineIntegration, 0.30, 64.0);
   llEnablePrisonerSystem();
   gGaribaldiRulesEnabled = true;
   llLogLeaderState("Garibaldi initialized");
}

rule garibaldiVolunteerColumns
inactive
minInterval 80
{
   llLogRuleTick("garibaldiVolunteerColumns");
   if (gGaribaldiRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.5;
      btBiasCav = 0.5;
   }
}

void enableLeaderGaribaldiRules(void)
{
   if (gGaribaldiRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("garibaldiVolunteerColumns");
}
